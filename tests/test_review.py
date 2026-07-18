"""S8 review: grounding with budget slack, the correction log, artifact
consistency with the outline."""

import json

import pytest

from tests.conftest import make_article, make_slot
from zonzijde.contracts import (Draft, EditionOutline, ReviewedArticle,
                                load_artifact, save_artifact, save_model)
from zonzijde.stages import review

BUDGET = {"min": 230, "max": 360}   # config's standard class
PARAS = {"min": 3, "max": 11}
SLACK = 0.15


def _paragraphs(n_paras: int = 4, words_each: int = 60) -> list[str]:
    return [("woord " * words_each).strip() for _ in range(n_paras)]


def _draft(pos: int = 1) -> Draft:
    return Draft(pos=pos, title="Titel", location="Wijchen",
                 source_date=None, paragraphs=_paragraphs(), words=240)


def _payload(**overrides) -> dict:
    payload = {"title": "Betere titel", "paragraphs": _paragraphs(),
               "fact_issues": ["aantal gecorrigeerd naar bron"],
               "corrections": ["spelfout hersteld"]}
    payload.update(overrides)
    return payload


def test_ground_keeps_review_findings_and_slack():
    reviewed, problems = review.ground(_payload(), _draft(), BUDGET, PARAS, SLACK)
    assert problems == []
    assert reviewed.title == "Betere titel"
    assert reviewed.review.fact_issues == ["aantal gecorrigeerd naar bron"]
    assert reviewed.review.corrections == ["spelfout hersteld"]

    # 200 words: under budget minimum but within the 15% slack — a review
    # trim is not a rewrite.
    ok = _payload(paragraphs=_paragraphs(4, 50))
    _, problems = review.ground(ok, _draft(), BUDGET, PARAS, SLACK)
    assert problems == []

    ballooned = _payload(paragraphs=_paragraphs(9, 60))  # 540 > 360·1.15
    _, problems = review.ground(ballooned, _draft(), BUDGET, PARAS, SLACK)
    assert any("correct, don't rewrite" in p for p in problems)


def test_ground_tolerates_null_findings():
    # null instead of [] for the finding lists must not crash the stage.
    payload = _payload(fact_issues=None, corrections=None)
    reviewed, problems = review.ground(payload, _draft(), BUDGET, PARAS, SLACK)
    assert problems == []
    assert reviewed.review.fact_issues == []
    assert reviewed.review.corrections == []


def _seed_work(ctx, n_drafts: int = 2) -> None:
    slots = [make_slot(pos, "L", pos) for pos in range(1, n_drafts + 1)]
    outline = EditionOutline(
        edition=ctx.edition, slots=slots,
        illustration={"slot_pos": 1, "subject": "een zonnebloem"},
        optional_element={"kind": "none", "content": ""})
    save_model(ctx.work_dir / "60-outline.json", outline)
    save_artifact(ctx.work_dir / "50-articles.json",
                  [make_article(pos) for pos in range(1, n_drafts + 1)])
    save_artifact(ctx.work_dir / "70-drafts.json",
                  [_draft(pos) for pos in range(1, n_drafts + 1)])


def test_run_writes_reviewed_articles_and_correction_log(tmp_ctx):
    _seed_work(tmp_ctx)

    def call(prompt, system):
        assert "Fact-check (WR-2)" in system
        assert "Titel" in prompt and "woord" in prompt  # draft + source text
        return _payload()

    review.run(tmp_ctx, call=call)
    reviewed = load_artifact(tmp_ctx.work_dir / "80-reviewed.json",
                             ReviewedArticle)
    assert [r.pos for r in reviewed] == [1, 2]
    assert all(r.review.fact_issues for r in reviewed)
    log = json.loads((tmp_ctx.work_dir / "80-review-log.json").read_text())
    assert log["articles"][0]["words"] == {"draft": 240, "reviewed": 240}
    assert log["articles"][0]["fact_issues"] == ["aantal gecorrigeerd naar bron"]


def test_run_rejects_drafts_not_in_outline(tmp_ctx):
    _seed_work(tmp_ctx, n_drafts=1)
    save_artifact(tmp_ctx.work_dir / "70-drafts.json", [_draft(pos=9)])
    with pytest.raises(SystemExit, match="not in the outline"):
        review.run(tmp_ctx, call=lambda p, s: _payload())


def test_run_is_fatal_after_retries(tmp_ctx, monkeypatch):
    monkeypatch.setattr(review.time, "sleep", lambda s: None)
    _seed_work(tmp_ctx, n_drafts=1)
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        raise review.llm.LlmError("transport down")

    with pytest.raises(SystemExit, match="slot\\(s\\) \\[1\\]"):
        review.run(tmp_ctx, call=call)
    assert len(calls) == 3
    assert "previous review was invalid" not in calls[1]  # transport ≠ feedback
