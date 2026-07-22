from __future__ import annotations

import json
from datetime import date
from string import Template
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Candidate, EditionOutline, ScoredItem,
                         load_artifact, save_model)

RING = ["L", "R", "N", "I"]


def response_schema(candidate_keys: list[str], woorden: dict) -> dict:
    rng = lambda d: f"{d['min']}–{d['max']}"
    lengte_omschrijving = (
        "lang / mid / kort. Richtlijn: "
        f"lang ≈ {rng(woorden['lang'])}, mid ≈ {rng(woorden['mid'])}, "
        f"kort ≈ {rng(woorden['kort'])} woorden — het verhaal bepaalt.")
    return {
        "type": "object",
        "properties": {
            "slots": {
                "type": "array", "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "candidate": {
                            "type": "string", "enum": candidate_keys,
                            "description": "De shortlist-key van het onderwerp "
                                           "voor dit slot (bijv. L1, R2)."},
                        "topic": {
                            "type": "string",
                            "description": "De werktitel — een korte werknaam "
                                           "voor het stuk, voor de opdracht aan "
                                           "de auteur. Niet de gedrukte kop; "
                                           "die bepaalt de auteur."},
                        "length": {
                            "type": "string",
                            "enum": ["lang", "mid", "kort"],
                            "description": lengte_omschrijving},
                        "angle": {
                            "type": "string",
                            "description": "De redactionele invalshoek om "
                                           "vanuit te schrijven; zie de "
                                           "voorbeelden van invalshoeken in "
                                           "de brief."},
                        "location": {
                            "type": "string",
                            "description": "De locatie van de dateline waar "
                                           "het stuk aan verankerd is "
                                           "(plaats, regio of land), "
                                           "afgeleid uit het bronmateriaal."},
                    },
                    "required": ["candidate", "topic", "length",
                                 "angle", "location"],
                    "additionalProperties": False,
                },
            },
        },
        "required": ["slots"],
        "additionalProperties": False,
    }

JsonCall = Callable[[str, str], object]


def constants(cfg: dict) -> dict:
    mix, woorden = cfg["length_mix"], cfg["woorden"]
    rng = lambda d: f"{d['min']}–{d['max']}"
    return {
        "scope_min": cfg["scope_items"]["min"],
        "scope_max": cfg["scope_items"]["max"],
        "mix_lang": rng(mix["lang"]),
        "mix_mid": rng(mix["mid"]),
        "mix_kort": rng(mix["kort"]),
        "woorden_lang": rng(woorden["lang"]),
        "woorden_mid": rng(woorden["mid"]),
        "woorden_kort": rng(woorden["kort"]),
        "body": rng(cfg["body_words"]),
    }


def eligible_candidates(candidates: list[Candidate],
                        articles: dict[str, ArticleText],
                        ) -> list[tuple[str, Candidate]]:
    keyed: list[tuple[str, Candidate]] = []
    counters: dict[str, int] = {}
    for cand in candidates:
        if any(articles[r.id].ok for r in cand.items):
            n = counters.get(cand.scope, 0) + 1
            counters[cand.scope] = n
            keyed.append((f"{cand.scope}{n}", cand))
    return keyed


def first_words(text: str, n: int) -> str:
    return " ".join(text.split(maxsplit=n)[:n])


def story_blocks(keyed: list[tuple[str, Candidate]],
                 articles: dict[str, ArticleText],
                 published: dict[str, date | None]) -> str:
    blocks = []
    for key, cand in keyed:
        lines = [f"## {key} — {cand.topic}"]
        for row in cand.items:
            art = articles[row.id]
            if not art.ok:
                continue
            pub = published.get(row.id)
            tekst = first_words(art.text, 200)
            ok_refs = [r for r in art.references if r.ok]
            ref_words = sum(r.words for r in ok_refs)
            ref_links = ", ".join(r.url for r in ok_refs) or "geen"
            lines.append(f"- bron={row.bron} | published={pub or 'onbekend'}"
                         f" | bron_link={row.bron_link}"
                         f" | bron_titel={row.bron_titel} | bron_tekst={tekst}"
                         f" | source_words={art.words}"
                         f" | referentie_links={ref_links}"
                         f" | referentie_words={ref_words}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def build_prompt(outline_body: str, cfg: dict,
                 keyed: list[tuple[str, Candidate]],
                 articles: dict[str, ArticleText],
                 published: dict[str, date | None]) -> str:
    subs = {**constants(cfg),
            "shortlist": story_blocks(keyed, articles, published)}
    return Template(outline_body).safe_substitute(subs)


def ground(payload: object, edition: date,
           by_key: dict[str, Candidate],
           articles: dict[str, ArticleText],
           published: dict[str, date | None],
           ) -> tuple[EditionOutline | None, list[str]]:
    if not isinstance(payload, dict) or not isinstance(payload.get("slots"), list):
        return None, ["response is not an object with a slots list"]
    raw_slots = [s for s in payload["slots"] if isinstance(s, dict)]

    resolved: list[tuple[dict, Candidate]] = []
    for slot in raw_slots:
        cand = by_key.get(slot.get("candidate"))
        if cand is None:
            return None, [f"unknown candidate {slot.get('candidate')!r}"]
        resolved.append((slot, cand))

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
            "topic": slot.get("topic"), "length": slot.get("length"),
            "angle": slot.get("angle"),
            "source_ids": sids, "location": slot.get("location"),
            "source_date": max(dates) if dates else None,
        })

    try:
        outline = EditionOutline.model_validate({
            "edition": edition, "slots": slots,
        })
    except ValidationError as e:
        return None, [f"invalid outline: {e}"]
    return outline, []


def run(ctx: RunContext, call: JsonCall | None = None) -> None:
    cfg = ctx.llm_cfg("outline")
    ed_cfg = ctx.edition_cfg
    brief = prompts.load_prompt(ctx.root, "brief")
    pipeline = prompts.load_prompt(ctx.root, "pipeline")
    outline_prompt = prompts.load_prompt(ctx.root, "outline")
    system = prompts.system_base(brief.body, pipeline.body)

    candidates = load_artifact(ctx.work_dir / "f4-candidates.json", Candidate)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "f5-articles.json", ArticleText)}
    published = {s.id: s.published.date() if s.published else None
                 for s in load_artifact(ctx.work_dir / "f3-scored.json",
                                        ScoredItem)}
    enrich_log = json.loads(
        (ctx.work_dir / "f5-enrich-log.json").read_text(encoding="utf-8"))
    dropped = enrich_log.get("dropped_topics", [])

    keyed = eligible_candidates(candidates, articles)
    if not keyed:
        raise SystemExit("F6 outline: no candidate has usable source text (PIPE-5)")
    by_key = {key: cand for key, cand in keyed}
    usage: list[dict] = []
    schema = response_schema([key for key, _ in keyed], ed_cfg["woorden"])
    if call is None:
        call = lambda prompt, system: llm.agent_json(
            prompt, system=system, schema=schema,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)

    available: dict[str, int] = {s: 0 for s in RING}
    for _, cand in keyed:
        available[cand.scope] += 1

    prompt = build_prompt(outline_prompt.body, ed_cfg, keyed, articles,
                          published)
    try:
        payload = call(prompt, system)
    except llm.LlmError as e:
        raise SystemExit(f"F6 outline: call failed: {e}")
    outline, problems = ground(payload, ctx.edition, by_key, articles, published)
    if problems:
        raise SystemExit(f"F6 outline: unusable response: {problems}")

    save_model(ctx.work_dir / "f6-outline.json", outline)
    woorden = ed_cfg["woorden"]
    planned = {
        "min": sum(woorden[s.length]["min"] for s in outline.slots),
        "max": sum(woorden[s.length]["max"] for s in outline.slots),
    }
    log = {
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version,
                            "pipeline": pipeline.version,
                            "outline": outline_prompt.version},
        "input_topics": {s: available[s] for s in RING},
        "dropped_topics": dropped,
        "planned_words": planned,
        "system": system,
        "prompt": prompt,
        "schema": schema,
        "llm": llm.summarize_usage(usage),
    }
    (ctx.work_dir / "f6-outline-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    mix = {cls: sum(1 for s in outline.slots if s.length == cls)
           for cls in ("lang", "mid", "kort")}
    print(f"F6 outline: {len(outline.slots)} slots "
          f"({mix['lang']} lang, {mix['mid']} mid, {mix['kort']} "
          f"kort; planned {planned['min']}–{planned['max']} words)")
