from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

from pydantic import ValidationError

from .. import llm, prompts
from ..context import RunContext
from ..contracts import (ArticleText, Draft, EditionOutline, OutlineSlot,
                         Review, ReviewedArticle, load_artifact, load_model,
                         save_artifact)
from .write import word_count

RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "text": {"type": "string"},
        "fact_issues": {"type": "array", "items": {"type": "string"}},
        "corrections": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["title", "text", "fact_issues", "corrections"],
    "additionalProperties": False,
}

FrontierCall = Callable[[str, str], object]


def build_prompt(draft: Draft, slot: OutlineSlot, budget: dict,
                 sources: list[ArticleText]) -> str:
    parts = [
        f"Draft article (slot {draft.pos}, {slot.length}, written to a "
        f"guide of {budget['min']}–{budget['max']} words):",
        f"Titel: {draft.title}",
        draft.text,
        "Source text(s):",
    ]
    for art in sources:
        parts.append(f"### {art.bron} — {art.titel}\n\n{art.text}")
    refs = [r for art in sources for r in art.references if r.ok]
    if refs:
        parts.append("Background reference text (from links in the source):")
        for ref in refs:
            parts.append(f"#### {ref.url}\n\n{ref.text}")
    return "\n\n".join(parts)


def ground(payload: object, draft: Draft) -> tuple[ReviewedArticle | None, list[str]]:
    if not isinstance(payload, dict):
        return None, [f"not a JSON object: {type(payload).__name__}"]
    title = payload.get("title").strip() \
        if isinstance(payload.get("title"), str) else ""
    text = payload.get("text").strip() \
        if isinstance(payload.get("text"), str) else ""

    def _strings(key: str) -> list[str]:
        raw = payload.get(key)
        return [s.strip() for s in raw if isinstance(s, str) and s.strip()] \
            if isinstance(raw, list) else []

    try:
        reviewed = ReviewedArticle(
            pos=draft.pos, title=title, location=draft.location,
            source_date=draft.source_date, text=text,
            words=word_count(text),
            review=Review(fact_issues=_strings("fact_issues"),
                          corrections=_strings("corrections")))
    except ValidationError as e:
        return None, [f"invalid reviewed article: {e}"]
    return reviewed, []


def review_draft(draft: Draft, slot: OutlineSlot,
                 articles: dict[str, ArticleText], ed_cfg: dict,
                 system: str, call: FrontierCall
                 ) -> tuple[ReviewedArticle | None, list[str]]:
    budget = ed_cfg["words"][slot.length]
    sources = [articles[sid] for sid in slot.source_ids if sid in articles]
    prompt = build_prompt(draft, slot, budget, sources)
    try:
        return ground(call(prompt, system), draft)
    except llm.LlmError as e:
        return None, [str(e)]


def run(ctx: RunContext, call: FrontierCall | None = None) -> None:
    cfg = ctx.llm_cfg("frontier")
    ed_cfg = ctx.edition_cfg
    stage_cfg = ctx.stage_cfg("review")
    concurrency = int(stage_cfg.get("concurrency", 3))
    rules = prompts.load_prompt(ctx.root, "review")
    if call is None:
        call = lambda prompt, system: llm.frontier_json(
            prompt, system=system, schema=RESPONSE_SCHEMA,
            model=cfg["model"], effort=cfg.get("effort"))

    drafts = load_artifact(ctx.work_dir / "70-drafts.json", Draft)
    outline = load_model(ctx.work_dir / "60-outline.json", EditionOutline)
    slots = {s.pos: s for s in outline.slots}
    missing = [d.pos for d in drafts if d.pos not in slots]
    if missing:
        raise SystemExit(f"S8 review: draft slot(s) {missing} not in the "
                         "outline — artifacts out of step, re-run S6/S7")
    articles = {a.id: a for a in
                load_artifact(ctx.work_dir / "50-articles.json", ArticleText)}

    def work(draft: Draft) -> tuple[ReviewedArticle | None, list[str]]:
        return review_draft(draft, slots[draft.pos], articles, ed_cfg,
                            rules.body, call)

    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        results = list(pool.map(work, drafts))

    reviewed = [r for r, _ in results if r is not None]
    failed = [d.pos for d, (r, _) in zip(drafts, results) if r is None]
    log = {
        "model": cfg["model"],
        "prompt_versions": {"review": rules.version},
        "articles": [{"pos": d.pos,
                      "words": {"draft": d.words,
                                "reviewed": r.words if r else None},
                      "fact_issues": r.review.fact_issues if r else [],
                      "corrections": r.review.corrections if r else [],
                      "problems": p}
                     for d, (r, p) in zip(drafts, results)],
        "words_total": sum(r.words for r in reviewed),
        "failed_slots": failed,
    }
    (ctx.work_dir / "80-review-log.json").write_text(
        json.dumps(log, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if failed:
        raise SystemExit(
            f"S8 review: no valid review for slot(s) {failed} "
            "— see 80-review-log.json")

    reviewed.sort(key=lambda r: r.pos)
    save_artifact(ctx.work_dir / "80-reviewed.json", reviewed)
    issues = sum(len(r.review.fact_issues) for r in reviewed)
    corrections = sum(len(r.review.corrections) for r in reviewed)
    print(f"S8 review: {len(reviewed)} articles, {issues} fact issue(s), "
          f"{corrections} correction(s), {log['words_total']} words")
