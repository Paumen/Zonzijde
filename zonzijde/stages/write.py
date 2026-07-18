"""S7 write (PIPE-7): one frontier call per article, per the outline.

Reads ``60-outline.json`` + ``50-articles.json``, writes ``70-drafts.json``
and ``70-write-log.json``. Each call is grounded on the slot's own S5 source
texts only; the brief + writing rules (``prompts/brief.md`` +
``prompts/write.md``) are the system prompt, and the length guidance and
no-self-reference rule are stated there for the model to follow — they are
not re-checked in code. The response is
schema-enforced at the call layer; ``words`` is computed. One call per
article, no retry: only a structurally unusable response leaves a hole, and
an edition with holes fails the run (§6).

The model's editorial choices — title, length, paragraphing, whether it
followed the plan — are not validated here; the human gate judges them. The
length guidance in the prompt steers the writer; final fit is a compose/gate
decision (PIPE-9).
"""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         load_artifact, load_model, save_artifact)

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "paragraphs": {"type": "array", "minItems": 1,
                       "items": {"type": "string"}},
    },
    "required": ["title", "paragraphs"],
    "additionalProperties": False,
}

# call(prompt, system) -> parsed JSON; injectable for tests.
FrontierCall = Callable[[str, str], object]


def word_count(paragraphs: list[str]) -> int:
    return len(" ".join(paragraphs).split())


def build_prompt(slot: OutlineSlot, budget: dict, para_cfg: dict,
                 sources: list[ArticleText]) -> str:
    """The plan for this one article + its source texts."""
    plan = [
        f"Edition slot {slot.pos} ({'front page hero' if slot.role == 'front-hero' else 'body'}).",
        f"- topic: {slot.topic}",
        f"- article type: {slot.type}",
        f"- devices: {', '.join(slot.devices) or 'none'}",
        f"- location (dateline, do not restate in the body): {slot.location}",
        f"- length: {slot.length} — as a guide {budget['min']}–{budget['max']} "
        f"words, {para_cfg['min']}–{para_cfg['max']} paragraphs; the story "
        "decides, not the count",
    ]
    parts = ["\n".join(plan)]
    parts.append("Source text(s) — the only writing material:")
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    return "\n\n".join(parts)


def ground(payload: object, slot: OutlineSlot) -> tuple[Draft | None, list[str]]:
    """Build the draft from the response — no validation of the model's
    title, length or paragraphing (the human gate judges those). ``words`` is
    computed; the pydantic contract is the only structural backstop."""
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = payload.get("title").strip() \
        if isinstance(payload.get("title"), str) else ""
    raw = payload.get("paragraphs")
    paragraphs = [p.strip() for p in raw if isinstance(p, str) and p.strip()] \
        if isinstance(raw, list) else []
    try:
        draft = Draft(pos=slot.pos, title=title, location=slot.location,
                      source_date=slot.source_date, paragraphs=paragraphs,
                      words=word_count(paragraphs))
    except ValidationError as e:
        return None, [f"invalid draft: {e}"]
    return draft, []


def write_slot(slot: OutlineSlot, articles: dict[str, ArticleText],
               ed_cfg: dict, system: str,
               call: FrontierCall) -> tuple[Draft | None, list[str]]:
    """Write one article with a single call — no retry. Returns the draft
    (or None only if the call failed or the response was structurally
    unusable) plus any problem for the log."""
    budget = ed_cfg["words"][slot.length]
    para_cfg = ed_cfg["paragraphs"]
    sources = [articles[sid] for sid in slot.source_ids if sid in articles]
    prompt = build_prompt(slot, budget, para_cfg, sources)
    try:
        return ground(call(prompt, system), slot)
    except llm.LlmError as e:
        return None, [str(e)]


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    stage_cfg = ctx.stage_cfg("write")
    concurrency = int(stage_cfg.get("concurrency", 3))
    brief = prompts.load_prompt(ctx.root, "brief")
    rules = prompts.load_prompt(ctx.root, "write")
    system = f"{brief.body}\n\n{rules.body}"
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}

    def work(slot: OutlineSlot) -> tuple[Draft | None, list[str]]:
        return write_slot(slot, articles, ed_cfg, system, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, outline.slots))

    drafts = [d for d, _ in results if d is not None]
    failed = [s.pos for s, (d, _) in zip(outline.slots, results) if d is None]
    log = {
        "model": cfg["model"],
        "prompt_versions": {"brief": brief.version, "write": rules.version},
        "slots": [{"pos": s.pos, "length": s.length,
                   "words": d.words if d else None, "problems": p}
                  for s, (d, p) in zip(outline.slots, results)],
        "words_total": sum(d.words for d in drafts),
        "failed_slots": failed,
    }
    (ctx.work_dir / "70-write-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:  # an edition with holes never advances — the plan counts on
        raise SystemExit(  # every slot (ED-1/ED-2)
            f"S7 write: no valid draft for slot(s) {failed} "
            "— see 70-write-log.json")

    drafts.sort(key=lambda d: d.pos)
    save_artifact(ctx.work_dir / "70-drafts.json", drafts)
    print(f"S7 write: {len(drafts)} articles, {log['words_total']} words "
          f"(ED-5 target {ed_cfg['body_words']['min']}–"
          f"{ed_cfg['body_words']['max']})")
