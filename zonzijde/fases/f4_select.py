from __future__ import annotations

import json
from string import Template
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import RING, Candidate, ScoredItem, load_artifact, save_artifact

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "onderwerpen": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "schaal": {"type": "string", "enum": RING,
                               "description": "De schaal waartoe dit onderwerp "
                                              "behoort: L (lokaal), R (regionaal), "
                                              "N (nationaal), I (internationaal)."},
                    "onderwerptitel": {
                        "type": "string",
                        "description": "De onderwerptitel: een korte "
                                       "naam voor het gegroepeerde "
                                       "verhaal, niet de artikelkop."},
                    "bronnen": {
                        "type": "array", "minItems": 1,
                        "items": {"type": "string",
                                  "description": "De id van een item "
                                                 "(uit de lijst) dat dit "
                                                 "onderwerp behandelt."},
                    },
                },
                "required": ["schaal", "onderwerptitel", "bronnen"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["onderwerpen"],
    "additionalProperties": False,
}

JsonCall = Callable[[str, str], object]


def item_line(item: ScoredItem) -> str:
    summary = " ".join(item.summary.split())
    return (f"- id={item.id} | medium={item.bron} | schaal={','.join(item.scopes)}"
            f" | bron_titel={item.title} | bron_samenvatting={summary}")


def build_prompt(select_body: str, items: list[ScoredItem],
                 ed_cfg: dict) -> str:
    counts = ed_cfg["onderwerpen"]
    subs = {"items": "\n".join(item_line(i) for i in items),
            **{f"onderwerpen_{s}": counts[s] for s in RING}}
    return Template(select_body).safe_substitute(subs)


def ground(payload: object, by_id: dict[str, ScoredItem]) -> tuple[list[Candidate], list[str]]:
    raw = payload.get("onderwerpen") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return [], ["response is not an object with an onderwerpen list"]

    candidates: list[Candidate] = []
    problems: list[str] = []
    for entry in raw:
        try:
            rows = [{"id": item_id, "bron": "", "bron_titel": "",
                     "samenvatting": "", "bron_link": ""}
                    for item_id in entry.get("bronnen", [])]
            cand = Candidate.model_validate({
                "scope": entry.get("schaal"),
                "topic": entry.get("onderwerptitel"),
                "items": rows})
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
            model=cfg["model"], effort=cfg.get("effort"),
            max_turns=cfg["max_turns"], usage_sink=usage)

    scored = load_artifact(ctx.work_dir / "f3-scored.json", ScoredItem)
    positive = [i for i in scored if i.score >= 1]
    if not positive:
        raise SystemExit("F4 select: no +1/+2 items to select from (PIPE-4)")
    by_id = {i.id: i for i in positive}

    prompt = build_prompt(select.body, positive, ctx.edition_cfg)
    log = {
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version,
                            "pipeline": pipeline.version,
                            "select": select.version},
        "input_items": len(positive),
        "system": system,
        "prompt": prompt,
        "schema": RESPONSE_SCHEMA,
    }
    log_path = ctx.work_dir / "f4-select-log.json"

    def write_log(**extra: object) -> None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(
            json.dumps({**log, **extra, "llm": llm.summarize_usage(usage)},
                       indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    try:
        payload = call(prompt, system)
    except llm.LlmError as e:
        write_log(error=str(e))
        raise SystemExit(f"F4 select: call failed: {e} — see {log_path.name}")
    candidates, problems = ground(payload, by_id)
    if problems:
        write_log(response=payload, problems=problems)
        raise SystemExit(f"F4 select: invalid selection: {problems} "
                         f"— see {log_path.name}")

    candidates.sort(key=lambda c: RING.index(c.scope))
    save_artifact(ctx.work_dir / "f4-candidates.json", candidates)
    write_log()

    rows = sum(len(c.items) for c in candidates)
    print(f"F4 select: {len(positive)} +1/+2 items → {len(candidates)} onderwerpen"
          f" ({rows} bronnen)")
