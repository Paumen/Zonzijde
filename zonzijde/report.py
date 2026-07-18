from __future__ import annotations

import json
from collections import Counter

from .context import RunContext
from .contracts import (Candidate, EditionOutline, FeedItem, RejectedItem,
                        ReviewedArticle, ScoredItem, load_artifact, load_model)


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
    enrich_log_path = work / "50-enrich-log.json"
    outline_path = work / "60-outline.json"
    write_log_path = work / "70-write-log.json"
    review_log_path = work / "80-review-log.json"
    reviewed_path = work / "80-reviewed.json"

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
        if enrich_log_path.is_file():
            elog = json.loads(enrich_log_path.read_text(encoding="utf-8"))
            m = elog["methods"]
            parts += [f"- S5 enrich: {elog['rows']} source rows → "
                      f"{elog['full_text']} full texts"
                      f" (requests {m['requests']}, playwright {m['playwright']})"
                      + (f"; {len(elog['dropped_topics'])} topics dropped (PIPE-5)"
                         if elog["dropped_topics"] else "")]
        if outline_path.is_file():
            outline = load_model(outline_path, EditionOutline)
            olog = json.loads((work / "60-outline-log.json")
                              .read_text(encoding="utf-8"))
            planned = olog["planned_words"]
            parts += [f"- S6 outline: {len(outline.slots)} slots, planned "
                      f"{planned['min']}–{planned['max']} words"]
        if write_log_path.is_file():
            wlog = json.loads(write_log_path.read_text(encoding="utf-8"))
            parts += [f"- S7 write: {len(wlog['slots'])} articles, "
                      f"{wlog['words_total']} words"]
        if review_log_path.is_file():
            rlog = json.loads(review_log_path.read_text(encoding="utf-8"))
            issues = sum(len(a["fact_issues"]) for a in rlog["articles"])
            corr = sum(len(a["corrections"]) for a in rlog["articles"])
            body = ctx.edition_cfg["body_words"]
            parts += [f"- S8 review: {issues} fact issue(s), {corr} "
                      f"correction(s), {rlog['words_total']} words body text"
                      f" (ED-5 target {body['min']}–{body['max']})"]
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
                  _table(["scope", "topic", "bronnen"],
                         [[c.scope, c.topic,
                           ", ".join(r.bron for r in c.items)]
                          for c in candidates])]

    if enrich_log_path.is_file():
        elog = json.loads(enrich_log_path.read_text(encoding="utf-8"))
        rows = []
        for t in elog["topics"]:
            status = ("**dropped** — no full text on any source row"
                      if t["dropped"] else "ok")
            rows.append([t["scope"], t["rank"], t["topic"],
                         f"{t['ok_rows']}/{t['rows']}", status])
        parts += ["", "## Full text (PIPE-5)", "",
                  _table(["scope", "rank", "topic", "full text", "status"], rows)]

    if outline_path.is_file():
        outline = load_model(outline_path, EditionOutline)
        parts += ["", "## Edition plan (PIPE-6)", "",
                  _table(["pos", "scope", "length", "type", "topic",
                          "location", "source date"],
                         [[s.pos, s.scope, s.length, s.type, s.topic,
                           s.location, s.source_date or "—"]
                          for s in outline.slots])]
        ill = outline.illustration
        parts += ["", f"Illustration (EL-3): slot {ill.slot_pos} — {ill.subject}"]

    if reviewed_path.is_file():
        reviewed = load_artifact(reviewed_path, ReviewedArticle)
        rlog = json.loads(review_log_path.read_text(encoding="utf-8"))
        draft_words = {a["pos"]: a["words"]["draft"] for a in rlog["articles"]}
        parts += ["", "## Articles (PIPE-7/8)", "",
                  _table(["pos", "title", "words draft → reviewed", "paragraphs"],
                         [[r.pos, r.title,
                           f"{draft_words.get(r.pos, '—')} → {r.words}",
                           len(r.paragraphs)] for r in reviewed])]
        correction_lines = []
        for r in reviewed:
            for issue in r.review.fact_issues:
                correction_lines.append(f"- slot {r.pos} (fact, WR-2): {issue}")
            for corr in r.review.corrections:
                correction_lines.append(f"- slot {r.pos}: {corr}")
        parts += ["", "## Correction log (PIPE-8)", ""]
        parts += correction_lines or ["No corrections — clean review."]

    return "\n".join(parts) + "\n"


def run(ctx: RunContext) -> None:
    ctx.edition_dir.mkdir(parents=True, exist_ok=True)
    report = build(ctx)
    (ctx.edition_dir / "report.md").write_text(report, encoding="utf-8")
    print(f"report: {ctx.edition_dir / 'report.md'}")
