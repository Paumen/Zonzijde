"""Run report (OPS-4): the inspectable trail for the edition PR.

Regenerates ``editions/<date>/report.md`` from whatever stage artifacts exist
in ``work/`` — the funnel counts, per-feed results, and rejection breakdown.
Later phases extend it (scores distribution, drops, corrections, LLM cost).
"""

from __future__ import annotations

import json
from collections import Counter

from .context import RunContext
from .contracts import FeedItem, RejectedItem, load_artifact


def _table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def build(ctx: RunContext) -> str:
    work = ctx.work_dir
    parts = [f"# Run report — edition {ctx.edition.isoformat()}", ""]

    log_path = work / "10-fetch-log.json"
    items_path = work / "20-filtered.json"
    rejected_path = work / "20-rejected.json"

    if log_path.is_file():
        log = json.loads(log_path.read_text(encoding="utf-8"))
        feeds = log["feeds"]
        entries = sum(f["entries"] for f in feeds)
        kept = sum(f["kept"] for f in feeds)
        failed = [f for f in feeds if f["error"]]
        parts += [
            "## Funnel", "",
            f"- window: {log['window_days']} days (from {log['window_start']}, SRC-4)",
            f"- S1 fetch: {entries} feed items → {kept} in window"
            f" ({len(feeds) - len(failed)}/{len(feeds)} feeds ok)",
        ]
        if items_path.is_file():
            filtered = load_artifact(items_path, FeedItem)
            rejected = load_artifact(rejected_path, RejectedItem)
            parts += [f"- S2 filter: {kept} → {len(filtered)} candidates"
                      f" ({len(rejected)} rejected)"]
        parts += ["", "## Feeds", "",
                  _table(["bron", "items", "in window", "undated", "error"],
                         [[f["bron"], f["entries"], f["kept"], f["undated"],
                           f["error"] or "—"] for f in feeds])]

    if rejected_path.is_file():
        rejected = load_artifact(rejected_path, RejectedItem)
        reasons = Counter()
        for r in rejected:
            if r.reason == "duplicate":
                reasons["duplicate"] += 1
            else:
                # bucket:B1,B3 → count every matched bucket
                for b in r.reason.removeprefix("bucket:").split(","):
                    reasons[b] += 1
        parts += ["", "## Rejected (PIPE-2)", "",
                  _table(["reason", "count"],
                         [[k, v] for k, v in sorted(reasons.items())])]

    return "\n".join(parts) + "\n"


def run(ctx: RunContext) -> None:
    ctx.edition_dir.mkdir(parents=True, exist_ok=True)
    report = build(ctx)
    (ctx.edition_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"report: {ctx.edition_dir / 'report.md'}")
