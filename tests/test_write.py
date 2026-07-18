"""S7 write: per-article grounding (ED-4, the loose word backstop, no
self-reference), computed word counts, retry-then-fatal, artifact writing."""

import json
from datetime import date

import pytest

from tests.conftest import make_article, make_slot
from zonzijde.contracts import (Draft, EditionOutline, load_artifact,
                                save_artifact, save_model)
from zonzijde.stages import write

BUDGET = {"min": 250, "max": 500}   # config's standard class
PARAS = {"min": 3, "max": 11}


def _paragraphs(n_paras: int = 4, words_each: int = 75) -> list[str]:
    return [("woord " * words_each).strip() for _ in range(n_paras)]


def _payload(**overrides) -> dict:
    payload = {"title": "Goed nieuws uit Wijchen", "paragraphs": _paragraphs()}
    payload.update(overrides)
    return payload


def _slot(pos: int = 1, n: int = 1, length: str = "standard"):
    return make_slot(pos, "L", n, length)


def test_ground_computes_words_and_carries_slot_fields():
    draft, problems = write.ground(_payload(), _slot(), BUDGET, PARAS)
    assert problems == []
    assert draft.words == 300                       # computed, not trusted
    assert (draft.pos, draft.location) == (1, "Wijchen")
    assert draft.source_date == date(2026, 7, 15)   # ED-3, from the outline


def test_ground_rejects_budget_paragraphs_title_and_self_reference():
    _, problems = write.ground(_payload(paragraphs=_paragraphs(2)),
                               _slot(), BUDGET, PARAS)
    assert any("(ED-4)" in p for p in problems)

    _, problems = write.ground(_payload(paragraphs=_paragraphs(4, 20)),
                               _slot(), BUDGET, PARAS)
    assert any("guidance" in p for p in problems)

    # the word range is guidance widened by slack into a backstop: a draft
    # a bit over the guide passes, one that plainly ignored the plan fails
    near = _payload(paragraphs=_paragraphs(4, 130))        # 520 words
    assert write.ground(near, _slot(), BUDGET, PARAS, slack=0.10)[1] == []
    _, problems = write.ground(near, _slot(), BUDGET, PARAS)
    assert any("guidance" in p for p in problems)
    wild = _payload(paragraphs=_paragraphs(4, 250))        # 1000 > 500·1.5
    _, problems = write.ground(wild, _slot(), BUDGET, PARAS, slack=0.5)
    assert any("guidance" in p for p in problems)

    _, problems = write.ground(_payload(title="  "), _slot(), BUDGET, PARAS)
    assert any("title" in p for p in problems)

    sneaky = _paragraphs(3) + ["Zo staat het in Deze Krant."]
    _, problems = write.ground(_payload(paragraphs=sneaky),
                               _slot(), BUDGET, PARAS)
    assert any("PIPE-7" in p for p in problems)

    assert write.ground("nee", _slot(), BUDGET, PARAS)[1] == \
        ["not a JSON object: str"]


def _seed_work(ctx, lengths=("standard", "standard")) -> EditionOutline:
    slots = [make_slot(pos, "L", pos, length)
             for pos, length in enumerate(lengths, start=1)]
    outline = EditionOutline(
        edition=ctx.edition, slots=slots,
        illustration={"slot_pos": 1, "subject": "een zonnebloem"},
        optional_element={"kind": "none", "content": ""})
    save_model(ctx.work_dir / "60-outline.json", outline)
    save_artifact(ctx.work_dir / "50-articles.json",
                  [make_article(pos) for pos in range(1, len(lengths) + 1)])
    return outline


def test_run_writes_drafts_per_slot(tmp_ctx):
    _seed_work(tmp_ctx)
    prompts_seen = []

    def call(prompt, system):
        prompts_seen.append(prompt)
        assert "Schrijf alle artikelen in het Nederlands" in system
        assert "woord" in prompt                    # its source text is inline
        return _payload()

    write.run(tmp_ctx, call=call)
    drafts = load_artifact(tmp_ctx.work_dir / "70-drafts.json", Draft)
    assert [d.pos for d in drafts] == [1, 2]
    assert all(d.words == 300 for d in drafts)
    # each prompt names the other slots as context only (WR-1 references)
    assert any("Elsewhere in this edition" in p for p in prompts_seen)
    log = json.loads((tmp_ctx.work_dir / "70-write-log.json").read_text())
    assert log["words_total"] == 600
    assert log["failed_slots"] == []


def test_run_retries_with_feedback_then_fatal(tmp_ctx, monkeypatch):
    monkeypatch.setattr(write.time, "sleep", lambda s: None)
    _seed_work(tmp_ctx, lengths=("standard",))
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        return _payload(paragraphs=_paragraphs(2))  # always too few (ED-4)

    with pytest.raises(SystemExit, match="slot\\(s\\) \\[1\\]"):
        write.run(tmp_ctx, call=call)
    assert len(calls) == 3
    assert "previous draft was invalid" in calls[1]
    # the log survives the failure for diagnosis
    log = json.loads((tmp_ctx.work_dir / "70-write-log.json").read_text())
    assert log["failed_slots"] == [1]
