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
        "text": {"type": "string"},
    },
    "required": ["title", "text"],
    "additionalProperties": False,
}

FrontierCall = Callable[[str, str], object]


def word_count(text: str) -> int:
    return len(text.split())


def build_prompt(slot: OutlineSlot, budget: dict,
                 sources: list[ArticleText]) -> str:
    plan = [
        f"Edition slot {slot.pos}.",
        f"- topic: {slot.topic}",
        f"- devices: {', '.join(slot.devices) or 'none'}",
        f"- location (dateline, do not restate in the body): {slot.location}",
        f"- length: {slot.length} — as a guide {budget['min']}–{budget['max']} "
        "words; the story decides, not the count",
    ]
    parts = ["\n".join(plan)]
    parts.append("Source text(s):")
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    refs = [r for art in sources for r in art.references if r.ok]
    if refs:
        parts.append("Background reference text (from links in the source):")
        for ref in refs:
            parts.append(f"#### {ref.url}\n\n{ref.text}")
    return "\n\n".join(parts)


def ground(payload: object, slot: OutlineSlot) -> tuple[Draft | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = payload.get("title").strip() \
        if isinstance(payload.get("title"), str) else ""
    text = payload.get("text").strip() \
        if isinstance(payload.get("text"), str) else ""
    try:
        draft = Draft(pos=slot.pos, title=title, location=slot.location,
                      source_date=slot.source_date, text=text,
                      words=word_count(text))
    except ValidationError as e:
        return None, [f"invalid draft: {e}"]
    return draft, []


def write_slot(slot: OutlineSlot, articles: dict[str, ArticleText],
               ed_cfg: dict, system: str,
               call: FrontierCall) -> tuple[Draft | None, list[str]]:
    budget = ed_cfg["words"][slot.length]
    sources = [articles[sid] for sid in slot.source_ids if sid in articles]
    prompt = build_prompt(slot, budget, sources)
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
    usage: list[dict] = []
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"), usage_sink=usage)

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
        "model": cfg["model"], "effort": cfg.get("effort"),
        "prompt_versions": {"brief": brief.version, "write": rules.version},
        "slots": [{"pos": s.pos, "length": s.length,
                   "words": d.words if d else None, "problems": p}
                  for s, (d, p) in zip(outline.slots, results)],
        "words_total": sum(d.words for d in drafts),
        "failed_slots": failed,
        "llm": llm.summarize_usage(usage),
    }
    (ctx.work_dir / "70-write-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(
            f"S7 write: no valid draft for slot(s) {failed} "
            "— see 70-write-log.json")

    drafts.sort(key=lambda d: d.pos)
    save_artifact(ctx.work_dir / "70-drafts.json", drafts)
    print(f"S7 write: {len(drafts)} articles, {log['words_total']} words "
          f"(ED-5 target {ed_cfg['body_words']['min']}–"
          f"{ed_cfg['body_words']['max']})")
