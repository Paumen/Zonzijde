from __future__ import annotations

import json
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from .. import llm, prompts
from ..context import RunContext
from ..contracts import FeedItem, ScoredItem, load_artifact, save_artifact

_WS_RE = re.compile(r"\s+")

LightCall = Callable[[str], object]

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "scores": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "i": {"type": "integer"},
                    "score": {"type": "integer", "minimum": -2, "maximum": 2},
                },
                "required": ["i", "score"],
                "additionalProperties": False,
            },
        },
    },
    "required": ["scores"],
    "additionalProperties": False,
}


def _unwrap_scores(payload: object) -> object:
    if not (isinstance(payload, dict) and isinstance(payload.get("scores"), list)):
        return payload
    out: dict = {}
    for row in payload["scores"]:
        if isinstance(row, dict) and "i" in row:
            out[str(row["i"])] = row.get("score")
    return out


def make_call(cfg: dict) -> LightCall:
    return lambda p: _unwrap_scores(
        llm.light_json(p, model=cfg["model"], schema=RESPONSE_SCHEMA))


def item_line(index: int, item: FeedItem) -> str:
    text = f"{item.title} — {item.summary}" if item.summary else item.title
    return f"{index}. {_WS_RE.sub(' ', text)[:500]}"


def build_batch_prompt(prompt_body: str, batch: list[FeedItem]) -> str:
    lines = [item_line(k + 1, item) for k, item in enumerate(batch)]
    return prompt_body + "\n" + "\n".join(lines)


def parse_scores(payload: object, n: int) -> tuple[dict[int, int], list[str]]:
    if not isinstance(payload, dict):
        return {}, [f"not a JSON object: {type(payload).__name__}"]
    scores: dict[int, int] = {}
    problems = []
    for key, value in payload.items():
        try:
            idx = int(key)
        except (TypeError, ValueError):
            problems.append(f"non-integer key {key!r}")
            continue
        if not 1 <= idx <= n:
            problems.append(f"key {idx} out of range 1..{n}")
        elif idx in scores:
            problems.append(f"key {idx} repeated")
        elif not isinstance(value, int) or isinstance(value, bool) or not -2 <= value <= 2:
            problems.append(f"item {idx}: invalid score {value!r}")
        else:
            scores[idx] = value
    missing = [i for i in range(1, n + 1) if i not in scores]
    if missing:
        problems.append(f"missing items {missing}")
    return scores, problems


def score_batch(prompt_body: str, batch: list[FeedItem],
                call: LightCall) -> tuple[dict[int, int], list[str]]:
    prompt = build_batch_prompt(prompt_body, batch)
    try:
        return parse_scores(call(prompt), len(batch))
    except llm.LlmError as e:
        return {}, [str(e)]


def run(ctx: RunContext, call: LightCall | None = None) -> None:
    cfg = ctx.llm_cfg("light")
    batch_size = int(cfg.get("batch_size", 80))
    concurrency = int(cfg.get("concurrency", 6))
    prompt = prompts.load_prompt(ctx.root, "score")
    if call is None:
        call = make_call(cfg)

    items = load_artifact(ctx.work_dir / "20-filtered.json", FeedItem)
    batches = [items[off:off + batch_size] for off in range(0, len(items), batch_size)]

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(lambda b: score_batch(prompt.body, b, call), batches))

    scored: list[ScoredItem] = []
    unscored_ids: list[str] = []
    log_batches = []
    for batch, (scores, problems) in zip(batches, results):
        for k, item in enumerate(batch):
            if k + 1 in scores:
                scored.append(ScoredItem(**item.model_dump(), score=scores[k + 1]))
            else:
                unscored_ids.append(item.id)
        log_batches.append({"items": len(batch), "scored": len(scores),
                            "problems": problems})

    save_artifact(ctx.work_dir / "30-scored.json", scored)
    distribution = Counter(s.score for s in scored)
    log = {
        "model": cfg["model"], "prompt_version": prompt.version,
        "batch_size": batch_size,
        "distribution": {str(k): distribution[k] for k in range(-2, 3)},
        "unscored_ids": unscored_ids, "batches": log_batches,
    }
    (ctx.work_dir / "30-score-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    positive = sum(1 for s in scored if s.score >= 1)
    print(f"S3 score: {len(items)} in → {len(scored)} scored"
          f" ({positive} at +1/+2), {len(unscored_ids)} unscored (excluded)")
