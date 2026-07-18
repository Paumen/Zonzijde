"""S7 write: no validation of the model's output — the draft is built as-is
and only computed word counts + the pydantic contract stand. Single call,
fatal only on a structurally unusable response."""

import json
from datetime import date

import pytest

from tests.conftest import make_article, make_slot
from zonzijde.contracts import (Draft, EditionOutline, load_artifact,
                                save_artifact, save_model)
from zonzijde.stages import write


def _paragraphs(n_paras: int = 4, words_each: int = 75) -> list[str]:
    return [("woord " * words_each).strip() for _ in range(n_paras)]


def _payload(**overrides) -> dict:
    payload = {"title": "Goed nieuws uit Wijchen", "paragraphs": _paragraphs()}
    payload.update(overrides)
    return payload


def _slot(pos: int = 1, n: int = 1, length: str = "standard"):
    return make_slot(pos, "L", n, length)


def test_ground_computes_words_and_carries_slot_fields():
    draft, problems = write.ground(_payload(), _slot())
    assert problems == []
    assert draft.words == 300                       # computed, not trusted
    assert (draft.pos, draft.location) == (1, "Wijchen")
    assert draft.source_date == date(2026, 7, 15)   # ED-3, from the outline


def test_ground_takes_the_model_output_as_is():
    # None of the old checks apply: too few paragraphs, off-budget length,
    # a self-reference — all accepted now (the human gate judges them).
    draft, problems = write.ground(
        _payload(paragraphs=_paragraphs(2, 5) + ["Zo staat het in Deze Krant."]),
        _slot())
    assert problems == []
    assert len(draft.paragraphs) == 3
    assert "Deze Krant" in draft.paragraphs[-1]


def test_ground_only_rejects_structurally_unusable_output():
    # not a dict, or no usable paragraphs (the pydantic contract) — those are
    # the only things that fail now.
    assert write.ground("nee", _slot())[1] == ["not a JSON object: str"]
    _, problems = write.ground(_payload(paragraphs=[]), _slot())
    assert any("invalid draft" in p for p in problems)


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


def test_unusable_response_is_fatal_single_call(tmp_ctx):
    _seed_work(tmp_ctx, lengths=("standard",))
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        return {"title": "T", "paragraphs": []}  # no usable paragraphs

    with pytest.raises(SystemExit, match="slot\\(s\\) \\[1\\]"):
        write.run(tmp_ctx, call=call)
    assert len(calls) == 1  # one call per slot, no retry
    # the log survives the failure for diagnosis
    log = json.loads((tmp_ctx.work_dir / "70-write-log.json").read_text())
    assert log["failed_slots"] == [1]
    assert log["slots"][0]["problems"]  # why it failed is recorded
