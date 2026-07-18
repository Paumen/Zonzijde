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


def response_schema(candidate_keys: list[str]) -> dict:
    """The structured-output schema for one run. Each slot names the
    ``candidate`` it is built from (constrained to the shortlist keys, so the
    pick is always resolvable); scope/source_ids/source_date/pos/role/edition
    are absent because code derives them (see module docstring)."""
    return {
        "type": "object",
        "properties": {
            "slots": {
                "type": "array", "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate": {"type": "string", "enum": candidate_keys},
                        "topic": {"type": "string"},
                        "length": {"type": "string",
                                   "enum": ["long", "standard", "short"]},
                        "type": {"type": "string",
                                 "enum": ["news", "feature", "profile",
                                          "zoom-out", "zoom-in"]},
                        "devices": {"type": "array",
                                    "items": {"type": "string"}},
                        "location": {"type": "string"},
                    },
                    "required": ["candidate", "topic", "length", "type",
                                 "devices", "location"],
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
        },
        "required": ["slots", "illustration"],
        "additionalProperties": False,
    }

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


def eligible_candidates(candidates: list[Candidate],
                        articles: dict[str, ArticleText],
                        ) -> list[tuple[str, Candidate]]:
    """The shortlist the model may pick from: candidates with at least one ok
    source (PIPE-5), each given a stable ``scope+index`` key (L1, L2, R1…) in
    the candidates' file order. The key is what the model references and how
    code re-attaches the topic's sources."""
    keyed: list[tuple[str, Candidate]] = []
    counters: dict[str, int] = {}
    for cand in candidates:
        if any(articles[r.id].ok for r in cand.items):
            n = counters.get(cand.scope, 0) + 1
            counters[cand.scope] = n
            keyed.append((f"{cand.scope}{n}", cand))
    return keyed


def story_blocks(keyed: list[tuple[str, Candidate]],
                 articles: dict[str, ArticleText],
                 published: dict[str, date | None]) -> str:
    """Each shortlisted topic under its key, with its usable source rows as
    titel + RSS samenvatting (not the full text — this is the pitch, the
    writers get the texts)."""
    blocks = []
    for key, cand in keyed:
        lines = [f"## {key} — {cand.topic}"]
        for row in cand.items:
            if not articles[row.id].ok:
                continue
            pub = published.get(row.id)
            summary = " ".join(row.samenvatting.split())
            lines.append(f"- bron={row.bron} | published={pub or 'unknown'} | "
                         f"titel={row.titel} | samenvatting={summary}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_prompt(outline_body: str, cfg: dict,
                 keyed: list[tuple[str, Candidate]],
                 articles: dict[str, ArticleText],
                 published: dict[str, date | None],
                 dropped: list[str]) -> str:
    parts = [outline_body, spec_note(cfg)]
    if dropped:
        parts.append("Topics dropped in enrichment (no full text — rebalance "
                     "around them):\n"
                     + "\n".join(f"- {t}" for t in dropped))
    parts.append("Shortlist:\n\n"
                 + story_blocks(keyed, articles, published))
    return "\n\n".join(parts)


def ground(payload: object, edition: date,
           by_key: dict[str, Candidate],
           articles: dict[str, ArticleText],
           published: dict[str, date | None],
           ) -> tuple[EditionOutline | None, list[str]]:
    """Build the edition plan from the model's response — no validation of its
    editorial choices (counts, mix, which topics). Code assembles what it owns
    from the picked candidate: ``scope``, ``source_ids`` (its ok rows) and
    ``source_date`` (newest, ED-3), plus ring order (ED-6), ``pos``/``role``
    and the illustration slot. Only the pydantic contract is a structural
    backstop."""
    if not isinstance(payload, dict) or not isinstance(payload.get("slots"), list):
        return None, ["response is not an object with a slots list"]
    raw_slots = [s for s in payload["slots"] if isinstance(s, dict)]

    resolved: list[tuple[dict, Candidate]] = []
    for slot in raw_slots:
        cand = by_key.get(slot.get("candidate"))
        if cand is None:
            return None, [f"unknown candidate {slot.get('candidate')!r}"]
        resolved.append((slot, cand))

    # Ring order (ED-6): stable sort by the candidate's scope keeps the model's
    # order within each scope, so its first lokaal pick leads.
    order = sorted(range(len(resolved)),
                   key=lambda i: RING.index(resolved[i][1].scope))
    pos_of_index = {i: pos for pos, i in enumerate(order, start=1)}

    slots = []
    for i in order:
        slot, cand = resolved[i]
        sids = [r.id for r in cand.items if articles[r.id].ok]
        dates = [published.get(sid) for sid in sids if published.get(sid)]
        slots.append({
            "pos": pos_of_index[i], "scope": cand.scope,
            "role": "front-hero" if pos_of_index[i] == 1 else "body",
            "topic": slot.get("topic"), "length": slot.get("length"),
            "type": slot.get("type"), "devices": slot.get("devices"),
            "source_ids": sids, "location": slot.get("location"),
            "source_date": max(dates) if dates else None,
        })

    ill = payload.get("illustration") if isinstance(payload.get("illustration"), dict) else {}
    idx = ill.get("slot_index")
    slot_pos = (pos_of_index[idx - 1] if isinstance(idx, int)
                and 1 <= idx <= len(resolved) else 1)
    subject = ill.get("subject").strip() if isinstance(ill.get("subject"), str) else ""

    try:
        outline = EditionOutline.model_validate({
            "edition": edition, "slots": slots,
            "illustration": {"slot_pos": slot_pos, "subject": subject},
        })
    except ValidationError as e:
        return None, [f"invalid outline: {e}"]
    return outline, []


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    brief = prompts.load_prompt(ctx.root, "brief")
    outline_prompt = prompts.load_prompt(ctx.root, "outline")

    candidates = load_artifact(ctx.work_dir / "40-candidates.json", Candidate)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}
    published = {s.id: s.published.date() if s.published else None
                 for s in load_artifact(ctx.work_dir / "30-scored.json",
                                        ScoredItem)}
    enrich_log = json.loads(
        (ctx.work_dir / "50-enrich-log.json").read_text(encoding="utf-8"))
    dropped = enrich_log.get("dropped_topics", [])

    keyed = eligible_candidates(candidates, articles)
    if not keyed:
        raise SystemExit("S6 outline: no candidate has usable source text (PIPE-5)")
    by_key = {key: cand for key, cand in keyed}
    if call is None:
        # Plain prompt-in/JSON-out, no tools: the outline is a quick pitch
        # from the shortlist, not a research session.
        schema = response_schema([key for key, _ in keyed])
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=schema,
            model=cfg["model"], effort=cfg.get("effort"))

    # How many topics survived S5 per scope — informational for the log; no
    # longer a gate (ED-1 counts are the model's call, judged at the gate).
    available: dict[str, int] = {s: 0 for s in RING}
    for _, cand in keyed:
        available[cand.scope] += 1

    prompt = build_prompt(outline_prompt.body, ed_cfg, keyed, articles,
                          published, dropped)
    try:
        payload = call(prompt, brief.body)
    except llm.LlmError as e:
        raise SystemExit(f"S6 outline: call failed: {e}")
    outline, problems = ground(payload, ctx.edition, by_key, articles, published)
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
