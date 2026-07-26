from __future__ import annotations

import json
from pathlib import Path

from .context import RunContext
from .contracts import (ArticleText, Candidate, Draft, EditionManifest,
                        EditionOutline, FeedItem, RejectedItem,
                        ReviewedArticle, ScoredItem, load_artifact, load_model)
from .fases.f2_filter import compile_buckets
from .report import FASE_LOGS, fase_usage, funnel_flows

FASE_IDS = {
    "fetch": "F1", "filter": "F2", "score": "F3", "select": "F4",
    "enrich": "F5", "outline": "F6", "write": "F7", "review": "F8",
    "compose": "F9",
}

ACTORS = {
    "fetch": ("Bronnen", "code"),
    "filter": ("Correspondenten", "code"),
    "score": ("Analisten", "llm"),
    "select": ("Sectieredacteuren", "llm"),
    "enrich": ("Onderzoeksjournalisten", "code+llm"),
    "outline": ("Hoofdredacteur", "llm"),
    "write": ("Reporters", "llm"),
    "review": ("Eindredacteuren", "llm"),
    "compose": ("Vormgevers", "code+llm"),
}

SCOPE_LABELS = {"L": "lokaal", "R": "regionaal",
                "N": "nationaal", "I": "internationaal"}

EXIT_LABELS = {
    "too_old": "te oud",
    "no_link": "geen link",
    "duplicate": "dubbel",
    "buckets": "negatief / ruis",
    "unscored": "niet beoordeeld",
    "negative": "negatief nieuws",
    "neutral": "neutraal",
    "not_selected": "niet gekozen",
    "no_source": "geen bron",
    "not_placed": "niet geplaatst",
}

SPEEDS = [1, 4, 8, 12]
MIN_SCREEN_MS = 60_000


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise SystemExit(f"trace: fidelity check failed — {msg}")


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _iso(value) -> str | None:
    return value.isoformat() if value is not None else None


def _screen_ms(reals: dict[str, int]) -> dict[str, int]:
    deficit = sum(max(0, MIN_SCREEN_MS - ms) for ms in reals.values())
    surplus = sum(max(0, ms - MIN_SCREEN_MS) for ms in reals.values())
    factor = min(1.0, deficit / surplus) if surplus else 0.0
    return {
        key: (MIN_SCREEN_MS if ms <= MIN_SCREEN_MS
              else round(ms - (ms - MIN_SCREEN_MS) * factor))
        for key, ms in reals.items()
    }


def _bucket_hits(title: str, reason: str,
                 compiled: dict) -> list[dict]:
    hits = []
    for name in reason.removeprefix("bucket:").split(","):
        rx = compiled.get(name)
        m = rx.search(title) if rx else None
        hits.append({"bucket": name, "match": m.group(0) if m else None})
    return hits


def _partition(f1: list[FeedItem], filtered: list[FeedItem],
               rejected: list[RejectedItem]) -> list[RejectedItem | None]:
    out: list[RejectedItem | None] = []
    ki = ri = 0
    for it in f1:
        key = (it.id, it.source)
        if ki < len(filtered) and (filtered[ki].id, filtered[ki].source) == key:
            out.append(None)
            ki += 1
        elif ri < len(rejected) and (rejected[ri].id, rejected[ri].source) == key:
            out.append(rejected[ri])
            ri += 1
        else:
            _require(False, f"f1 item {key} is in neither f2 artifact in order")
    _require(ki == len(filtered) and ri == len(rejected),
             f"f2 artifacts not fully consumed ({ki}/{len(filtered)} kept, "
             f"{ri}/{len(rejected)} rejected)")
    return out


def build(ctx: RunContext) -> dict:
    work = ctx.work_dir
    f1 = load_artifact(work / "f1-items.json", FeedItem)
    filtered = load_artifact(work / "f2-filtered.json", FeedItem)
    rejected = load_artifact(work / "f2-rejected.json", RejectedItem)
    scored = load_artifact(work / "f3-scored.json", ScoredItem)
    candidates = load_artifact(work / "f4-candidates.json", Candidate)
    articles = load_artifact(work / "f5-articles.json", ArticleText)
    outline = load_model(work / "f6-outline.json", EditionOutline)
    drafts = load_artifact(work / "f7-drafts.json", Draft)
    reviewed = load_artifact(work / "f8-reviewed.json", ReviewedArticle)
    manifest = load_model(ctx.edition_dir / "edition.json", EditionManifest)

    logs = {key: _read(work / fn) for key, _label, fn in FASE_LOGS
            if fn and (work / fn).is_file()}
    fetch_log = _read(work / "f1-fetch-log.json")
    score_log = logs["score"]
    enrich_log = logs["enrich"]
    write_log = logs["write"]
    review_log = logs["review"]
    compose_log = logs["compose"]
    timeline = _read(work / "timeline.json")["fases"]

    compiled = compile_buckets(ctx.buckets)
    window_start = fetch_log["window_start"]
    scopes_of = {s.id: s.scopes for s in ctx.sources}

    batch_size = int(score_log["batch_size"])
    chunks = [filtered[off:off + batch_size]
              for off in range(0, len(filtered), batch_size)]
    log_batches = score_log["batches"]
    _require(len(chunks) == len(log_batches),
             f"{len(chunks)} derived batches != {len(log_batches)} logged")
    for i, (chunk, logged) in enumerate(zip(chunks, log_batches)):
        _require(len(chunk) == logged["items"],
                 f"batch {i}: {len(chunk)} derived != {logged['items']} logged")
    batch_of = {it.id: i for i, chunk in enumerate(chunks) for it in chunk}

    score_of = {s.id: s.score for s in scored}
    unscored = set(score_log["unscored_ids"])

    onderwerp_of: dict[str, int] = {}
    samenvatting_of: dict[str, str] = {}
    for oi, c in enumerate(candidates):
        for it in c.items:
            onderwerp_of[it.id] = oi
            samenvatting_of[it.id] = it.samenvatting
    art_of = {a.id: a for a in articles}
    pos_of: dict[str, int] = {}
    for s in outline.slots:
        for sid in s.source_ids:
            pos_of.setdefault(sid, s.pos)

    _require(set(onderwerp_of) <= {i for i, v in score_of.items() if v >= 1},
             "F4 selected ids are not all F3-positive")
    _require(set(art_of) == set(onderwerp_of),
             "F5 article ids do not match F4 selected ids")
    _require(set(pos_of) <= set(art_of),
             "F6 source_ids are not all F5 article ids")

    nodes: list[dict] = []
    exits: dict[str, int] = {}

    def _exit(bin_key: str, fase: str, detail: dict | None = None) -> dict:
        exits[bin_key] = exits.get(bin_key, 0) + 1
        return {"fase": fase, "bin": bin_key,
                "label": EXIT_LABELS[bin_key], **(detail or {})}

    outcomes = _partition(f1, filtered, rejected)
    for uid, (it, reject) in enumerate(zip(f1, outcomes)):
        node = {
            "uid": uid, "id": it.id, "source": it.source, "titled": True,
            "scopes": it.scopes,
            "f1": {"medium": it.bron, "bron_titel": it.title,
                   "bron_samenvatting": it.summary,
                   "bron_datum": _iso(it.published), "link": it.link},
        }
        if reject is not None:
            if reject.reason == "duplicate":
                node["exit"] = _exit("duplicate", "F2")
            else:
                node["exit"] = _exit(
                    "buckets", "F2",
                    {"hits": _bucket_hits(it.title, reject.reason, compiled)})
            nodes.append(node)
            continue

        if it.id in unscored:
            node["exit"] = _exit("unscored", "F3")
            nodes.append(node)
            continue

        score = score_of[it.id]
        node["f3"] = {"score": score, "batch": batch_of[it.id]}
        if score < 0:
            node["exit"] = _exit("negative", "F3")
        elif score == 0:
            node["exit"] = _exit("neutral", "F3")
        elif it.id not in onderwerp_of:
            node["exit"] = _exit("not_selected", "F4")
        else:
            oi = onderwerp_of[it.id]
            node["f4"] = {"onderwerp": oi,
                          "onderwerptitel": candidates[oi].topic,
                          "samenvatting": samenvatting_of[it.id]}
            a = art_of[it.id]
            node["f5"] = {
                "ok": a.ok, "method": a.method, "bron_tekst": a.text,
                "bron_woorden": a.words,
                "referentie_links": [r.url for r in a.references],
                "referentie_tekst": [
                    {"url": r.url, "ok": r.ok, "tekst": r.text, "woorden": r.words}
                    for r in a.references],
            }
            if not a.ok:
                node["exit"] = _exit("no_source", "F5")
            elif it.id not in pos_of:
                node["exit"] = _exit("not_placed", "F6")
            else:
                node["f6"] = {"pos": pos_of[it.id]}
        nodes.append(node)

    titled = len(nodes)
    ghost_uid = titled
    for feed in fetch_log["feeds"]:
        for bin_key, count in (("too_old", feed["out_of_window"]),
                               ("no_link", feed["no_link"])):
            for _ in range(count):
                nodes.append({
                    "uid": ghost_uid, "id": None, "source": feed["source"],
                    "titled": False, "scopes": scopes_of.get(feed["source"], []),
                    "f1": {"medium": feed["bron"], "bron_titel": None,
                           "bron_samenvatting": None, "bron_datum": None,
                           "link": None},
                    "exit": _exit(bin_key, "F1"),
                })
                ghost_uid += 1

    entries = sum(f["entries"] for f in fetch_log["feeds"])
    _require(titled == len(f1), f"{titled} titled nodes != {len(f1)} f1 items")
    _require(len(nodes) == entries,
             f"{len(nodes)} nodes != {entries} fetched entries")
    placed = [n for n in nodes if "exit" not in n]
    _require(all(("exit" in n) != ("f6" in n) for n in nodes),
             "a node is both placed and dropped")
    _require(len(placed) == len(pos_of),
             f"{len(placed)} placed nodes != {len(pos_of)} outline source ids")
    for n in nodes:
        if n["f1"]["bron_datum"] is not None:
            _require(n["f1"]["bron_datum"] >= window_start,
                     f"node {n['uid']} predates the window")

    item_flows, edition_flows = funnel_flows(work)
    flow = {(s, d): v for s, d, v in item_flows}
    for (src, dst), expected in (
        (("Fetched", "in"), titled),
        (("Fetched", "Out of window"), exits.get("too_old", 0)),
        (("in", "Items"), len(filtered)),
        (("in", "Reject: duplicate"), exits.get("duplicate", 0)),
        (("in", "Reject: buckets"), exits.get("buckets", 0)),
        (("Items", "Score 0"), exits.get("neutral", 0)),
        (("Items", "Negative (-1/-2)"), exits.get("negative", 0)),
        (("Items", "Unscored"), exits.get("unscored", 0)),
        (("Positive (+1/+2)", "Selected bronnen"), len(art_of)),
        (("Positive (+1/+2)", "Not selected"), exits.get("not_selected", 0)),
    ):
        _require(flow.get((src, dst), 0) == expected,
                 f"funnel {src}→{dst} is {flow.get((src, dst))}, trace has {expected}")

    reals = {key: timeline[key]["elapsed_ms"]
             for key, _label, _fn in FASE_LOGS if key in timeline}
    screens = _screen_ms(reals)
    _require(min(screens.values()) >= MIN_SCREEN_MS,
             "a fase falls below the on-screen floor")
    _require(abs(sum(screens.values()) - sum(reals.values())) <= len(screens),
             f"schedule total {sum(screens.values())} != real {sum(reals.values())}")

    usage = fase_usage(work)
    sub_events = {
        "score": [{"items": b["items"], "scored": b["scored"],
                   "problems": b["problems"]} for b in log_batches],
        "enrich": [{"onderwerp": t["topic"], "scope": t["scope"],
                    "rows": t["rows"], "ok_rows": t["ok_rows"]}
                   for t in enrich_log["topics"]],
        "write": [{"pos": s["pos"], "woorden": s["words"],
                   "model": s.get("model"), "problems": s["problems"]}
                  for s in write_log["slots"]],
        "review": [{"pos": a["pos"], "woorden": a["words"],
                    "problems": a["problems"]} for a in review_log["articles"]],
    }

    counts_in = {
        "fetch": entries, "filter": len(f1), "score": len(filtered),
        "select": sum(1 for v in score_of.values() if v >= 1),
        "enrich": len(art_of), "outline": len(art_of),
        "write": len(outline.slots), "review": len(drafts),
        "compose": len(reviewed),
    }
    counts_out = {
        "fetch": len(f1), "filter": len(filtered), "score": len(score_of),
        "select": len(art_of), "enrich": sum(1 for a in articles if a.ok),
        "outline": len(outline.slots), "write": len(drafts),
        "review": len(reviewed), "compose": len(manifest.articles),
    }

    fases = []
    start = 0
    for key, label, _fn in FASE_LOGS:
        if key not in reals:
            continue
        actor, kind = ACTORS[key]
        u = usage.get(key) or {}
        log = logs.get(key, {})
        fases.append({
            "id": FASE_IDS[key], "key": key, "label": label,
            "actor": actor, "kind": kind,
            "started_at": timeline[key]["started_at"],
            "real_ms": reals[key], "screen_ms": screens[key],
            "screen_start_ms": start,
            "in": counts_in[key], "out": counts_out[key],
            "model": log.get("model"), "effort": log.get("effort"),
            "calls": u.get("calls"), "spans": u.get("spans"),
            "span_ms": u.get("span_ms"), "spans_labelled": False,
            "sub_events": sub_events.get(key),
        })
        start += screens[key]

    ill_of: dict[int, dict] = {}
    for ill in compose_log.get("illustrations") or []:
        svg = ctx.edition_dir / ill["file"]
        ill_of[ill["pos"]] = {
            "subject": ill["subject"],
            "svg": svg.read_text(encoding="utf-8") if svg.is_file() else None,
        }

    draft_of = {d.pos: d for d in drafts}
    rev_of = {r.pos: r for r in reviewed}
    art_pos = {a.pos: a for a in manifest.articles}
    slots = []
    for s in outline.slots:
        d, rv = draft_of.get(s.pos), rev_of.get(s.pos)
        slots.append({
            "pos": s.pos, "scope": s.scope,
            "onderwerptitel": s.topic,
            "source_ids": s.source_ids,
            "f6": {"invalshoek": s.angle, "lengterichtlijn": s.length,
                   "locatie": s.location, "bron_datum": _iso(s.source_date)},
            "f7": None if d is None else {
                "artikellichaam": d.text, "woorden": d.words, "titel": d.title},
            "f8": None if rv is None else {
                "artikelkop": rv.title, "artikellichaam": rv.text,
                "woorden": rv.words},
            "f9": {"positie": s.pos if s.pos in art_pos else None,
                   "illustratie": ill_of.get(s.pos)},
        })

    onderwerpen = [{
        "index": oi, "scope": c.scope, "onderwerptitel": c.topic,
        "bron_ids": [it.id for it in c.items],
        "pos": next((pos_of[it.id] for it in c.items if it.id in pos_of), None),
    } for oi, c in enumerate(candidates)]

    sources = [{
        "source": f["source"], "bron": f["bron"], "error": f["error"],
        "scopes": scopes_of.get(f["source"], []),
        "entries": f["entries"], "kept": f["kept"],
        "out_of_window": f["out_of_window"], "no_link": f["no_link"],
        "undated": f["undated"],
    } for f in fetch_log["feeds"]]
    _require(all(s["scopes"] for s in sources),
             "a feed in the fetch log has no configured scopes")

    return {
        "meta": {
            "edition": manifest.edition.isoformat(), "nr": manifest.nr,
            "window": {"start": window_start,
                       "days": fetch_log["window_days"],
                       "fetched_at": fetch_log["fetched_at"]},
            "scopes": list(SCOPE_LABELS), "scope_labels": SCOPE_LABELS,
            "speeds": SPEEDS, "default_speed": SPEEDS[0],
            "min_screen_ms": MIN_SCREEN_MS,
            "real_total_ms": sum(reals.values()),
            "screen_total_ms": sum(screens.values()),
            "pages": manifest.counts.get("pages"),
            "words_body": manifest.counts.get("words_body"),
            "weather": manifest.weather.model_dump(mode="json"),
            "counts": {"entries": entries, "in_window": len(f1),
                       "filtered": len(filtered), "scored": len(score_of),
                       "positive": counts_in["select"],
                       "bronnen": len(art_of), "onderwerpen": len(candidates),
                       "slots": len(outline.slots),
                       "articles": len(manifest.articles),
                       "placed_bronnen": len(pos_of)},
        },
        "fases": fases,
        "sources": sources,
        "exits": [{"key": k, "label": EXIT_LABELS[k], "count": v}
                  for k, v in exits.items()],
        "onderwerpen": onderwerpen,
        "slots": slots,
        "nodes": nodes,
    }


def run(ctx: RunContext, out: Path | None = None) -> None:
    trace = build(ctx)
    path = out or (ctx.root / "viz" / "viz-trace.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(trace, indent=1, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    meta = trace["meta"]
    print(f"trace: {path} ({len(trace['nodes'])} nodes, "
          f"{meta['counts']['slots']} slots, "
          f"{meta['screen_total_ms'] / 1000:.0f}s at x1)")
