from __future__ import annotations

import re

from ..context import RunContext
from ..contracts import FeedItem, RejectedItem, load_artifact, save_artifact

_PL = r"[^\W\d_]"


def compile_buckets(buckets: dict[str, str]) -> dict[str, re.Pattern]:
    return {name: re.compile(pattern.replace(r"\p{L}", _PL), re.IGNORECASE)
            for name, pattern in buckets.items()}


def matching_buckets(title: str, compiled: dict[str, re.Pattern]) -> list[str]:
    return [name for name, rx in compiled.items() if rx.search(title)]


def split_items(
    items: list[FeedItem], compiled: dict[str, re.Pattern]
) -> tuple[list[FeedItem], list[RejectedItem]]:
    kept: list[FeedItem] = []
    rejected: list[RejectedItem] = []
    seen: set[str] = set()
    for item in items:
        if item.id in seen:
            reason = "duplicate"
        elif hits := matching_buckets(item.title, compiled):
            reason = "bucket:" + ",".join(hits)
        else:
            seen.add(item.id)
            kept.append(item)
            continue
        seen.add(item.id)
        rejected.append(RejectedItem(**item.model_dump(), reason=reason))
    return kept, rejected


def run(ctx: RunContext) -> None:
    items = load_artifact(ctx.work_dir / "f1-items.json", FeedItem)
    kept, rejected = split_items(items, compile_buckets(ctx.buckets))
    save_artifact(ctx.work_dir / "f2-filtered.json", kept)
    save_artifact(ctx.work_dir / "f2-rejected.json", rejected)
    dupes = sum(1 for r in rejected if r.reason == "duplicate")
    print(f"F2 filter: {len(items)} in → {len(kept)} kept, "
          f"{dupes} duplicates, {len(rejected) - dupes} bucket-blocked")
