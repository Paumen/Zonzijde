"""Run report (OPS-4): the inspectable trail for the edition PR.

Regenerates ``editions/<date>/report.md`` from whatever stage artifacts exist
in ``work/`` — the funnel counts, per-feed results, and rejection breakdown.
Later phases extend it (scores distribution, drops, corrections, LLM cost).
"""

from __future__ import annotations

import json
from collections import Counter

from .context import RunContext
from .contracts import Candidate, FeedItem, RejectedItem, ScoredItem, load_artifact


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
    score_log_path = work / "30-score-log.json"
    candidates_path = work / "40-candidates.json"

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
        if score_log_path.is_file():
            scored = load_artifact(work / "30-scored.json", ScoredItem)
            positive = sum(1 for s in scored if s.score >= 1)
            unscored = len(json.loads(score_log_path.read_text(encoding="utf-8"))
                           ["unscored_ids"])
            parts += [f"- S3 score: {len(scored)} scored → {positive} at +1/+2"
                      + (f" ({unscored} unscored, excluded — PIPE-3)"
                         if unscored else "")]
        if candidates_path.is_file():
            candidates = load_artifact(candidates_path, Candidate)
            rows = sum(len(c.items) for c in candidates)
            parts += [f"- S4 select: {len(candidates)} topics ({rows} source rows)"]
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

    if score_log_path.is_file():
        log = json.loads(score_log_path.read_text(encoding="utf-8"))
        parts += ["", "## Scores (PIPE-3)", "",
                  f"model {log['model']}, prompt score.md v{log['prompt_version']}",
                  "",
                  _table(["score", "count"],
                         [[f"+{k}" if int(k) > 0 else k, v]
                          for k, v in log["distribution"].items()])]
        if log["unscored_ids"]:
            parts += ["", f"Unscored and excluded (fail-closed): "
                          f"{len(log['unscored_ids'])} items"]

    if candidates_path.is_file():
        candidates = load_artifact(candidates_path, Candidate)
        parts += ["", "## Selected topics (PIPE-4)", "",
                  _table(["scope", "rank", "topic", "bronnen"],
                         [[c.scope, c.rank, c.topic,
                           ", ".join(r.bron for r in c.items)]
                          for c in candidates])]

    return "\n".join(parts) + "\n"


def run(ctx: RunContext) -> None:
    ctx.edition_dir.mkdir(parents=True, exist_ok=True)
    report = build(ctx)
    (ctx.edition_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"report: {ctx.edition_dir / 'report.md'}")
