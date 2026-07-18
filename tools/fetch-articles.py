#!/usr/bin/env python3
import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests
import trafilatura

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

CA_BUNDLE = (os.environ.get("REQUESTS_CA_BUNDLE")
             or os.environ.get("CURL_CA_BUNDLE")
             or "/root/.ccr/ca-bundle.crt")
VERIFY = CA_BUNDLE if os.path.exists(CA_BUNDLE) else True

URL_RE = re.compile(r"https?://[^\s)\]|>]+")
MD_LINK_RE = re.compile(r"\[[^\]]*\]\((https?://[^)]+)\)")


def read_input(args):
    blobs = []
    for a in args:
        if os.path.isfile(a):
            with open(a, encoding="utf-8") as fh:
                blobs.append(fh.read())
        elif URL_RE.fullmatch(a) or a.startswith("http"):
            blobs.append(a)
        else:
            print(f"waarschuwing: '{a}' is geen bestaand bestand of geldige URL — overgeslagen.",
                  file=sys.stderr)
    if not blobs and not sys.stdin.isatty():
        blobs.append(sys.stdin.read())
    text = "\n".join(blobs)
    if not text.strip():
        return []

    if "|" in text and re.search(r"\|\s*link\s*\|", text, re.I):
        return parse_md_table(text)
    return [blank_record(u) for u in dedupe(URL_RE.findall(text))]


def blank_record(url):
    return {"link": url, "bron": "", "scope": "", "titel": "", "samenvatting": ""}


def dedupe(seq):
    seen, out = set(), []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def parse_md_table(text):
    rows = [ln for ln in text.splitlines() if ln.strip().startswith("|")]
    if len(rows) < 2:
        return [blank_record(u) for u in dedupe(URL_RE.findall(text))]

    def cells(line):
        return [c.strip() for c in line.strip().strip("|").split("|")]

    header = [h.lower() for h in cells(rows[0])]
    idx = {name: header.index(name) for name in
           ("bron", "scope", "titel", "samenvatting", "link") if name in header}
    records, seen = [], set()
    for line in rows[2:]:
        col = cells(line)
        raw = col[idx["link"]] if "link" in idx and idx["link"] < len(col) else line
        m_link = MD_LINK_RE.search(raw)
        if m_link:
            link = m_link.group(1)
        else:
            m_url = URL_RE.search(raw)
            if not m_url:
                continue
            link = m_url.group(0)
        if link in seen:
            continue
        seen.add(link)

        def get(name):
            return col[idx[name]] if name in idx and idx[name] < len(col) else ""
        records.append({"link": link, "bron": get("bron"), "scope": get("scope"),
                        "titel": get("titel"), "samenvatting": get("samenvatting")})
    return records


def extract(html, url):
    data = trafilatura.extract(html, url=url, output_format="json",
                               include_links=True, with_metadata=True,
                               favor_recall=True)
    if not data:
        return None, None, None, "", []
    d = json.loads(data)
    text = (d.get("text") or "").strip()
    links = dedupe(re.findall(r"\[[^\]]+\]\((https?://[^)]+)\)", text))
    return d.get("title"), d.get("author"), d.get("date"), text, links


def fetch_requests(rec, timeout):
    r = requests.get(rec["link"], headers={"User-Agent": UA},
                     timeout=timeout, verify=VERIFY)
    if r.status_code != 200:
        return (None, None, None, "", []), r.status_code
    return extract(r.text, rec["link"]), r.status_code


def process(rec, timeout, min_words):
    out = dict(rec, method="requests", status=None, ok=False,
               title=rec["titel"] or None, author=None, date=None,
               text="", links=[], words=0, note="")
    t0 = time.perf_counter()
    try:
        (title, author, date, text, links), status = fetch_requests(rec, timeout)
        out.update(status=status, title=title or out["title"], author=author,
                   date=date, text=text, links=links, words=len(text.split()))
        out["ok"] = out["words"] >= min_words
        if not out["ok"]:
            out["note"] = (f"HTTP {status} (error page, not the article)" if status != 200
                           else "too thin for plain fetch (likely consent wall / JS / bot block)")
    except Exception as e:
        out["note"] = f"{type(e).__name__}: {e}"
    out["sec"] = round(time.perf_counter() - t0, 2)
    return out


def find_chromium():
    base = os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")
    for root in (base, os.path.expanduser("~/.cache/ms-playwright")):
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for exe in ("chrome", "headless_shell"):
                if exe in files and "chrome-linux" in dirpath:
                    return os.path.join(dirpath, exe)
    return None


CONSENT_SELECTORS = [
    "button:has-text('Accepteren')", "button:has-text('Accepteer')",
    "button:has-text('Akkoord')", "button:has-text('Alles accepteren')",
    "button:has-text('Accept')", "#pg-accept-btn",
]


def render_blocked(recs, timeout, min_words):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        for r in recs:
            r["note"] = (r["note"] + "; playwright not installed").lstrip("; ")
        return 0

    launch = {"headless": True, "args": ["--no-sandbox"]}
    exe = find_chromium()
    if exe:
        launch["executable_path"] = exe
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        launch["proxy"] = {"server": proxy}

    recovered = 0
    with sync_playwright() as p:
        browser = p.chromium.launch(**launch)
        for r in recs:
            t0 = time.perf_counter()
            ctx = browser.new_context(user_agent=UA, locale="nl-NL")
            page = ctx.new_page()
            try:
                resp = page.goto(r["link"], wait_until="domcontentloaded", timeout=timeout * 1000)
                if resp and resp.status != 200:
                    r["method"] = "playwright"
                    r["note"] = f"browser got HTTP {resp.status}; using RSS summary"
                    continue
                page.wait_for_timeout(2500)
                for sel in CONSENT_SELECTORS:
                    try:
                        page.click(sel, timeout=1200)
                        page.wait_for_timeout(1500)
                        break
                    except Exception:
                        pass
                title, author, date, text, links = extract(page.content(), r["link"])
                words = len(text.split())
                if words >= min_words:
                    r.update(method="playwright", ok=True, title=title or r["title"],
                             author=author, date=date, text=text, links=links,
                             words=words, note="")
                    recovered += 1
                else:
                    r["method"] = "playwright"
                    r["note"] = "still blocked after browser render; using RSS summary"
            except Exception as e:
                r["method"] = "playwright"
                r["note"] = f"browser render failed: {type(e).__name__}"
            finally:
                r["sec"] = round(r.get("sec", 0) + time.perf_counter() - t0, 2)
                ctx.close()
        browser.close()
    return recovered


def write_outputs(recs, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    json_path = os.path.join(out_dir, "articles.json")
    md_path = os.path.join(out_dir, "articles.md")
    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(recs, fh, ensure_ascii=False, indent=2)

    lines = ["# De Zonzijde — brontekst per artikel", ""]
    for i, r in enumerate(recs, 1):
        head = " · ".join(x for x in (r.get("bron"), r.get("scope")) if x)
        lines.append(f"## {i}. {r.get('title') or r.get('titel') or r['link']}"
                     + (f"  ({head})" if head else ""))
        meta = [f"link: {r['link']}"]
        if r.get("date"):
            meta.append(f"datum: {r['date']}")
        if r.get("author"):
            meta.append(f"auteur: {r['author']}")
        meta.append(f"bron-fetch: {r.get('method')} · {r.get('words', 0)} woorden"
                    + (f" · {r['note']}" if r.get("note") else ""))
        lines.append("  \n".join(meta))
        lines.append("")
        if r.get("ok") and r.get("text"):
            lines.append(r["text"])
        else:
            summary = r.get("samenvatting") or "—"
            quoted = "\n".join(f"> {ln}" for ln in summary.splitlines() or ["—"])
            lines.append(f"> _(brontekst geblokkeerd — RSS-samenvatting)_\n>\n{quoted}")
        if r.get("links"):
            lines.append("\n**Links in artikel:**")
            lines += [f"- {u}" for u in r["links"][:15]]
        lines.append("\n---\n")
    with open(md_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return json_path, md_path


def main():
    ap = argparse.ArgumentParser(description="Fetch full article text behind the selected links.")
    ap.add_argument("inputs", nargs="*", help="URLs, a URL-list file, or a markdown table file")
    ap.add_argument("--out-dir", default=ROOT)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--min-words", type=int, default=120)
    ap.add_argument("--timeout", type=int, default=25)
    ap.add_argument("--no-browser", action="store_true", help="skip the Playwright fallback")
    a = ap.parse_args()

    recs = read_input(a.inputs)
    if not recs:
        ap.error("no URLs found. Pipe the app's MD table in, or pass URLs / a file.")

    start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        recs = list(ex.map(lambda r: process(r, a.timeout, a.min_words), recs))

    blocked = [r for r in recs if not r["ok"]]
    if blocked and not a.no_browser:
        print(f"stage 1: {len(recs) - len(blocked)}/{len(recs)} ok — "
              f"rendering {len(blocked)} blocked link(s) in a browser…", file=sys.stderr)
        render_blocked(blocked, a.timeout, a.min_words)

    total = time.perf_counter() - start
    json_path, md_path = write_outputs(recs, a.out_dir)

    ok = sum(1 for r in recs if r["ok"])
    print(f"\n{'Bron':<12} {'Words':>6} {'Via':>11}  Titel / status")
    print("-" * 78)
    for r in recs:
        label = (r.get("title") or r.get("titel") or r["link"])[:44]
        flag = "" if r["ok"] else f"⚠ {r['note']}"
        print(f"{(r.get('bron') or '—'):<12} {r.get('words', 0):>6} "
              f"{r.get('method'):>11}  {label} {flag}")
    print("-" * 78)
    print(f"{ok}/{len(recs)} full articles in {total:.1f}s  →  {md_path}  ·  {json_path}")


if __name__ == "__main__":
    main()
