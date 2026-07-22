from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from .context import RunContext
from .contracts import (ArticleText, Candidate, Draft, EditionManifest,
                        EditionOutline, FeedItem, RejectedItem,
                        ReviewedArticle, ScoredItem, load_artifact, load_model)

ACTORS = {
    "F1": ("fetch", "Bronnen", "code"),
    "F2": ("filter", "Correspondenten", "code"),
    "F3": ("score", "Analisten", "llm"),
    "F4": ("select", "Sectieredacteuren", "llm"),
    "F5": ("enrich", "Onderzoeksjournalisten", "code+llm"),
    "F6": ("outline", "Hoofdredacteur", "llm"),
    "F7": ("write", "Reporters", "llm"),
    "F8": ("review", "Eindredacteuren", "llm"),
    "F9": ("compose", "Vormgevers", "code+llm"),
}

SCOPE_LABELS = {"L": "lokaal", "R": "regionaal",
                "N": "nationaal", "I": "internationaal"}
SPEED_PRESETS = [4, 8, 12]


def _trim(text: str | None, n: int) -> str | None:
    if text is None:
        return None
    text = " ".join(text.split())
    return text if len(text) <= n else text[:n - 1] + "…"


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _wall(log: dict) -> int | None:
    llm = log.get("llm") if isinstance(log, dict) else None
    return llm.get("wall_ms") if llm else None


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"trace: fidelity check failed — {msg}")


def build(work: Path, edition_json: Path) -> dict:
    f1 = load_artifact(work / "f1-items.json", FeedItem)
    filtered = load_artifact(work / "f2-filtered.json", FeedItem)
    rejected = load_artifact(work / "f2-rejected.json", RejectedItem)
    scored = load_artifact(work / "f3-scored.json", ScoredItem)
    candidates = load_artifact(work / "f4-candidates.json", Candidate)
    articles = load_artifact(work / "f5-articles.json", ArticleText)
    outline = load_model(work / "f6-outline.json", EditionOutline)
    drafts = load_artifact(work / "f7-drafts.json", Draft)
    reviewed = load_artifact(work / "f8-reviewed.json", ReviewedArticle)

    fetch_log = _read(work / "f1-fetch-log.json")
    score_log = _read(work / "f3-score-log.json")
    select_log = _read(work / "f4-select-log.json")
    enrich_log = _read(work / "f5-enrich-log.json")
    outline_log = _read(work / "f6-outline-log.json")
    write_log = _read(work / "f7-write-log.json")
    review_log = _read(work / "f8-review-log.json")
    compose_log = _read(work / "f9-compose-log.json")
    manifest = load_model(edition_json, EditionManifest)

    batch_size = int(score_log.get("batch_size") or 80)
    batch_of = {it.id: i // batch_size for i, it in enumerate(filtered)}
    score_of = {s.id: s.score for s in scored}

    cand_of: dict[str, tuple[str, str, str]] = {}
    for c in candidates:
        for it in c.items:
            cand_of[it.id] = (c.scope, c.topic, it.samenvatting)
    art_of = {a.id: a for a in articles}
    picked_slot: dict[str, int] = {}
    for s in outline.slots:
        for sid in s.source_ids:
            picked_slot.setdefault(sid, s.pos)

    positive_ids = {s.id for s in scored if s.score >= 1}
    _require(set(cand_of) <= positive_ids,
             "F4 selected ids not a subset of F3-positive ids")
    _require(set(art_of) <= set(cand_of),
             "F5 article ids not a subset of F4 selected ids")
    _require(set(picked_slot) <= set(art_of),
             "F6 source_ids not a subset of F5 article ids")

    items = []
    exit_tally: dict[str, int] = {}
    uid = 0

    def _base(it: FeedItem) -> dict:
        nonlocal uid
        rec = {
            "uid": uid, "id": it.id, "bron": it.bron, "feed": it.source,
            "scope": it.scopes[0] if it.scopes else "",
            "scopes": it.scopes,
            "title": _trim(it.title, 160),
            "summary": _trim(it.summary, 180),
            "score": None, "batch": None,
            "topic": None, "samenvatting": None,
            "ok": None, "method": None, "words": None,
            "slot": None, "exit_fase": None, "exit_bin": None,
        }
        uid += 1
        return rec

    for it in filtered:
        rec = _base(it)
        rec["batch"] = batch_of.get(it.id)
        score = score_of.get(it.id)
        rec["score"] = score
        if score is None:
            rec["exit_fase"], rec["exit_bin"] = "F3", "unscored"
        elif score < 0:
            rec["exit_fase"], rec["exit_bin"] = "F3", "negative_score"
        elif score == 0:
            rec["exit_fase"], rec["exit_bin"] = "F3", "neutral"
        else:
            cand = cand_of.get(it.id)
            if cand is None:
                rec["exit_fase"], rec["exit_bin"] = "F4", "not_selected"
            else:
                _, topic, samv = cand
                rec["topic"] = _trim(topic, 120)
                rec["samenvatting"] = _trim(samv, 240)
                art = art_of.get(it.id)
                if art is not None:
                    rec["ok"] = art.ok
                    rec["method"] = art.method
                    rec["words"] = art.words
                if art is None or not art.ok:
                    rec["exit_fase"], rec["exit_bin"] = "F5", "no_source"
                else:
                    slot = picked_slot.get(it.id)
                    rec["slot"] = slot
                    if slot is None:
                        rec["exit_fase"], rec["exit_bin"] = "F6", "not_picked"
        if rec["exit_bin"]:
            exit_tally[rec["exit_bin"]] = exit_tally.get(rec["exit_bin"], 0) + 1
        items.append(rec)

    for it in rejected:
        rec = _base(it)
        rec["exit_fase"] = "F2"
        rec["exit_bin"] = ("duplicate" if it.reason == "duplicate"
                           else "negative_filter")
        rec["buckets"] = (None if it.reason == "duplicate"
                          else it.reason.removeprefix("bucket:").split(","))
        exit_tally[rec["exit_bin"]] = exit_tally.get(rec["exit_bin"], 0) + 1
        items.append(rec)

    _require(len(items) == len(f1),
             f"node count {len(items)} != f1 items {len(f1)}")

    draft_of = {d.pos: d for d in drafts}
    rev_of = {r.pos: r for r in reviewed}
    ill_by_pos: dict[int, dict] = {}
    for ill in compose_log.get("illustrations") or []:
        pos, fp = ill.get("pos"), ill.get("file")
        if pos and fp:
            svg_path = work.parent / fp
            svg = (svg_path.read_text(encoding="utf-8")
                   if svg_path.is_file() else None)
            ill_by_pos[pos] = {"subject": ill.get("subject"), "svg": svg}

    slots = []
    for s in outline.slots:
        d = draft_of.get(s.pos)
        rv = rev_of.get(s.pos)
        slots.append({
            "pos": s.pos, "scope": s.scope, "length": s.length,
            "topic": _trim(s.topic, 120), "angle": _trim(s.angle, 320),
            "location": s.location,
            "source_date": s.source_date.isoformat() if s.source_date else None,
            "source_ids": s.source_ids,
            "draft_words": d.words if d else None,
            "draft_excerpt": _trim(d.text, 400) if d else None,
            "title": (rv.title if rv else (d.title if d else None)),
            "words": rv.words if rv else None,
            "correcties": (rv.review.correcties if rv else []),
            "illustration": ill_by_pos.get(s.pos),
        })

    entries = sum(f["entries"] for f in fetch_log["feeds"])
    in_window = len(f1)
    dup = sum(1 for r in rejected if r.reason == "duplicate")
    neg_filter = len(rejected) - dup
    neg_score = sum(1 for s in scored if s.score < 0)
    neutral = sum(1 for s in scored if s.score == 0)
    positive = len(positive_ids)
    selrows = len(cand_of)
    ok_ids = {a.id for a in articles if a.ok}
    picked = len(picked_slot)

    reason_bins = [
        {"key": "too_old", "label": "te oud", "fase": "F1",
         "count": entries - in_window, "identified": False},
        {"key": "duplicate", "label": "dubbel", "fase": "F2",
         "count": dup, "identified": True},
        {"key": "negative_filter", "label": "negatief / promo", "fase": "F2",
         "count": neg_filter, "identified": True},
        {"key": "negative_score", "label": "negatief nieuws", "fase": "F3",
         "count": neg_score, "identified": True},
        {"key": "neutral", "label": "neutraal / gemengd", "fase": "F3",
         "count": neutral, "identified": True},
        {"key": "not_selected", "label": "niet gekozen", "fase": "F4",
         "count": positive - selrows, "identified": True},
        {"key": "no_source", "label": "geen bron", "fase": "F5",
         "count": selrows - len(ok_ids), "identified": True},
        {"key": "not_picked", "label": "niet geplaatst", "fase": "F6",
         "count": len(ok_ids) - picked, "identified": True},
    ]
    for b in reason_bins:
        if b["identified"]:
            _require(exit_tally.get(b["key"], 0) == b["count"],
                     f"bin {b['key']} count {b['count']} != "
                     f"tallied {exit_tally.get(b['key'], 0)}")

    dist = {str(k): int(v) for k, v in score_log["distribution"].items()}
    batches = [b["items"] for b in score_log.get("batches", [])]

    fases = [
        {"id": "F1", **_fase("F1"), "real_ms": None,
         "in": entries, "out": in_window},
        {"id": "F2", **_fase("F2"), "real_ms": None,
         "in": in_window, "out": len(filtered)},
        {"id": "F3", **_fase("F3"), "real_ms": _wall(score_log),
         "in": len(filtered), "out": positive,
         "model": score_log.get("model"), "batches": batches,
         "distribution": dist},
        {"id": "F4", **_fase("F4"), "real_ms": _wall(select_log),
         "in": positive, "out": selrows,
         "model": select_log.get("model"), "topics": len(candidates)},
        {"id": "F5", **_fase("F5"), "real_ms": _wall(enrich_log),
         "in": selrows, "out": len(ok_ids),
         "calls": len(enrich_log.get("topics", [])),
         "methods": enrich_log.get("methods")},
        {"id": "F6", **_fase("F6"), "real_ms": _wall(outline_log),
         "in": len(ok_ids), "out": picked,
         "model": outline_log.get("model"), "slots": len(outline.slots)},
        {"id": "F7", **_fase("F7"), "real_ms": _wall(write_log),
         "in": len(outline.slots), "out": len(drafts),
         "model": write_log.get("model"),
         "calls": len(write_log.get("slots", []))},
        {"id": "F8", **_fase("F8"), "real_ms": _wall(review_log),
         "in": len(drafts), "out": len(reviewed),
         "model": review_log.get("model"),
         "calls": len(review_log.get("articles", []))},
        {"id": "F9", **_fase("F9"), "real_ms": _wall(compose_log),
         "in": len(reviewed), "out": len(manifest.articles),
         "recompiles": compose_log.get("recompiles"),
         "illustrations": len(ill_by_pos)},
    ]

    scopes_by_source: dict[str, list[str]] = {}
    for it in f1:
        scopes_by_source.setdefault(it.source, it.scopes)
    sources = [{
        "source": f["source"], "bron": f["bron"],
        "scopes": scopes_by_source.get(f["source"], []),
        "entries": f["entries"], "kept": f["kept"],
        "out_of_window": f["out_of_window"], "error": f.get("error") or "",
    } for f in fetch_log["feeds"]]

    meta = {
        "edition": manifest.edition.isoformat(),
        "nr": manifest.nr,
        "generated_at": datetime.now().astimezone().isoformat(),
        "scopes": list(SCOPE_LABELS),
        "scope_labels": SCOPE_LABELS,
        "speed_presets": SPEED_PRESETS,
        "default_speed": SPEED_PRESETS[0],
        "counts": {
            "entries": entries, "in_window": in_window,
            "filtered": len(filtered), "positive": positive,
            "selected_rows": selrows, "topics": len(candidates),
            "enriched_ok": len(ok_ids), "picked": picked,
            "slots": len(outline.slots), "articles": len(manifest.articles),
            "pages": manifest.counts.get("pages"),
            "words_body": manifest.counts.get("words_body"),
        },
    }

    return {"meta": meta, "fases": fases, "sources": sources,
            "reason_bins": reason_bins, "items": items, "slots": slots}


def _fase(fid: str) -> dict:
    key, actor, kind = ACTORS[fid]
    return {"key": key, "actor": actor, "kind": kind}


def _scopes_of(source: str, candidates, f1) -> list[str]:
    for it in f1:
        if it.source == source:
            return it.scopes
    return []


def run(ctx: RunContext, work: Path | None = None,
        out: Path | None = None) -> None:
    work_dir = work or ctx.work_dir
    edition_json = work_dir.parent / "edition.json"
    if not edition_json.is_file():
        raise SystemExit(f"trace: edition.json not found at {edition_json}")
    trace = build(work_dir, edition_json)
    out_path = out or (ctx.root / "viz" / "viz-trace.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(trace, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    print(f"trace: {out_path} "
          f"({trace['meta']['counts']['in_window']} items, "
          f"{len(trace['slots'])} slots)")
