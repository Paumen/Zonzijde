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
schema-enforced at the call layer, and the model's editorial choices — how
many per scope (ED-1), the length mix (ED-2), which sources — are taken as-is
and judged at the human gate, not validated here. Code still assembles what
it owns: ring order and the lokaal front (ED-6) by a stable sort, and
``pos``/``role``/``source_date`` (ED-3, newest source). One call, no retry:
only a call failure or a structurally unusable response fails the run (§6).
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
           published: dict[str, date | None],
           ) -> tuple[EditionOutline | None, list[str]]:
    """Build the edition plan from the model's response — no validation of
    its editorial choices (counts, mix, which sources). Code still assembles
    what it owns: ring order (ED-6), ``pos``/``role``, ``source_date`` (newest
    source, ED-3) and the illustration slot. Only the pydantic contract is
    left as a structural backstop."""
    if not isinstance(payload, dict) or not isinstance(payload.get("slots"), list):
        return None, ["response is not an object with a slots list"]
    raw_slots = [s for s in payload["slots"] if isinstance(s, dict)]

    # Ring order (ED-6): stable sort by scope keeps the model's order within
    # each scope, so its first lokaal pick leads. Unknown scope sorts last.
    def scope_key(i: int) -> int:
        sc = raw_slots[i].get("scope")
        return RING.index(sc) if sc in RING else len(RING)
    order = sorted(range(len(raw_slots)), key=scope_key)
    pos_of_index = {i: pos for pos, i in enumerate(order, start=1)}

    slots = []
    for i in order:
        slot = raw_slots[i]
        sids = slot.get("source_ids") or []
        dates = [published.get(sid) for sid in sids if published.get(sid)]
        slots.append({**slot, "pos": pos_of_index[i],
                      "role": "front-hero" if pos_of_index[i] == 1 else "body",
                      "source_date": max(dates) if dates else None})

    ill = payload.get("illustration") if isinstance(payload.get("illustration"), dict) else {}
    idx = ill.get("slot_index")
    slot_pos = (pos_of_index[idx - 1] if isinstance(idx, int)
                and 1 <= idx <= len(raw_slots) else 1)
    subject = ill.get("subject").strip() if isinstance(ill.get("subject"), str) else ""

    try:
        outline = EditionOutline.model_validate({
            "edition": edition, "slots": slots,
            "illustration": {"slot_pos": slot_pos, "subject": subject},
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

    # How many topics survived S5 per scope — informational for the log; no
    # longer a gate (ED-1 counts are the model's call, judged at the gate).
    available: dict[str, int] = {s: 0 for s in RING}
    for cand in candidates:
        if any(articles[r.id].ok for r in cand.items):
            available[cand.scope] += 1

    prompt = build_prompt(outline_prompt.body, ed_cfg, candidates, articles,
                          published, dropped)
    try:
        payload = call(prompt, brief.body)
    except llm.LlmError as e:
        raise SystemExit(f"S6 outline: call failed: {e}")
    outline, problems = ground(payload, ctx.edition, ed_cfg, articles, published)
    if problems:  # only a structural/contract break reaches here now
        raise SystemExit(f"S6 outline: unusable response: {problems}")

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
