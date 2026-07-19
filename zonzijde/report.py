from __future__ import annotations

import json
from collections import Counter

from .context import RunContext
from .contracts import (ArticleText, Candidate, EditionOutline, FeedItem,
                        RejectedItem, ReviewedArticle, ScoredItem,
                        load_artifact, load_model)


def _table(headers: list[str], rows: list[list]) -> str:
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join("---" for _ in headers) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in rows]
    return "\n".join(lines)


def _sk(name: str) -> str:
    return '"' + name.replace('"', "'") + '"' if "," in name or '"' in name else name


def _reflink(url: str) -> str:
    for prefix in ("https://", "http://"):
        if url.startswith(prefix):
            url = url[len(prefix):]
            break
    if url.startswith("www."):
        url = url[4:]
    return url if len(url) <= 60 else url[:59] + "…"


def _sankey(flows: list[tuple[str, str, int]]) -> list[str]:
    flows = [(s, d, v) for s, d, v in flows if v and v > 0]
    if not flows:
        return []
    return ["```mermaid",
            "---", "config:", "  sankey:", "    nodeAlignment: left", "---",
            "sankey-beta", ""] + [
        f"{_sk(s)},{_sk(d)},{v}" for s, d, v in flows] + ["```"]


def _overview(work) -> list[str]:
    fetch_path = work / "10-fetch-log.json"
    if not fetch_path.is_file():
        return []
    feeds = json.loads(fetch_path.read_text(encoding="utf-8"))["feeds"]
    entries = sum(f["entries"] for f in feeds)
    kept = sum(f["kept"] for f in feeds)

    item: list[tuple[str, str, int]] = [
        ("Fetched", "In window", kept),
        ("Fetched", "Out of window", entries - kept),
    ]
    filtered = positive = rows = None
    if (work / "20-filtered.json").is_file():
        filtered = len(load_artifact(work / "20-filtered.json", FeedItem))
        item.append(("In window", "Candidates", filtered))
        if (work / "20-rejected.json").is_file():
            reasons = Counter()
            for r in load_artifact(work / "20-rejected.json", RejectedItem):
                reasons["duplicate" if r.reason == "duplicate" else "buckets"] += 1
            for k in ("buckets", "duplicate"):
                if reasons[k]:
                    item.append(("In window", f"Reject: {k}", reasons[k]))
    if filtered and (work / "30-score-log.json").is_file():
        slog = json.loads((work / "30-score-log.json").read_text(encoding="utf-8"))
        dist = slog["distribution"]
        positive = int(dist.get("1", 0)) + int(dist.get("2", 0))
        item.append(("Candidates", "Negative (-1/-2)",
                     int(dist.get("-1", 0)) + int(dist.get("-2", 0))))
        item.append(("Candidates", "Unscored", len(slog.get("unscored_ids", []))))
        item.append(("Candidates", "Score 0", int(dist.get("0", 0))))
        item.append(("Candidates", "Positive (+1/+2)", positive))
    if positive and (work / "40-candidates.json").is_file():
        rows = sum(len(c.items) for c in
                   load_artifact(work / "40-candidates.json", Candidate))
        item.append(("Positive (+1/+2)", "Not selected", positive - rows))
        item.append(("Positive (+1/+2)", "Selected rows", rows))
    if rows and (work / "50-enrich-log.json").is_file():
        ft = json.loads((work / "50-enrich-log.json")
                        .read_text(encoding="utf-8")).get("full_text")
        if ft is not None:
            item.append(("Selected rows", "No full text", rows - ft))
            item.append(("Selected rows", "Enriched", ft))

    edition: list[tuple[str, str, int]] = []
    if (work / "60-outline.json").is_file():
        n_slots = len(load_model(work / "60-outline.json", EditionOutline).slots)
        written = n_slots
        if (work / "70-write-log.json").is_file():
            wf = len(json.loads((work / "70-write-log.json")
                                .read_text(encoding="utf-8")).get("failed_slots") or [])
            written = n_slots - wf
            edition += [("Outline slots", "Written", written),
                        ("Outline slots", "Write failed", wf)]
        if (work / "80-review-log.json").is_file():
            rf = len(json.loads((work / "80-review-log.json")
                                .read_text(encoding="utf-8")).get("failed_slots") or [])
            edition += [("Written", "Reviewed", written - rf),
                        ("Written", "Review failed", rf)]

    item_sankey = _sankey(item)
    edition_sankey = _sankey(edition)
    if not item_sankey and not edition_sankey:
        return []
    out = ["## Funnel overview", ""]
    if item_sankey:
        out += ["Items — fetched → in window → filtered → scored → selected → "
                "enriched (drop branches show why and what type):", ""]
        out += item_sankey + [""]
    if edition_sankey:
        out += ["Edition — outline slots → written → reviewed:", ""]
        out += edition_sankey + [""]
    return out


def _llm_usage(work) -> list[str]:
    stages = [("S3 score", "30-score-log.json"), ("S4 select", "40-select-log.json"),
              ("S5 enrich", "50-enrich-log.json"), ("S6 outline", "60-outline-log.json"),
              ("S7 write", "70-write-log.json"), ("S8 review", "80-review-log.json")]
    rows = []
    tot = Counter()
    for label, fn in stages:
        p = work / fn
        if not p.is_file():
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        u = d.get("llm")
        if not u:
            continue
        intok = (u["input_tokens"] + (u.get("cache_read_tokens") or 0)
                 + (u.get("cache_creation_tokens") or 0))
        wall = f"{u['wall_ms'] / 1000:.1f}s" if u.get("wall_ms") else "—"
        cost = f"${u['cost_usd']:.4f}" if u.get("cost_usd") is not None else "—"
        rows.append([label, d.get("model") or "—", d.get("effort") or "—",
                     u["calls"], u["turns"], f"{intok:,}",
                     f"{u['output_tokens']:,}", u["tool_uses"],
                     f"{u['thinking_chars']:,}", wall, cost])
        tot["input_tokens"] += intok
        for k in ("calls", "turns", "output_tokens",
                  "tool_uses", "thinking_chars", "wall_ms"):
            tot[k] += u.get(k) or 0
        if u.get("cost_usd") is not None:
            tot["cost_usd"] += u["cost_usd"]
    if not rows:
        return []
    rows.append(["**total**", "", "", tot["calls"], tot["turns"],
                 f"{tot['input_tokens']:,}", f"{tot['output_tokens']:,}",
                 tot["tool_uses"], f"{tot['thinking_chars']:,}",
                 f"{tot['wall_ms'] / 1000:.1f}s",
                 f"${tot['cost_usd']:.4f}" if tot["cost_usd"] else "—"])
    return ["## LLM usage (OPS-4)", "",
            _table(["stage", "model", "effort", "calls", "turns", "in tok",
                    "out tok", "tools", "think chars", "wall", "cost"], rows)]


def build(ctx: RunContext) -> str:
    work = ctx.work_dir
    parts = [f"# Run report — edition {ctx.edition.isoformat()}", ""]
    parts += _overview(work)

    log_path = work / "10-fetch-log.json"
    items_path = work / "20-filtered.json"
    rejected_path = work / "20-rejected.json"
    score_log_path = work / "30-score-log.json"
    candidates_path = work / "40-candidates.json"
    enrich_log_path = work / "50-enrich-log.json"
    articles_path = work / "50-articles.json"
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
            wfailed = wlog.get("failed_slots") or []
            parts += [f"- S7 write: {len(wlog['slots'])} articles, "
                      f"{wlog['words_total']} words"
                      + (f"; **{len(wfailed)} slot(s) failed to write — "
                         f"hole(s) at pos {wfailed}**" if wfailed else "")]
        if review_log_path.is_file():
            rlog = json.loads(review_log_path.read_text(encoding="utf-8"))
            corr = sum(len(a["corrections"]) for a in rlog["articles"])
            rfailed = rlog.get("failed_slots") or []
            body = ctx.edition_cfg["body_words"]
            parts += [f"- S8 review: {corr} "
                      f"correction(s), {rlog['words_total']} words body text"
                      f" (ED-5 target {body['min']}–{body['max']})"
                      + (f"; **{len(rfailed)} slot(s) failed review at "
                         f"pos {rfailed}**" if rfailed else "")]
        parts += ["", "## Feeds", "",
                  _table(["bron", "items", "in window", "undated", "error"],
                         [[f["bron"], f["entries"], f["kept"], f["undated"],
                           f["error"] or "—"] for f in feeds])]
        usage = _llm_usage(work)
        if usage:
            parts += ["", *usage]

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

    if articles_path.is_file() and candidates_path.is_file():
        articles = {a.id: a for a in load_artifact(articles_path, ArticleText)}
        rows = []
        for c in load_artifact(candidates_path, Candidate):
            ok_rows = sum(1 for it in c.items
                          if it.id in articles and articles[it.id].ok)
            for it in c.items:
                a = articles.get(it.id)
                if a is None:
                    continue
                refs = a.references
                ref_words = sum(r.words for r in refs)
                ref_links = "<br>".join(_reflink(r.url) for r in refs) or "—"
                if a.ok:
                    status = "ok"
                elif ok_rows == 0:
                    status = "**dropped** — no sufficient row"
                else:
                    status = "insufficient"
                rows.append([c.scope, c.topic, a.bron,
                             len(a.samenvatting.split()), len(a.text.split()),
                             len(refs), ref_words, ref_links, status])
        parts += ["", "## Enrichment (PIPE-5)", "",
                  _table(["scope", "topic", "bron", "summary", "text",
                          "refs", "ref words", "ref links", "status"], rows)]

    if outline_path.is_file():
        outline = load_model(outline_path, EditionOutline)
        parts += ["", "## Edition plan (PIPE-6)", "",
                  _table(["pos", "scope", "length", "topic",
                          "location", "source date"],
                         [[s.pos, s.scope, s.length, s.topic,
                           s.location, s.source_date or "—"]
                          for s in outline.slots])]

    if reviewed_path.is_file():
        reviewed = load_artifact(reviewed_path, ReviewedArticle)
        rlog = json.loads(review_log_path.read_text(encoding="utf-8"))
        draft_words = {a["pos"]: a["words"]["draft"] for a in rlog["articles"]}
        parts += ["", "## Articles (PIPE-7/8)", "",
                  _table(["pos", "title", "words draft → reviewed"],
                         [[r.pos, r.title,
                           f"{draft_words.get(r.pos, '—')} → {r.words}"]
                          for r in reviewed])]
        correction_lines = []
        for r in reviewed:
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
