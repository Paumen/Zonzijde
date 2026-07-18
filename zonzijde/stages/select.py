"""S4 select (PIPE-4): a frontier LLM picks the top-5 topics per scope.

Reads ``30-scored.json`` (only +1/+2 items advance), writes
``40-candidates.json`` and ``40-select-log.json``. The call sends
``prompts/brief.md`` (as system prompt) + ``prompts/select.md`` + the scored
titles/summaries; the response is schema-enforced at the call layer and then
grounded here: every row must reference an input item by id, with a scope
that item actually carries. Retries with backoff, fatal after 3 (§6).
"""

from __future__ import annotations

import json
import time
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import Candidate, ScoredItem, load_artifact, save_artifact

MAX_ATTEMPTS = 3
BACKOFF_S = 2.0

# JSON schema for the structured-output call; mirrors the Candidate contract.
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "candidates": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "scope": {"type": "string", "enum": ["L", "R", "N", "I"]},
                    "rank": {"type": "integer", "minimum": 1, "maximum": 5},
                    "topic": {"type": "string"},
                    "items": {
                        "type": "array", "minItems": 1,
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "titel": {"type": "string"},
                                "samenvatting": {"type": "string"},
                            },
                            "required": ["id", "titel", "samenvatting"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["scope", "rank", "topic", "items"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["candidates"],
    "additionalProperties": False,
}

# The output-shape half of the instruction. The editorial wording stays in
# prompts/select.md verbatim; this only maps its "table" onto the artifact.
SHAPE_NOTE = (
    "Antwoord als JSON volgens het opgegeven schema: één candidates-lijst, "
    "per topic één object met scope, rank (1–5 per scope), topic en items — "
    "één item per bronartikel, met het exacte id uit de lijst hieronder. "
    "titel en samenvatting mag je redigeren; bron en link volgen uit het id."
)

# call(prompt, system) -> parsed JSON; injectable for tests.
FrontierCall = Callable[[str, str], object]


def item_line(item: ScoredItem) -> str:
    summary = " ".join(item.summary.split())
    return (f"- id={item.id} | bron={item.bron} | scope={','.join(item.scopes)}"
            f" | score=+{item.score} | titel={item.title}"
            f" | samenvatting={summary} | link={item.link}")


def build_prompt(select_body: str, items: list[ScoredItem]) -> str:
    return "\n\n".join([
        select_body, SHAPE_NOTE,
        "Kandidaten (gescoord +1/+2):",
        "\n".join(item_line(i) for i in items),
    ])


def ground(payload: object, by_id: dict[str, ScoredItem]) -> tuple[list[Candidate], list[str]]:
    """Validate the response against the contract and the input items.
    ``bron`` and ``link`` are taken from the referenced item, never from the
    model, so every candidate row provably traces back to S1."""
    raw = payload.get("candidates") if isinstance(payload, dict) else None
    if not isinstance(raw, list):
        return [], ["response is not an object with a candidates list"]

    candidates: list[Candidate] = []
    problems: list[str] = []
    seen_ranks: dict[str, set[int]] = {}
    for entry in raw:
        try:
            rows = [{**row, "bron": "", "link": ""} for row in entry.get("items", [])]
            cand = Candidate.model_validate({**entry, "items": rows})
        except (ValidationError, AttributeError, TypeError) as e:
            problems.append(f"invalid candidate entry: {e}")
            continue
        if cand.rank in seen_ranks.setdefault(cand.scope, set()):
            problems.append(f"scope {cand.scope}: rank {cand.rank} used twice")
        seen_ranks[cand.scope].add(cand.rank)
        for row in cand.items:
            item = by_id.get(row.id)
            if item is None:
                problems.append(f"unknown item id {row.id!r} (topic {cand.topic!r})")
            elif cand.scope not in item.scopes:
                problems.append(f"item {row.id} has scopes {item.scopes}, "
                                f"not {cand.scope} (topic {cand.topic!r})")
            else:
                row.bron, row.link = item.bron, item.link
        candidates.append(cand)
    return candidates, problems


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    brief = prompts.load_prompt(ctx.root, "brief")
    select = prompts.load_prompt(ctx.root, "select")
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA, model=cfg["model"])

    scored = load_artifact(ctx.work_dir / "30-scored.json", ScoredItem)
    positive = [i for i in scored if i.score >= 1]
    if not positive:
        raise SystemExit("S4 select: no +1/+2 items to select from (PIPE-4)")
    by_id = {i.id: i for i in positive}

    prompt = build_prompt(select.body, positive)
    attempts = []
    for attempt in range(1, MAX_ATTEMPTS + 1):
        call_failed = False
        try:
            payload = call(prompt, brief.body)
            candidates, problems = ground(payload, by_id)
        except llm.LlmError as e:
            candidates, problems = [], [str(e)]
            call_failed = True
        attempts.append({"attempt": attempt, "problems": problems})
        if not problems:
            break
        if attempt < MAX_ATTEMPTS:
            time.sleep(BACKOFF_S * 2 ** (attempt - 1))
            prompt = build_prompt(select.body, positive)
            if not call_failed:  # only grounding feedback goes to the model
                prompt += ("\n\nJe vorige antwoord was ongeldig:\n- "
                           + "\n- ".join(problems) + "\nCorrigeer dit.")
    else:
        raise SystemExit("S4 select: no valid selection after "
                         f"{MAX_ATTEMPTS} attempts: {problems}")

    candidates.sort(key=lambda c: (["L", "R", "N", "I"].index(c.scope), c.rank))
    save_artifact(ctx.work_dir / "40-candidates.json", candidates)
    log = {
        "model": cfg["model"],
        "prompt_versions": {"brief": brief.version, "select": select.version},
        "input_items": len(positive), "attempts": attempts,
    }
    (ctx.work_dir / "40-select-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    rows = sum(len(c.items) for c in candidates)
    print(f"S4 select: {len(positive)} +1/+2 items → {len(candidates)} topics"
          f" ({rows} rows) in {len(attempts)} attempt(s)")
