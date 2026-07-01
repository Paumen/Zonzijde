#!/usr/bin/env python3
"""Build a top-N board games CSV from a public, no-login BoardGameGeek dump.

This is the offline counterpart to ``bgg_top_games.py`` (which hits BGG's live
XML API and needs a login). It downloads a ready-made public CSV export of BGG
data and slices it to the top-N ranked games, so it works instantly with no
credentials.

Source dump
-----------
https://raw.githubusercontent.com/jalwz17/Board-Game-Data-Analysis/main/bgg_dataset.csv
This is the widely-mirrored "BoardGameGeek Dataset" (also on Kaggle as
andrewmvd/board-games), scraped from BGG in **February 2021**. It is
semicolon-delimited with comma decimal separators.

What it covers vs. what it doesn't
----------------------------------
Covered:  rank, name, year, mechanisms, rating (raw average), complexity (weight)
Coarse:   "domains" -- BGG's 8 top-level families (Strategy, Thematic, Family,
          Wargames, Abstract, Party, Children's, Customizable). These stand in
          for "categories"; the dump does not carry BGG's granular categories
          (Fantasy, Economic, Card Game, ...).
Absent:   game "type" (every ranked row here is a base boardgame, so we emit
          "boardgame") and the Geek/Bayes rating (only the raw average exists).

For a *current* top-N with granular categories, true type and the Geek rating,
use ``bgg_top_games.py`` with a logged-in BGG session cookie instead.

Usage
-----
    python3 tools/build_top_games_from_dump.py --top 300 -o data/bgg_top300.csv
"""
from __future__ import annotations

import argparse
import csv
import http.client
import io
import os
import sys
import time
import urllib.error
import urllib.request

DUMP_URL = (
    "https://raw.githubusercontent.com/jalwz17/Board-Game-Data-Analysis/"
    "main/bgg_dataset.csv"
)
SNAPSHOT = "2021-02"


def _num(value: str) -> str:
    """Normalise a European decimal ('8,79') to a plain float string ('8.79')."""
    return value.strip().replace(",", ".")


def _download(url: str, tries: int = 6) -> bytes:
    """Fetch a URL, resuming with HTTP Range if the stream is truncated.

    Some proxies close the connection early, so a plain ``resp.read()`` raises
    IncompleteRead. We keep what arrived (``exc.partial``) and re-request the
    remaining byte range until the whole body is in hand.
    """
    buf = bytearray()
    total: int | None = None
    backoff = 2.0
    for attempt in range(1, tries + 1):
        headers = {"Accept-Encoding": "identity"}  # avoid partial-gzip corruption
        if buf:
            headers["Range"] = f"bytes={len(buf)}-"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                if resp.status == 200 and buf:  # server ignored Range -> restart
                    buf = bytearray()
                cr = resp.headers.get("Content-Range")
                if cr and "/" in cr:
                    total = int(cr.rsplit("/", 1)[1])
                elif total is None and resp.headers.get("Content-Length"):
                    total = len(buf) + int(resp.headers["Content-Length"])
                buf += resp.read()
        except http.client.IncompleteRead as exc:
            buf += exc.partial
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt == tries:
                raise
            time.sleep(backoff)
            backoff *= 2
            continue
        if total is not None and len(buf) >= total:
            return bytes(buf)
        if total is None:  # no length info to verify against; take what we have
            return bytes(buf)
    raise RuntimeError(f"incomplete download from {url}: {len(buf)}/{total} bytes")


def load_dump(src: str) -> list[dict]:
    """Load the dump from a local file path or a URL."""
    if os.path.exists(src):
        data = open(src, "rb").read()
    else:
        data = _download(src)
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8-sig")), delimiter=";"))
    if not rows or "BGG Rank" not in rows[0]:
        raise RuntimeError(f"dump from {src} was empty or in an unexpected format")
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--top", type=int, default=300, help="how many games (default 300)")
    ap.add_argument("--url", default=DUMP_URL, help="override the source dump URL")
    ap.add_argument("-o", "--out", default="bgg_top_games.csv", help="output CSV path")
    args = ap.parse_args()

    rows = load_dump(args.url)
    ranked = [r for r in rows if r.get("BGG Rank", "").strip().isdigit()]
    ranked.sort(key=lambda r: int(r["BGG Rank"]))
    ranked = ranked[: args.top]

    cols = ["rank", "name", "year", "type", "domains", "mechanisms",
            "rating_avg", "complexity", "bgg_id"]
    with open(args.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in ranked:
            w.writerow({
                "rank": r["BGG Rank"].strip(),
                "name": r["Name"].strip(),
                "year": r.get("Year Published", "").strip(),
                "type": "boardgame",
                "domains": r.get("Domains", "").strip(),
                "mechanisms": r.get("Mechanics", "").strip(),
                "rating_avg": _num(r.get("Rating Average", "")),
                "complexity": _num(r.get("Complexity Average", "")),
                "bgg_id": r.get("ID", "").strip(),
            })
    sys.stderr.write(
        f"Wrote top {len(ranked)} games to {args.out} "
        f"(source snapshot: {SNAPSHOT}).\n"
    )


if __name__ == "__main__":
    main()
