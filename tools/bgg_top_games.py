#!/usr/bin/env python3
"""Build a CSV of type, categories, mechanisms, rating and complexity for the
top-N ranked board games on BoardGameGeek.

Why this exists
---------------
BGG's XML API2 `thing` endpoint (with ``&stats=1``) returns every field we want
in a single response per game, and accepts up to ~20 ids at a time. The only
thing it does *not* expose is the ranked ordering, so we need a separate source
for "which games are the top 300, and in what order".

Two ways to supply that ordering (pick one):

  1. --ranks-csv PATH
       Point at BGG's official daily ranks dump
       (https://boardgamegeek.com/data_dumps/bg_ranks, login required to
       download). It already contains id, name, rank, average and bayesaverage,
       so we only call the API to enrich each game with type/categories/
       mechanisms/complexity. This is the most reliable source.

  2. --scrape-browse
       Scrape the public /browse/boardgame/page/N listing for the ranked ids.
       Simple, but the pages sit behind Cloudflare, so it only works from a
       normal browser-like context (your own machine / IP), not from locked-down
       CI.

Authentication
--------------
As of 2024-25 the XML API rejects anonymous automated requests with
``401 Unauthorized``. Log in to boardgamegeek.com in a browser, copy your
session cookie, and pass it via the BGG_COOKIE environment variable, e.g.

    export BGG_COOKIE="bggusername=you; bggpassword=...; SessionID=..."

Usage
-----
    # From the official ranks dump (recommended):
    python3 tools/bgg_top_games.py --ranks-csv boardgames_ranks.csv \
        --top 300 -o top300.csv

    # Scraping the browse pages instead:
    python3 tools/bgg_top_games.py --scrape-browse --top 300 -o top300.csv

Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

API = "https://boardgamegeek.com/xmlapi2/thing"
BROWSE = "https://boardgamegeek.com/browse/boardgame/page/{page}"
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)
BATCH = 20          # ids per API call
PAUSE = 2.0         # seconds between calls (be polite to BGG)


def _get(url: str, tries: int = 5) -> bytes:
    """Fetch a URL, honouring BGG's 202 "request queued, retry" responses."""
    headers = {"User-Agent": UA}
    cookie = os.environ.get("BGG_COOKIE")
    if cookie:
        headers["Cookie"] = cookie
    backoff = PAUSE
    for attempt in range(1, tries + 1):
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                if resp.status == 202:  # accepted but not ready yet
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code == 401:
                sys.exit(
                    "401 Unauthorized from BGG. Set BGG_COOKIE to a logged-in "
                    "session cookie (see this file's docstring)."
                )
            if exc.code in (429, 503) and attempt < tries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            # Transient network failure (DNS, timeout, connection reset) — retry.
            if attempt < tries:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    raise RuntimeError(f"gave up fetching {url} after {tries} tries")


def ranked_ids_from_csv(path: str, top: int) -> list[tuple[int, dict]]:
    """Read (id, row) pairs from BGG's ranks dump, ordered by rank."""
    rows = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rank = row.get("rank") or row.get("Rank")
            if not rank or not rank.strip().isdigit():
                continue
            gid = row.get("id") or row.get("Id") or row.get("ID")
            if not gid or not gid.strip().isdigit():
                continue
            rows.append((int(rank), int(gid), row))
    rows.sort(key=lambda r: r[0])
    return [(gid, row) for _rank, gid, row in rows[:top]]


def ranked_ids_from_browse(top: int) -> list[tuple[int, dict]]:
    """Scrape ranked ids off the public /browse listing (100 per page)."""
    out: list[tuple[int, dict]] = []
    page = 1
    while len(out) < top:
        html = _get(BROWSE.format(page=page)).decode("utf-8", "replace")
        # Only pull ids from the ranked table rows (id="row_..."); matching every
        # /boardgame/<id>/ link would also grab sidebar/header/footer games and
        # corrupt the ranking order. Rows appear in document (rank) order.
        seen, fresh = set(), []
        for row in re.findall(r'<tr[^>]*id="row_".*?</tr>', html, re.DOTALL):
            match = re.search(r"/boardgame/(\d+)/", row)
            if match and match.group(1) not in seen:
                seen.add(match.group(1))
                fresh.append(int(match.group(1)))
        if not fresh:
            break
        for gid in fresh:
            out.append((gid, {}))
        page += 1
        time.sleep(PAUSE)
    return out[:top]


def _links(item: ET.Element, link_type: str) -> str:
    vals = [
        ln.get("value", "")
        for ln in item.findall("link")
        if ln.get("type") == link_type
    ]
    return "; ".join(v for v in vals if v)


def _stat(item: ET.Element, tag: str) -> str:
    el = item.find(f"statistics/ratings/{tag}")
    return el.get("value", "") if el is not None else ""


def _name(item: ET.Element) -> str:
    for nm in item.findall("name"):
        if nm.get("type") == "primary":
            return nm.get("value", "")
    nm = item.find("name")
    return nm.get("value", "") if nm is not None else ""


def _overall_rank(item: ET.Element) -> str:
    for rk in item.findall("statistics/ratings/ranks/rank"):
        if rk.get("name") == "boardgame":
            return rk.get("value", "")
    return ""


def enrich(ids: list[int]) -> dict[int, dict]:
    """Call the API in batches and parse the fields we care about."""
    result: dict[int, dict] = {}
    for i in range(0, len(ids), BATCH):
        chunk = ids[i : i + BATCH]
        url = f"{API}?id={','.join(map(str, chunk))}&stats=1"
        root = ET.fromstring(_get(url))
        for item in root.findall("item"):
            gid = int(item.get("id"))
            result[gid] = {
                "type": item.get("type", ""),
                "categories": _links(item, "boardgamecategory"),
                "mechanisms": _links(item, "boardgamemechanic"),
                "rating_avg": _stat(item, "average"),
                "rating_geek": _stat(item, "bayesaverage"),
                "complexity": _stat(item, "averageweight"),
                "rank": _overall_rank(item),
                "name": _name(item),
            }
        sys.stderr.write(f"  fetched {min(i + BATCH, len(ids))}/{len(ids)}\n")
        time.sleep(PAUSE)
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--ranks-csv", help="path to BGG's boardgames_ranks.csv dump")
    src.add_argument("--scrape-browse", action="store_true",
                     help="scrape ranked ids from the public /browse pages")
    ap.add_argument("--top", type=int, default=300, help="how many games (default 300)")
    ap.add_argument("-o", "--out", default="bgg_top_games.csv", help="output CSV path")
    args = ap.parse_args()

    if args.ranks_csv:
        ranked = ranked_ids_from_csv(args.ranks_csv, args.top)
    else:
        ranked = ranked_ids_from_browse(args.top)
    ids = [gid for gid, _ in ranked]
    csv_meta = {gid: meta for gid, meta in ranked}
    sys.stderr.write(f"Enriching {len(ids)} games via the BGG XML API...\n")
    api_data = enrich(ids)

    cols = ["rank", "name", "type", "categories", "mechanisms",
            "rating_geek", "rating_avg", "complexity", "bgg_id"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for pos, gid in enumerate(ids, start=1):
            d = api_data.get(gid, {})
            meta = csv_meta.get(gid, {})
            w.writerow({
                "rank": d.get("rank") or meta.get("rank") or pos,
                "name": d.get("name") or meta.get("name", ""),
                "type": d.get("type", ""),
                "categories": d.get("categories", ""),
                "mechanisms": d.get("mechanisms", ""),
                "rating_geek": d.get("rating_geek") or meta.get("bayesaverage", ""),
                "rating_avg": d.get("rating_avg") or meta.get("average", ""),
                "complexity": d.get("complexity", ""),
                "bgg_id": gid,
            })
    sys.stderr.write(f"Wrote {len(ids)} rows to {args.out}\n")


if __name__ == "__main__":
    main()
