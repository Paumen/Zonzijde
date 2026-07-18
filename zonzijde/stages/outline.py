"""S6 outline (PIPE-6): a frontier LLM plans the edition — a quick pitch.

This is the Monday-morning pitch meeting: the model gets the shortlist and
gives rough direction, fast. No web browsing, no full texts — just titles and
RSS summaries. One plain prompt-in/JSON-out call, no tools. The full source
texts belong to the writers (S7).

Reads ``40-candidates.json`` (the shortlist), ``50-articles.json`` (only the
``ok`` flag per row — which topics have usable text, never the text itself
here), ``50-enrich-log.json`` (the drop log, so scope counts can rebalance)
and ``30-scored.json`` (published dates for ED-3). Writes ``60-outline.json``
and ``60-outline-log.json``.

The call sends ``prompts/brief.md`` (system) + ``prompts/outline.md`` + the
edition constants (SPEC §5, from config) + the shortlist. The response is
schema-enforced at the call layer and grounded here: every slot must build on
``ok`` article ids of matching scope, scope counts and length mix must satisfy
ED-1/ED-2, ring order and the lokaal front are enforced by construction
(ED-6), and ``pos``/``role``/``source_date`` are assigned in code — never
taken from the model. One call, no retry: a call failure or an invalid plan
fails the run (§6).

ED-1 is not relaxed: a scope that cannot contribute its minimum after the
S5 drops fails the run up front — the spec's answer to a thin harvest is
widening the candidate window (SRC-4), a human decision, not a quietly
thinner edition.
"""

from __future__ import annotations

import json
from datetime import date
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Candidate, EditionOutline, ScoredItem,
                         load_artifact, save_model)

RING = ["L", "R", "N", "I"]
SCOPE_NAMES = {"L": "lokaal", "R": "regionaal", "N": "nationaal",
               "I": "internationaal"}

# JSON schema for the structured-output call. pos/role/source_date/edition
# are deliberately absent: code derives them (see module docstring).
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "slots": {
            "type": "array", "minItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": RING},
                    "topic": {"type": "string"},
                    "length": {"type": "string",
                               "enum": ["long", "standard", "short"]},
                    "type": {"type": "string",
                             "enum": ["news", "feature", "profile",
                                      "zoom-out", "zoom-in"]},
                    "angle": {"type": "string"},
                    "devices": {"type": "array", "items": {"type": "string"}},
                    "source_ids": {"type": "array", "minItems": 1,
                                   "items": {"type": "string"}},
                    "location": {"type": "string"},
                },
                "required": ["scope", "topic", "length", "type", "angle",
                             "devices", "source_ids", "location"],
                "additionalProperties": False,
            },
        },
        "illustration": {
            "type": "object",
            "properties": {
                "slot_index": {"type": "integer", "minimum": 1},
                "subject": {"type": "string"},
            },
            "required": ["slot_index", "subject"],
            "additionalProperties": False,
        },
        "optional_element": {
            "type": "object",
            "properties": {
                "kind": {"type": "string",
                         "enum": ["quote", "number", "side-story", "none"]},
                "content": {"type": "string"},
            },
            "required": ["kind", "content"],
            "additionalProperties": False,
        },
    },
    "required": ["slots", "illustration", "optional_element"],
    "additionalProperties": False,
}

# The output-shape half of the instruction (editorial wording stays in
# prompts/outline.md — same split as S4's SHAPE_NOTE).
SHAPE_NOTE = (
    "Answer as JSON per the given schema: slots in reading order (the slots "
    "are re-sorted into strict ring order afterwards, so order within a scope "
    "is what you control), each with the exact source id(s) from the story "
    "blocks below — only ids marked ok are usable. illustration.slot_index "
    "is the 1-based index into your own slots array. Give optional_element "
    "kind 'none' with empty content if the edition carries none.")

# call(prompt, system) -> parsed JSON; injectable for tests.
FrontierCall = Callable[[str, str], object]


def spec_note(cfg: dict) -> str:
    """The SPEC §5 constants rendered for the prompt, so the plan and the
    grounding checks share one source of truth (config/edition.yaml)."""
    mix = cfg["length_mix"]
    words = cfg["words"]
    scope = cfg["scope_items"]
    body = cfg["body_words"]
    lines = [
        "Edition constants (SPEC §5):",
        f"- Each scope contributes {scope['min']}–{scope['max']} items (ED-1).",
        "- Length mix (ED-2): "
        + ", ".join(f"{mix[c]['min']}–{mix[c]['max']} {c}" for c in
                    ("long", "standard", "short"))
        + " — word guidance (loose, the story decides): "
        + ", ".join(f"{c} {words[c]['min']}–{words[c]['max']}" for c in
                    ("long", "standard", "short")) + ".",
        f"- Edition body total ≈ {body['min']}–{body['max']} words (ED-5).",
        "- Ring order lokaal → regionaal → nationaal → internationaal is "
        "strict; the front page leads with the best lokaal story (ED-6).",
    ]
    return "\n".join(lines)


def story_blocks(candidates: list[Candidate], articles: dict[str, ArticleText],
                 published: dict[str, date | None]) -> str:
    """The shortlist: each candidate topic with its rows as titel + RSS
    samenvatting (not the full text — this is the pitch, the writers get the
    texts). ``ok=false`` rows had no full text in S5, so a slot must not be
    built on them (PIPE-5)."""
    blocks = []
    for cand in candidates:
        lines = [f"## {cand.scope}{cand.rank} — {cand.topic}"]
        for row in cand.items:
            art = articles[row.id]
            pub = published.get(row.id)
            summary = " ".join(row.samenvatting.split())
            lines.append(f"- id={row.id} | ok={str(art.ok).lower()} | "
                         f"bron={row.bron} | published={pub or 'unknown'} | "
                         f"titel={row.titel} | samenvatting={summary}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_prompt(outline_body: str, cfg: dict, candidates: list[Candidate],
                 articles: dict[str, ArticleText],
                 published: dict[str, date | None],
                 dropped: list[str]) -> str:
    parts = [outline_body, SHAPE_NOTE, spec_note(cfg)]
    if dropped:
        parts.append("Topics dropped in enrichment (no full text — rebalance "
                     "around them):\n"
                     + "\n".join(f"- {t}" for t in dropped))
    parts.append("Shortlist:\n\n"
                 + story_blocks(candidates, articles, published))
    return "\n\n".join(parts)


def ground(payload: object, edition: date, cfg: dict,
           articles: dict[str, ArticleText],
           scopes_by_id: dict[str, set[str]],
           published: dict[str, date | None],
           ) -> tuple[EditionOutline | None, list[str]]:
    """Validate the plan against the contract, the source articles and the
    ED-1/ED-2 constants. Returns the grounded outline (slots re-sorted into
    ring order, pos/role/source_date assigned) or the list of problems."""
    if not isinstance(payload, dict) or not isinstance(payload.get("slots"), list):
        return None, ["response is not an object with a slots list"]

    problems: list[str] = []
    raw_slots = payload["slots"]
    used_ids: set[str] = set()
    for k, slot in enumerate(raw_slots, start=1):
        if not isinstance(slot, dict):
            problems.append(f"slot {k}: not an object")
            continue
        if slot.get("scope") not in RING:
            problems.append(f"slot {k}: invalid scope {slot.get('scope')!r}")
            continue
        sids = slot.get("source_ids")
        if not isinstance(sids, list) or not sids:
            # Recorded as a problem here so the later slot-construction pass
            # (which runs only problem-free) can index source_ids safely.
            problems.append(f"slot {k}: missing source_ids")
            continue
        for sid in sids:
            art = articles.get(sid)
            if art is None:
                problems.append(f"slot {k}: unknown source id {sid!r}")
            elif not art.ok:
                problems.append(f"slot {k}: source {sid} has no full text "
                                "(PIPE-5 — not writing material)")
            elif slot.get("scope") not in scopes_by_id.get(sid, set()):
                problems.append(f"slot {k}: source {sid} does not back a "
                                f"{slot.get('scope')} topic")
            if sid in used_ids:
                problems.append(f"source {sid} used by more than one slot")
            used_ids.add(sid)

    # ED-1: per-scope counts, as specified — run() already verified the
    # surviving topics can satisfy the minimum.
    scope_cfg = cfg["scope_items"]
    counts = {s: sum(1 for slot in raw_slots
                     if isinstance(slot, dict) and slot.get("scope") == s)
              for s in RING}
    for s in RING:
        if counts[s] < scope_cfg["min"]:
            problems.append(f"scope {SCOPE_NAMES[s]}: {counts[s]} items, "
                            f"needs at least {scope_cfg['min']} (ED-1)")
        if counts[s] > scope_cfg["max"]:
            problems.append(f"scope {SCOPE_NAMES[s]}: {counts[s]} items, "
                            f"at most {scope_cfg['max']} (ED-1)")

    # ED-2: length mix.
    for cls, rng in cfg["length_mix"].items():
        n = sum(1 for slot in raw_slots
                if isinstance(slot, dict) and slot.get("length") == cls)
        if not rng["min"] <= n <= rng["max"]:
            problems.append(f"{n} {cls} articles, needs "
                            f"{rng['min']}–{rng['max']} (ED-2)")

    if counts["L"] == 0:
        problems.append("no lokaal slot — the front page leads lokaal (ED-6)")
    if problems:
        return None, problems

    # Ring order by construction (ED-6): stable sort keeps the model's order
    # within each scope, so its first lokaal pick stays the front hero.
    order = sorted(range(len(raw_slots)),
                   key=lambda i: RING.index(raw_slots[i]["scope"]))
    pos_of_index = {i: pos for pos, i in enumerate(order, start=1)}

    slots = []
    for i in order:
        slot = raw_slots[i]
        pos = pos_of_index[i]
        dates = [published.get(sid) for sid in slot["source_ids"]]
        dates = [d for d in dates if d is not None]
        try:
            slots.append({**slot, "pos": pos,
                          "role": "front-hero" if pos == 1 else "body",
                          "source_date": max(dates) if dates else None})
        except (TypeError, AttributeError) as e:
            problems.append(f"slot {i + 1}: {e}")

    ill = payload.get("illustration") or {}
    idx = ill.get("slot_index") if isinstance(ill, dict) else None
    if not isinstance(idx, int) or not 1 <= idx <= len(raw_slots):
        problems.append(f"illustration.slot_index {idx!r} does not point at "
                        "a slot")
    elif not (isinstance(ill.get("subject"), str) and ill["subject"].strip()):
        problems.append("illustration needs a concrete subject (EL-3)")
    if problems:
        return None, problems

    try:
        outline = EditionOutline.model_validate({
            "edition": edition, "slots": slots,
            "illustration": {"slot_pos": pos_of_index[idx - 1],
                             "subject": ill["subject"].strip()},
            "optional_element": payload.get("optional_element"),
        })
    except ValidationError as e:
        return None, [f"invalid outline: {e}"]
    return outline, []


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    brief = prompts.load_prompt(ctx.root, "brief")
    outline_prompt = prompts.load_prompt(ctx.root, "outline")
    if call is None:
        # Plain prompt-in/JSON-out, no tools: the outline is a quick pitch
        # from the shortlist, not a research session.
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    candidates = load_artifact(ctx.work_dir / "40-candidates.json", Candidate)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}
    published = {s.id: s.published.date() if s.published else None
                 for s in load_artifact(ctx.work_dir / "30-scored.json",
                                        ScoredItem)}
    enrich_log = json.loads(
        (ctx.work_dir / "50-enrich-log.json").read_text(encoding="utf-8"))
    dropped = enrich_log.get("dropped_topics", [])

    # Which candidate topics survived S5 per scope, and which scopes each ok
    # id may back.
    scopes_by_id: dict[str, set[str]] = {}
    available: dict[str, int] = {s: 0 for s in RING}
    for cand in candidates:
        if any(articles[r.id].ok for r in cand.items):
            available[cand.scope] += 1
        for row in cand.items:
            scopes_by_id.setdefault(row.id, set()).add(cand.scope)
    if not any(available.values()):
        raise SystemExit("S6 outline: no topic survived enrichment (PIPE-5)")

    # ED-1 is not relaxed. A scope that cannot reach its minimum after the S5
    # drops fails the run here — the spec's remedy for a thin harvest is
    # widening the candidate window (SRC-4, --window-days), a human call, not
    # a quietly thinner edition.
    need = ed_cfg["scope_items"]["min"]
    short = {SCOPE_NAMES[s]: available[s] for s in RING if available[s] < need}
    if short:
        raise SystemExit(
            f"S6 outline: scope(s) below the ED-1 minimum of {need} after S5 "
            f"drops: {short}. Widen the window (SRC-4, --window-days) and "
            "re-run from S1, or adjust config — the edition is not thinned "
            "automatically.")

    prompt = build_prompt(outline_prompt.body, ed_cfg, candidates, articles,
                          published, dropped)
    try:
        payload = call(prompt, brief.body)
    except llm.LlmError as e:
        raise SystemExit(f"S6 outline: call failed: {e}")
    outline, problems = ground(payload, ctx.edition, ed_cfg, articles,
                               scopes_by_id, published)
    if problems:
        raise SystemExit(f"S6 outline: invalid edition plan: {problems}")

    save_model(ctx.work_dir / "60-outline.json", outline)
    words = ed_cfg["words"]
    planned = {
        "min": sum(words[s.length]["min"] for s in outline.slots),
        "max": sum(words[s.length]["max"] for s in outline.slots),
    }
    log = {
        "model": cfg["model"],
        "prompt_versions": {"brief": brief.version,
                            "outline": outline_prompt.version},
        "input_topics": {s: available[s] for s in RING},
        "dropped_topics": dropped,
        "planned_words": planned,
    }
    (ctx.work_dir / "60-outline-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    mix = {cls: sum(1 for s in outline.slots if s.length == cls)
           for cls in ("long", "standard", "short")}
    print(f"S6 outline: {len(outline.slots)} slots "
          f"({mix['long']} long, {mix['standard']} standard, {mix['short']} "
          f"short; planned {planned['min']}–{planned['max']} words)")
