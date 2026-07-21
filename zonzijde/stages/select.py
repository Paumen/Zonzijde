from __future__ import annotations

import json
from string import Template
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import Candidate, ScoredItem, load_artifact, save_artifact

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "kandidaten": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["L", "R", "N", "I"],
                              "description": "De schaal waartoe dit onderwerp "
                                             "behoort: L (lokaal), R (regionaal), "
                                             "N (nationaal), I (internationaal)."},
                    "topic": {"type": "string",
                              "description": "Een kort label voor het "
                                             "gegroepeerde verhaal."},
                    "items": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string",
                                       "description": "De id van een bronitem "
                                                      "(uit de lijst) dat dit "
                                                      "onderwerp behandelt."},
                            },
                            "required": ["id"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["scope", "topic", "items"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["kandidaten"],
    "additionalProperties": False,
}

JsonCall = Callable[[str, str], object]


def item_line(item: ScoredItem) -> str:
    summary = " ".join(item.summary.split())
    return (f"- id={item.id} | bron={item.bron} | scope={','.join(item.scopes)}"
            f" | bron_titel={item.title} | bron_samenvatting={summary}")


def build_prompt(select_body: str, items: list[ScoredItem]) -> str:
    subs = {"kandidaten": "\n".join(item_line(i) for i in items)}
    return Template(select_body).safe_substitute(subs)


def ground(payload: object, by_id: dict[str, ScoredItem]) -> tuple[list[Candidate], list[str]]:
    raw = payload.get("kandidaten") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return [], ["response is not an object with a kandidaten list"]

    candidates: list[Candidate] = []
    problems: list[str] = []
    for entry in raw:
        try:
            rows = [{"id": row.get("id", ""), "bron": "", "bron_titel": "",
                     "samenvatting": "", "bron_link": ""}
                    for row in entry.get("items", [])]
            cand = Candidate.model_validate({**entry, "items": rows})
        except (ValidationError, AttributeError, TypeError) as e:
            problems.append(f"invalid candidate entry: {e}")
            continue
        for row in cand.items:
            item = by_id.get(row.id)
            if item is None:
                problems.append(f"unknown item id {row.id!r} (topic {cand.topic!r})")
            elif cand.scope not in item.scopes:
                problems.append(f"item {row.id} has scopes {item.scopes}, "
                                f"not {cand.scope} (topic {cand.topic!r})")
            else:
                row.bron, row.bron_link = item.bron, item.link
                row.bron_titel, row.samenvatting = item.title, item.summary
        candidates.append(cand)
    return candidates, problems


def run(ctx: RunContext, call: JsonCall | None = None) -> None:
    cfg = ctx.llm_cfg("select")
    brief = prompts.load_prompt(ctx.root, "brief")
    pipeline = prompts.load_prompt(ctx.root, "pipeline")
    select = prompts.load_prompt(ctx.root, "select")
    system = prompts.system_base(brief.body, pipeline.body)
    usage: list[dict] = []
    if call is None:
        call = lambda prompt, system: llm.agent_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), max_turns=2,
            usage_sink=usage)

    scored = load_artifact(ctx.work_dir / "30-scored.json", ScoredItem)
    positive = [i for i in scored if i.score >= 1]
    if not positive:
        raise SystemExit("S4 select: no +1/+2 items to select from (PIPE-4)")
    by_id = {i.id: i for i in positive}

    prompt = build_prompt(select.body, positive)
    try:
        payload = call(prompt, system)
    except llm.LlmError as e:
        raise SystemExit(f"S4 select: call failed: {e}")
    candidates, problems = ground(payload, by_id)
    if problems:
        raise SystemExit(f"S4 select: invalid selection: {problems}")

    candidates.sort(key=lambda c: ["L", "R", "N", "I"].index(c.scope))
    save_artifact(ctx.work_dir / "40-candidates.json", candidates)
    log = {
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version,
                            "pipeline": pipeline.version,
                            "select": select.version},
        "input_items": len(positive),
        "system": system,
        "prompt": prompt,
        "schema": RESPONSE_SCHEMA,
        "llm": llm.summarize_usage(usage),
    }
    (ctx.work_dir / "40-select-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = sum(len(c.items) for c in candidates)
    print(f"S4 select: {len(positive)} +1/+2 items → {len(candidates)} topics"
          f" ({rows} rows)")
