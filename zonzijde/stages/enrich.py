"""S5 enrich (PIPE-5): fetch the full article text behind every selected link.

Reads ``40-candidates.json``, writes ``50-articles.json`` and
``50-enrich-log.json``. Ported from ``tools/fetch-articles.py`` (the fetch,
extraction and browser-render logic is tuned — see CLAUDE.md), minus its
RSS-summary fallback: **a blurb is never writing material** (PIPE-5/WR-2).

Two-stage fetch, because a few of the sources block plain HTTP clients:
  1. requests + trafilatura — fast, gets most sources cleanly.
  2. Playwright (headless Chromium) — only for links stage 1 left blocked or
     too thin (consent gates, JS-rendered bodies).

Re-source-or-drop, per topic: a topic whose other source rows delivered full
text needs nothing more (the sibling rows *are* the re-source). A topic with
no full text at all gets one search for alternative coverage; if that also
fails, the topic is dropped and logged — S6 sees the drop log so scope counts
can rebalance (ARCHITECTURE §3).
"""

from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable
from urllib.parse import urlsplit

import requests
import trafilatura

from .. import llm
from ..context import RunContext
from ..contracts import ArticleText, Candidate, CandidateItem, load_artifact, save_artifact
from ..net import VERIFY

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")

# fetch(url, timeout) -> (status, html); injectable for tests.
Fetch = Callable[[str, float], tuple[int, str]]
# render(blocked_articles, timeout, min_words) -> recovered count; mutates.
Render = Callable[[list[ArticleText], float, int], int]
# search(query, timeout, max_results) -> candidate URLs.
Search = Callable[[str, float, int], list[str]]


def _dedupe(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def _host(url: str) -> str:
    """Hostname normalised for comparison: hostnames are case-insensitive and
    a site may serve the same pages with and without ``www.``."""
    return urlsplit(url).netloc.lower().removeprefix("www.")


# ----- fetch + extraction ---------------------------------------------------

def fetch_html(url: str, timeout: float) -> tuple[int, str]:
    res = requests.get(url, headers={"User-Agent": UA},
                       timeout=timeout, verify=VERIFY)
    return res.status_code, res.text


def extract(html: str, url: str) -> tuple[str, list[str]]:
    """Clean body text + in-article links from raw HTML."""
    data = trafilatura.extract(html, url=url, output_format="json",
                               include_links=True, with_metadata=True,
                               favor_recall=True)
    if not data:
        return "", []
    text = (json.loads(data).get("text") or "").strip()
    return text, _dedupe(MD_LINK_RE.findall(text))


def _stage1(item: CandidateItem, fetch: Fetch, timeout: float,
            min_words: int) -> ArticleText:
    art = ArticleText(**item.model_dump(), ok=False, method="requests",
                      text="", words=0, links=[], note="")
    try:
        status, html = fetch(item.link, timeout)
    except requests.RequestException as e:
        art.note = f"{type(e).__name__}: {e}"
        return art
    if status != 200:  # 403/404/500 bodies are error pages, not the article
        art.note = f"HTTP {status} (error page, not the article)"
        return art
    try:
        art.text, art.links = extract(html, item.link)
    except Exception as e:  # broken markup must not kill the whole stage
        art.note = f"extraction failed: {type(e).__name__}: {e}"
        return art
    art.words = len(art.text.split())
    art.ok = art.words >= min_words
    if not art.ok:
        art.note = "too thin for plain fetch (likely consent wall / JS / bot block)"
    return art


# ----- Playwright fallback for the blocked handful --------------------------

CONSENT_SELECTORS = [
    "button:has-text('Accepteren')", "button:has-text('Accepteer')",
    "button:has-text('Akkoord')", "button:has-text('Alles accepteren')",
    "button:has-text('Accept')", "#pg-accept-btn",
]


def _find_chromium() -> str | None:
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    for root in (base, os.path.expanduser("~/.cache/ms-playwright")):
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for exe in ("chrome", "headless_shell"):
                if exe in files and "chrome-linux" in dirpath:
                    return os.path.join(dirpath, exe)
    return None


def render_blocked(blocked: list[ArticleText], timeout: float,
                   min_words: int) -> int:
    """Render the still-blocked articles in a headless browser, re-extract.

    Mutates the records in place, returns the count recovered. Without
    Playwright installed the records stay blocked (noted) — PIPE-5's
    re-source-or-drop takes over from there, never a summary fallback.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        for a in blocked:
            a.note = (a.note + "; playwright not installed").lstrip("; ")
        return 0

    launch = {"headless": True, "args": ["--no-sandbox"]}
    exe = _find_chromium()
    if exe:
        launch["executable_path"] = exe
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:  # route through the agent proxy if present
        launch["proxy"] = {"server": proxy}

    recovered = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for art in blocked:
            art.method = "playwright"
            ctx = None
            try:
                ctx = browser.new_context(user_agent=UA, locale="nl-NL")
                page = ctx.new_page()
                resp = page.goto(art.link, wait_until="domcontentloaded",
                                 timeout=timeout * 1000)
                if resp and resp.status != 200:  # don't extract an error page
                    art.note = f"browser got HTTP {resp.status}"
                    continue
                page.wait_for_timeout(2500)  # let JS + consent settle
                for sel in CONSENT_SELECTORS:
                    try:
                        page.click(sel, timeout=1200)
                        page.wait_for_timeout(1500)
                        break
                    except Exception:
                        pass
                text, links = extract(page.content(), art.link)
                words = len(text.split())
                if words >= min_words:
                    art.ok, art.text, art.words, art.links = True, text, words, links
                    art.note = ""
                    recovered += 1
                else:
                    art.note = "still blocked after browser render"
            except Exception as e:
                detail = str(e).splitlines()[0][:100] if str(e) else ""
                art.note = f"browser render failed: {type(e).__name__}: {detail}"
            finally:
                if ctx is not None:
                    try:
                        ctx.close()
                    except Exception:
                        pass
        browser.close()
    return recovered


# ----- alternative coverage (the "search" half of re-source-or-drop) --------
#
# Scraping a search engine is a dead end here: production runs from
# datacenter IPs (GitHub Actions) which the engines bot-wall. The frontier
# tier already provides tool-assisted browsing (§6 — the same adapter gives
# S6 its SRC-3 browsing), so a fully-blocked topic gets one short WebSearch
# session. Operational instruction, not editorial wording, hence in code
# (like S4's SHAPE_NOTE) rather than config/prompts/.

SEARCH_SYSTEM = (
    "Je zoekt alternatieve berichtgeving voor een Nederlands nieuwsverhaal "
    "waarvan de oorspronkelijke bron niet op te halen is. Zoek op het web en "
    "geef directe artikel-URL's van andere nieuwsmedia over precies hetzelfde "
    "verhaal. Alleen nieuwsartikelen — geen homepagina's, aggregators, "
    "zoekpagina's, Wikipedia of profielpagina's. Vind je geen berichtgeving "
    "over hetzelfde verhaal, geef dan een lege lijst.")

SEARCH_SCHEMA = {
    "type": "object",
    "properties": {"urls": {"type": "array", "items": {"type": "string"}}},
    "required": ["urls"],
    "additionalProperties": False,
}


def make_search(cfg: dict) -> Search:
    """Default alternative-coverage search: one frontier session with
    WebSearch. Failures (no key, transport) surface as ``LlmError`` — the
    caller logs them and the topic drops (PIPE-5), never a summary fallback."""
    def search(query: str, timeout: float, max_results: int) -> list[str]:
        payload = llm.frontier_json(
            f"Vind maximaal {max_results} alternatieve bronnen voor dit "
            f"verhaal: {query}. Doe hooguit 2 zoekopdrachten en geef "
            f"daarna direct je antwoord.",
            system=SEARCH_SYSTEM, schema=SEARCH_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"),
            allowed_tools=["WebSearch"], max_turns=16)
        urls = payload.get("urls") if isinstance(payload, dict) else None
        if not isinstance(urls, list):
            raise llm.LlmError(f"search returned no urls list: {payload!r:.200}")
        # News-only is the search prompt's job (SEARCH_SYSTEM); no code-side
        # host blocklist second-guesses it.
        return _dedupe([u for u in urls if isinstance(u, str)
                        and u.startswith("http")])[:max_results]
    return search


def _alt_source(cand: Candidate, articles: dict[str, ArticleText],
                fetch: Fetch, search: Search, timeout: float,
                min_words: int, max_results: int) -> dict:
    """Search for alternative coverage of a fully-blocked topic; on success
    the text lands on the topic's first row as ``method: alt-source``.
    Returns the log entry either way."""
    query = cand.items[0].titel  # the headline finds same-story coverage
    own_hosts = {_host(r.link) for r in cand.items}
    log: dict = {"query": query, "tried": [], "picked": None}
    try:
        results = search(query, timeout, max_results)
    except (requests.RequestException, llm.LlmError) as e:
        log["error"] = f"search failed: {type(e).__name__}: {e}"
        return log
    log["found"] = len(results)
    for url in results:
        if _host(url) in own_hosts:  # those hosts just blocked us
            continue
        log["tried"].append(url)
        try:  # best-effort per URL: one bad page must not kill the run
            status, html = fetch(url, timeout)
            if status != 200:
                continue
            text, links = extract(html, url)
        except Exception:
            continue
        words = len(text.split())
        if words >= min_words:
            art = articles[cand.items[0].id]
            art.ok, art.method = True, "alt-source"
            art.text, art.words, art.links = text, words, links
            art.note = f"alt coverage: {url}"
            log["picked"] = url
            return log
    return log


# ----- the stage ------------------------------------------------------------

def run(ctx: RunContext, fetch: Fetch | None = None,
        render: Render | None = None, search: Search | None = None) -> None:
    cfg = ctx.enrich_cfg
    timeout = float(cfg.get("timeout_s", 25))
    min_words = int(cfg.get("min_words", 120))
    concurrency = int(cfg.get("concurrency", 8))
    max_results = int(cfg.get("search_results", 5))
    fetch = fetch or fetch_html
    render = render or render_blocked
    search = search or make_search(ctx.llm_cfg("frontier"))

    candidates = load_artifact(ctx.work_dir / "40-candidates.json", Candidate)
    if not candidates:
        raise SystemExit("S5 enrich: 40-candidates.json is empty (PIPE-5)")

    # One fetch per unique item — the same article can back several topics.
    rows: dict[str, CandidateItem] = {}
    for cand in candidates:
        for row in cand.items:
            rows.setdefault(row.id, row)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        fetched = ex.map(lambda r: _stage1(r, fetch, timeout, min_words),
                         rows.values())
        articles = {a.id: a for a in fetched}

    blocked = [a for a in articles.values() if not a.ok]
    if blocked and cfg.get("browser", True):
        render(blocked, timeout, min_words)

    topics_log: list[dict] = []
    for cand in candidates:
        ok_rows = sum(1 for r in cand.items if articles[r.id].ok)
        entry = {"scope": cand.scope, "rank": cand.rank, "topic": cand.topic,
                 "rows": len(cand.items), "ok_rows": ok_rows,
                 "alt_search": None, "dropped": False}
        if ok_rows == 0:  # sibling rows delivered nothing either → search
            entry["alt_search"] = _alt_source(cand, articles, fetch, search,
                                              timeout, min_words, max_results)
            entry["ok_rows"] = sum(1 for r in cand.items if articles[r.id].ok)
        entry["dropped"] = entry["ok_rows"] == 0
        if entry["dropped"]:
            for row in cand.items:
                art = articles[row.id]
                if "topic dropped" not in art.note:
                    art.note = (art.note + "; topic dropped (PIPE-5)").lstrip("; ")
        topics_log.append(entry)

    save_artifact(ctx.work_dir / "50-articles.json", list(articles.values()))
    methods = {m: sum(1 for a in articles.values() if a.ok and a.method == m)
               for m in ("requests", "playwright", "alt-source")}
    dropped = [t["topic"] for t in topics_log if t["dropped"]]
    log = {
        "rows": len(articles),
        "full_text": sum(1 for a in articles.values() if a.ok),
        "methods": methods,
        "min_words": min_words,
        "topics": topics_log,
        "dropped_topics": dropped,
        "duration_s": round(time.perf_counter() - t0, 1),
    }
    (ctx.work_dir / "50-enrich-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"S5 enrich: {log['rows']} source rows → {log['full_text']} full texts"
          f" (requests {methods['requests']}, playwright {methods['playwright']},"
          f" alt-source {methods['alt-source']});"
          f" {len(dropped)} topic(s) dropped in {log['duration_s']}s")
