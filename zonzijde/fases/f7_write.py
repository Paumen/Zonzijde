from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from string import Template
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         load_artifact, load_model, save_artifact)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "artikelkop": {
            "type": "string",
            "description": "De kop precies zoals hij boven het artikel in de "
                           "krant komt te staan. Alleen platte tekst — geen "
                           "label ervoor, geen aanhalingstekens.",
        },
        "artikellichaam": {
            "type": "string",
            "description": "De artikeltekst precies zoals hij onder de kop "
                           "wordt afgedrukt, beginnend bij de eerste zin. "
                           "Herhaal de kop hier niet, zet er geen plaats- of "
                           "datumregel boven (dat wordt apart afgedrukt), en "
                           "voeg geen opmerkingen toe over woordentelling of "
                           "het schrijfproces — alleen de af te drukken "
                           "tekst.",
        },
    },
    "required": ["artikelkop", "artikellichaam"],
    "additionalProperties": False,
}

JsonCall = Callable[[str, str], object]


def word_count(text: str) -> int:
    return len(text.split())


def build_material(slot: OutlineSlot, budget: dict,
                   sources: list[ArticleText]) -> str:
    opdracht = "\n".join([
        "<opdracht>",
        f"- onderwerp (werktitel): {slot.topic}",
        f"- invalshoek: {slot.angle}",
        f"- locatie (dateline): {slot.location}",
        f"- lengte: {slot.length} — als richtlijn {budget['min']}–{budget['max']} "
        "woorden; het verhaal bepaalt, niet het aantal",
        "</opdracht>",
    ])
    parts = [opdracht]
    for art in sources:
        parts.append(f"<bron>\nbron_titel: {art.bron_titel}\nbron: {art.bron}\n\n"
                     f"bron_tekst:\n{art.text}\n</bron>")
    for ref in (r for art in sources for r in art.references if r.ok):
        parts.append(f"<referentie>\nlink: {ref.url}\n\n"
                     f"referentie_tekst:\n{ref.text}\n</referentie>")
    return "\n\n".join(parts)


def build_prompt(write_body: str, slot: OutlineSlot, budget: dict,
                 sources: list[ArticleText]) -> str:
    subs = {"material": build_material(slot, budget, sources)}
    return Template(write_body).safe_substitute(subs)


def ground(payload: object, slot: OutlineSlot) -> tuple[Draft | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = payload.get("artikelkop").strip() \
        if isinstance(payload.get("artikelkop"), str) else ""
    text = payload.get("artikellichaam").strip() \
        if isinstance(payload.get("artikellichaam"), str) else ""
    try:
        draft = Draft(pos=slot.pos, title=title, location=slot.location,
                      source_date=slot.source_date, text=text,
                      words=word_count(text))
    except ValidationError as e:
        return None, [f"invalid draft: {e}"]
    return draft, []


def write_slot(slot: OutlineSlot, articles: dict[str, ArticleText],
               ed_cfg: dict, write_body: str, system: str,
               call: JsonCall) -> tuple[str, Draft | None, list[str]]:
    budget = ed_cfg["woorden"][slot.length]
    sources = [articles[sid] for sid in slot.source_ids if sid in articles]
    prompt = build_prompt(write_body, slot, budget, sources)
    try:
        draft, problems = ground(call(prompt, system), slot)
    except llm.LlmError as e:
        draft, problems = None, [str(e)]
    return prompt, draft, problems


def run(ctx: RunContext, call: JsonCall | None = None) -> None:
    cfg = ctx.llm_cfg("write")
    ed_cfg = ctx.edition_cfg
    fase_cfg = ctx.fase_cfg("write")
    concurrency = int(fase_cfg.get("concurrency", 3))
    brief = prompts.load_prompt(ctx.root, "brief")
    pipeline = prompts.load_prompt(ctx.root, "pipeline")
    stijlgids = prompts.load_prompt(ctx.root, "stijlgids")
    rules = prompts.load_prompt(ctx.root, "write")
    system = prompts.system_base(brief.body, pipeline.body, stijlgids.body)
    usage: list[dict] = []
    if call is None:
        call = lambda prompt, system: llm.agent_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)

    outline = load_model(ctx.work_dir / "f6-outline.json", EditionOutline)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "f5-articles.json", ArticleText)}

    def work(slot: OutlineSlot) -> tuple[str, Draft | None, list[str]]:
        return write_slot(slot, articles, ed_cfg, rules.body, system, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, outline.slots))

    drafts = [d for _, d, _ in results if d is not None]
    failed = [s.pos for s, (_, d, _) in zip(outline.slots, results) if d is None]
    log = {
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version,
                            "pipeline": pipeline.version,
                            "stijlgids": stijlgids.version,
                            "write": rules.version},
        "system": system,
        "schema": RESPONSE_SCHEMA,
        "slots": [{"pos": s.pos, "length": s.length,
                   "words": d.words if d else None, "problems": p,
                   "prompt": prompt}
                  for s, (prompt, d, p) in zip(outline.slots, results)],
        "words_total": sum(d.words for d in drafts),
        "failed_slots": failed,
        "llm": llm.summarize_usage(usage),
    }
    (ctx.work_dir / "f7-write-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(
            f"F7 write: no valid draft for slot(s) {failed} "
            "— see f7-write-log.json")

    drafts.sort(key=lambda d: d.pos)
    save_artifact(ctx.work_dir / "f7-drafts.json", drafts)
    print(f"F7 write: {len(drafts)} articles, {log['words_total']} words "
          f"(ED-5 target {ed_cfg['body_words']['min']}–"
          f"{ed_cfg['body_words']['max']})")
