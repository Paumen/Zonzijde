from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from string import Template
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (Draft, EditionOutline, OutlineSlot, Review,
                         ReviewedArticle, load_artifact, load_model,
                         save_artifact)
from .write import word_count

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "artikelkop": {
            "type": "string",
            "description": "De kop precies zoals hij boven het artikel in de "
                           "krant komt te staan. Alleen platte tekst — geen "
                           "label ervoor (zoals 'Titel:' of 'Copy-edit:'), "
                           "geen verwijzing naar het slotnummer of naar het "
                           "redactieproces.",
        },
        "artikellichaam": {
            "type": "string",
            "description": "De artikeltekst precies zoals hij onder de kop "
                           "wordt afgedrukt, beginnend bij de eerste zin. "
                           "Herhaal de kop hier niet, zet er geen plaats- of "
                           "datumregel boven (dat wordt apart afgedrukt), en "
                           "voeg geen opmerkingen toe over woordentelling of "
                           "correcties — dat hoort alleen in 'corrections' "
                           "thuis.",
        },
        "corrections": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["artikelkop", "artikellichaam", "corrections"],
    "additionalProperties": False,
}

JsonCall = Callable[[str, str], object]


def build_prompt(review_body: str, draft: Draft, slot: OutlineSlot,
                 budget: dict) -> str:
    draft_block = "\n".join([
        f"<concept slot={draft.pos} lengte={slot.length} "
        f"richtlijn={budget['min']}–{budget['max']}>",
        f"werktitel: {draft.title}",
        "",
        f"artikel_concept:\n{draft.text}",
        "</concept>",
    ])
    return Template(review_body).safe_substitute({"draft": draft_block})


def ground(payload: object, draft: Draft) -> tuple[ReviewedArticle | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = payload.get("artikelkop").strip() \
        if isinstance(payload.get("artikelkop"), str) else ""
    text = payload.get("artikellichaam").strip() \
        if isinstance(payload.get("artikellichaam"), str) else ""

    raw = payload.get("corrections")
    corrections = [s.strip() for s in raw if isinstance(s, str) and s.strip()] \
        if isinstance(raw, list) else []

    try:
        reviewed = ReviewedArticle(
            pos=draft.pos, title=title, location=draft.location,
            source_date=draft.source_date, text=text,
            words=word_count(text),
            review=Review(corrections=corrections))
    except ValidationError as e:
        return None, [f"invalid reviewed article: {e}"]
    return reviewed, []


def review_draft(draft: Draft, slot: OutlineSlot, ed_cfg: dict,
                 review_body: str, system: str, call: JsonCall
                 ) -> tuple[str, ReviewedArticle | None, list[str]]:
    budget = ed_cfg["woorden"][slot.length]
    prompt = build_prompt(review_body, draft, slot, budget)
    try:
        reviewed, problems = ground(call(prompt, system), draft)
    except llm.LlmError as e:
        reviewed, problems = None, [str(e)]
    return prompt, reviewed, problems


def run(ctx: RunContext, call: JsonCall | None = None) -> None:
    cfg = ctx.llm_cfg("review")
    ed_cfg = ctx.edition_cfg
    stage_cfg = ctx.stage_cfg("review")
    concurrency = int(stage_cfg.get("concurrency", 3))
    brief = prompts.load_prompt(ctx.root, "brief")
    pipeline = prompts.load_prompt(ctx.root, "pipeline")
    rules = prompts.load_prompt(ctx.root, "review")
    system = prompts.system_base(brief.body, pipeline.body)
    usage: list[dict] = []
    if call is None:
        call = lambda prompt, system: llm.agent_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)

    drafts = load_artifact(ctx.work_dir / "70-drafts.json", Draft)
    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    slots = {s.pos: s for s in outline.slots}
    missing = [d.pos for d in drafts if d.pos not in slots]
    if missing:
        raise SystemExit(f"S8 review: draft slot(s) {missing} not in the "
                         "outline — artifacts out of step, re-run S6/S7")

    def work(draft: Draft) -> tuple[str, ReviewedArticle | None, list[str]]:
        return review_draft(draft, slots[draft.pos], ed_cfg, rules.body,
                            system, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, drafts))

    reviewed = [r for _, r, _ in results if r is not None]
    failed = [d.pos for d, (_, r, _) in zip(drafts, results) if r is None]
    log = {
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version,
                            "pipeline": pipeline.version,
                            "review": rules.version},
        "system": system,
        "schema": RESPONSE_SCHEMA,
        "articles": [{"pos": d.pos,
                      "words": {"draft": d.words,
                                "reviewed": r.words if r else None},
                      "corrections": r.review.corrections if r else [],
                      "problems": p, "prompt": prompt}
                     for d, (prompt, r, p) in zip(drafts, results)],
        "words_total": sum(r.words for r in reviewed),
        "failed_slots": failed,
        "llm": llm.summarize_usage(usage),
    }
    (ctx.work_dir / "80-review-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(
            f"S8 review: no valid review for slot(s) {failed} "
            "— see 80-review-log.json")

    reviewed.sort(key=lambda r: r.pos)
    save_artifact(ctx.work_dir / "80-reviewed.json", reviewed)
    corrections = sum(len(r.review.corrections) for r in reviewed)
    print(f"S8 review: {len(reviewed)} articles, "
          f"{corrections} correction(s), {log['words_total']} words")
