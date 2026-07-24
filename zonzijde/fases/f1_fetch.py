from __future__ import annotations

import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from email.utils import parsedate_to_datetime
from urllib.parse import quote
from xml.etree import ElementTree

import requests

from ..context import TZ, RunContext, Source
from ..contracts import FeedItem, item_id, save_artifact
from ..net import VERIFY

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def build_rijksoverheid_url(window_start: datetime, until: datetime) -> str:
    q = {
        "filters": [
            {"field": "content_type", "values": ["pro:newsDocument"], "type": "all"},
            {"field": "sort_date", "type": "all",
             "values": [{"to": until.isoformat(), "from": window_start.isoformat(),
                         "name": "editionWindow"}]},
        ],
        "resultSearchTerm": "", "pageTitle": "Nieuws",
    }
    return "https://www.rijksoverheid.nl/api/rss?query=" + quote(json.dumps(q))

URL_BUILDERS = {"rijksoverheid": build_rijksoverheid_url}


def strip_html(text: str) -> str:
    return _WS_RE.sub(" ", html.unescape(_TAG_RE.sub(" ", text or ""))).strip()


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_date(raw: str) -> datetime | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    for parse in (parsedate_to_datetime, datetime.fromisoformat):
        try:
            dt = parse(raw)
            return dt if dt.tzinfo else dt.replace(tzinfo=TZ)
        except ValueError:
            continue
    return None


def parse_feed(xml_text: str) -> list[dict]:
    root = ElementTree.fromstring(xml_text)
    entries = []
    for el in root.iter():
        if _local(el.tag) not in ("item", "entry"):
            continue
        fields: dict[str, str] = {}
        link_href = ""
        for child in el:
            name = _local(child.tag)
            text = (child.text or "").strip()
            if name == "link" and not text:
                if child.get("rel") in (None, "alternate") and child.get("href"):
                    link_href = child.get("href")
            elif name not in fields:
                fields[name] = text
        entries.append({
            "title": strip_html(fields.get("title", "")),
            "link": fields.get("link") or link_href,
            "summary": strip_html(fields.get("description") or fields.get("summary", "")),
            "published": parse_date(fields.get("pubDate") or fields.get("date")
                                    or fields.get("published") or fields.get("updated", "")),
        })
    return entries


def fetch_source(source: Source, ctx: RunContext, timeout: float) -> tuple[list[dict], str]:
    url = source.url
    if source.builder:
        url = URL_BUILDERS[source.builder](ctx.window_start, ctx.now())
    try:
        res = requests.get(url, headers={"User-Agent": UA}, timeout=timeout, verify=VERIFY)
        res.raise_for_status()
        return parse_feed(res.text), ""
    except (requests.RequestException, ElementTree.ParseError) as e:
        return [], f"{type(e).__name__}: {e}"


def in_window(published: datetime | None, ctx: RunContext) -> bool:
    return published is None or published >= ctx.window_start


def run(ctx: RunContext) -> None:
    timeout = float(ctx.fetch_cfg.get("timeout_s", 15))
    concurrency = int(ctx.fase_cfg("fetch")["concurrency"])
    fetched_at = ctx.now()

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda s: fetch_source(s, ctx, timeout), ctx.sources))

    items: list[FeedItem] = []
    log = {"fetched_at": fetched_at.isoformat(), "window_start": ctx.window_start.isoformat(),
           "window_days": ctx.window_days, "feeds": []}
    for source, (entries, error) in zip(ctx.sources, results):
        kept = no_link = out_of_window = undated = 0
        for e in entries:
            if not e["link"]:
                no_link += 1
                continue
            if not in_window(e["published"], ctx):
                out_of_window += 1
                continue
            if e["published"] is None:
                undated += 1
            items.append(FeedItem(
                id=item_id(e["link"]), source=source.id, bron=source.bron,
                scopes=source.scopes, title=e["title"], link=e["link"],
                summary=e["summary"], published=e["published"], fetched=fetched_at,
            ))
            kept += 1
        log["feeds"].append({
            "source": source.id, "bron": source.bron, "error": error,
            "entries": len(entries), "kept": kept, "out_of_window": out_of_window,
            "no_link": no_link, "undated": undated,
        })

    save_artifact(ctx.work_dir / "f1-items.json", items)
    (ctx.work_dir / "f1-fetch-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    failed = [f["source"] for f in log["feeds"] if f["error"]]
    print(f"F1 fetch: {len(items)} items from {len(ctx.sources) - len(failed)} feeds"
          + (f"; failed: {', '.join(failed)}" if failed else ""))
