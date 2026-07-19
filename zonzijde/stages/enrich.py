from __future__ import annotations

import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import requests
import trafilatura

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Candidate, CandidateItem, Reference,
                         load_artifact, save_artifact)
from ..net import VERIFY

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

MD_LINK_RE = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")

Fetch = Callable[[str, float], tuple[int, str]]
Render = Callable[[list[ArticleText], float, int], int]


def _dedupe(seq: list[str]) -> list[str]:
    seen: set[str] = set()
    return [x for x in seq if not (x in seen or seen.add(x))]


def fetch_html(url: str, timeout: float) -> tuple[int, str]:
    res = requests.get(url, headers={"User-Agent": UA},
                       timeout=timeout, verify=VERIFY)
    return res.status_code, res.text


def extract(html: str, url: str) -> tuple[str, list[str]]:
    data = trafilatura.extract(html, url=url, output_format="json",
                               include_links=True, with_metadata=True,
                               favor_recall=True)
    if not data:
        return "", []
    text = (json.loads(data).get("text") or "").strip()
    return text, _dedupe(MD_LINK_RE.findall(text))


FOLLOW = {"EXT", "INT"}

CLASSIFY_SCHEMA = {
    "type": "object",
    "properties": {
        "links": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "i": {"type": "integer"},
                    "category": {"type": "string",
                                 "enum": ["EXT", "INT", "NAV", "PROMO"]},
                },
                "required": ["i", "category"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["links"],
    "additionalProperties": False,
}

Classify = Callable[[ArticleText], dict[int, str]]


def make_classify(body: str, model: str) -> Classify:
    def classify(art: ArticleText) -> dict[int, str]:
        lines = [body, "", f"Title: {art.titel}", f"Article URL: {art.link}",
                 "Links:"]
        for k, link in enumerate(art.links):
            lines.append(f"  [{k}] {link}")
        prompt = "\n".join(lines) + (
            "\n\nReturn a classification for every link index shown above.")
        payload = llm.agent_json(prompt, model=model, schema=CLASSIFY_SCHEMA,
                                 allowed_tools=[], max_turns=2)
        cats: dict[int, str] = {}
        rows = payload.get("links") if isinstance(payload, dict) else None
        for row in rows or []:
            if isinstance(row, dict) and isinstance(row.get("i"), int):
                cats[row["i"]] = row.get("category")
        return cats
    return classify


def select_references(art: ArticleText, cats: dict[int, str],
                      deny: list[str], cap: int) -> list[str]:
    picks: list[str] = []
    for k, link in enumerate(art.links):
        if cats.get(k) not in FOLLOW:
            continue
        if any(d in link for d in deny):
            continue
        picks.append(link)
        if len(picks) >= cap:
            break
    return picks


def fetch_reference(url: str, fetch: Fetch, timeout: float,
                    min_words: int, max_words: int) -> Reference:
    ref = Reference(url=url, ok=False, text="", words=0)
    try:
        status, html = fetch(url, timeout)
        if status != 200:
            return ref
        text, _links = extract(html, url)
    except Exception:
        return ref
    words = text.split()
    if len(words) < min_words:
        return ref
    if len(words) > max_words:
        text = " ".join(words[:max_words])
    ref.text, ref.words, ref.ok = text, min(len(words), max_words), True
    return ref


def _stage1(item: CandidateItem, fetch: Fetch, timeout: float,
            min_words: int) -> ArticleText:
    art = ArticleText(**item.model_dump(), ok=False, method="requests",
                      text="", words=0, links=[], note="")
    try:
        status, html = fetch(item.link, timeout)
    except requests.RequestException as e:
        art.note = f"{type(e).__name__}: {e}"
        return art
    if status != 200:
        art.note = f"HTTP {status} (error page, not the article)"
        return art
    try:
        art.text, art.links = extract(html, item.link)
    except Exception as e:
        art.note = f"extraction failed: {type(e).__name__}: {e}"
        return art
    art.words = len(art.text.split())
    art.ok = art.words >= min_words
    if not art.ok:
        art.note = "too thin for plain fetch (likely consent wall / JS / bot block)"
    return art


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
    if proxy:
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
                if resp and resp.status != 200:
                    art.note = f"browser got HTTP {resp.status}"
                    continue
                page.wait_for_timeout(2500)
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


def run(ctx: RunContext, fetch: Fetch | None = None,
        render: Render | None = None, classify: Classify | None = None) -> None:
    cfg = ctx.enrich_cfg
    timeout = float(cfg.get("timeout_s", 25))
    min_words = int(cfg.get("min_words", 120))
    concurrency = int(cfg.get("concurrency", 8))
    fetch = fetch or fetch_html
    render = render or render_blocked

    ref_cfg = cfg.get("references", {})
    ref_cap = int(ref_cfg.get("max", 3))
    ref_min = int(ref_cfg.get("min_words", 60))
    ref_max = int(ref_cfg.get("max_words", 1200))
    ref_deny = list(ref_cfg.get("deny", []))
    if classify is None:
        classify = make_classify(prompts.load_prompt(ctx.root, "classify").body,
                                  ctx.llm_cfg("light")["model"])

    candidates = load_artifact(ctx.work_dir / "40-candidates.json", Candidate)
    if not candidates:
        raise SystemExit("S5 enrich: 40-candidates.json is empty (PIPE-5)")

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

    def enrich_refs(art: ArticleText) -> None:
        try:
            cats = classify(art)
        except llm.LlmError:
            return
        picks = select_references(art, cats, ref_deny, ref_cap)
        art.references = [fetch_reference(u, fetch, timeout, ref_min, ref_max)
                          for u in picks]

    linked = [a for a in articles.values() if a.ok and a.links]
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        list(ex.map(enrich_refs, linked))

    topics_log: list[dict] = []
    for cand in candidates:
        ok_rows = sum(1 for r in cand.items if articles[r.id].ok)
        entry = {"scope": cand.scope, "topic": cand.topic,
                 "rows": len(cand.items), "ok_rows": ok_rows,
                 "dropped": ok_rows == 0}
        if entry["dropped"]:
            for row in cand.items:
                art = articles[row.id]
                if "topic dropped" not in art.note:
                    art.note = (art.note + "; topic dropped (PIPE-5)").lstrip("; ")
        topics_log.append(entry)

    save_artifact(ctx.work_dir / "50-articles.json", list(articles.values()))
    methods = {m: sum(1 for a in articles.values() if a.ok and a.method == m)
               for m in ("requests", "playwright")}
    dropped = [t["topic"] for t in topics_log if t["dropped"]]
    ref_selected = sum(len(a.references) for a in articles.values())
    ref_ok = sum(1 for a in articles.values() for r in a.references if r.ok)
    log = {
        "rows": len(articles),
        "full_text": sum(1 for a in articles.values() if a.ok),
        "methods": methods,
        "min_words": min_words,
        "references": {"selected": ref_selected, "ok": ref_ok},
        "topics": topics_log,
        "dropped_topics": dropped,
        "duration_s": round(time.perf_counter() - t0, 1),
    }
    (ctx.work_dir / "50-enrich-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"S5 enrich: {log['rows']} source rows → {log['full_text']} full texts"
          f" (requests {methods['requests']}, playwright {methods['playwright']});"
          f" {ref_ok}/{ref_selected} references; "
          f"{len(dropped)} topic(s) dropped in {log['duration_s']}s")
