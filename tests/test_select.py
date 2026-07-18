"""S4 select: grounding validation, retry-then-fatal, artifact writing."""

from datetime import datetime

import pytest

from zonzijde.contracts import Candidate, ScoredItem, load_artifact, save_artifact
from zonzijde.context import TZ
from zonzijde.stages import select


def _scored(n: int, scopes, score: int = 2, title: str = "Titel") -> ScoredItem:
    return ScoredItem(
        id=f"{n:012d}", source="s", bron=f"Bron{n}", scopes=scopes, title=title,
        link=f"https://x.nl/{n}", summary="Samenvatting", published=None,
        fetched=datetime(2026, 7, 18, 6, 0, tzinfo=TZ), score=score)


def _payload(**overrides):
    entry = {"scope": "L", "rank": 1, "topic": "Onderwerp",
             "items": [{"id": "000000000001", "titel": "T", "samenvatting": "S"}]}
    entry.update(overrides)
    return {"candidates": [entry]}


def test_ground_fills_bron_and_link_from_source_item():
    by_id = {"000000000001": _scored(1, ["L", "R"])}
    candidates, problems = select.ground(_payload(), by_id)
    assert problems == []
    (cand,) = candidates
    assert (cand.items[0].bron, cand.items[0].link) == ("Bron1", "https://x.nl/1")


def test_ground_rejects_unknown_id_and_wrong_scope():
    by_id = {"000000000001": _scored(1, ["N"])}
    _, problems = select.ground(_payload(scope="L"), by_id)
    assert any("has scopes" in p for p in problems)
    _, problems = select.ground(
        {"candidates": [dict(_payload()["candidates"][0],
                             items=[{"id": "ffffffffffff", "titel": "T",
                                     "samenvatting": "S"}])]}, by_id)
    assert any("unknown item id" in p for p in problems)


def test_ground_rejects_duplicate_rank_and_bad_shapes():
    by_id = {"000000000001": _scored(1, ["L"])}
    payload = {"candidates": [_payload()["candidates"][0],
                              _payload(topic="Ander")["candidates"][0]]}
    _, problems = select.ground(payload, by_id)
    assert any("rank 1 used twice" in p for p in problems)
    assert select.ground("nee", by_id)[1] == \
        ["response is not an object with a candidates list"]
    _, problems = select.ground({"candidates": [{"scope": "X"}]}, by_id)
    assert any("invalid candidate entry" in p for p in problems)


def test_run_writes_sorted_candidates(tmp_ctx):
    items = [_scored(1, ["L"]), _scored(2, ["N"]), _scored(3, ["L"], score=1)]
    save_artifact(tmp_ctx.work_dir / "30-scored.json",
                  items + [_scored(9, ["L"], score=0)])  # 0 never advances

    def call(prompt, system):
        assert "000000000009" not in prompt      # PIPE-4: only +1/+2 go in
        assert "People are worn out" in system   # brief.md is the system prompt
        return {"candidates": [
            {"scope": "N", "rank": 1, "topic": "Landelijk",
             "items": [{"id": items[1].id, "titel": "T", "samenvatting": "S"}]},
            {"scope": "L", "rank": 1, "topic": "Lokaal",
             "items": [{"id": items[0].id, "titel": "T", "samenvatting": "S"},
                       {"id": items[2].id, "titel": "T2", "samenvatting": "S2"}]},
        ]}

    select.run(tmp_ctx, call=call)
    candidates = load_artifact(tmp_ctx.work_dir / "40-candidates.json", Candidate)
    assert [c.scope for c in candidates] == ["L", "N"]  # L before N
    assert len(candidates[0].items) == 2                # multi-source topic


def test_run_retries_on_problems_then_succeeds(tmp_ctx, monkeypatch):
    monkeypatch.setattr(select.time, "sleep", lambda s: None)
    item = _scored(1, ["L"])
    save_artifact(tmp_ctx.work_dir / "30-scored.json", [item])
    calls = []

    def call(prompt, system):
        calls.append(prompt)
        if len(calls) == 1:
            return {"candidates": [{"scope": "L", "rank": 1, "topic": "X",
                    "items": [{"id": "ffffffffffff", "titel": "T",
                               "samenvatting": "S"}]}]}
        return _payload()

    select.run(tmp_ctx, call=call)
    assert len(calls) == 2
    assert "ongeldig" in calls[1]  # retry carries the validation feedback
    import json
    log = json.loads((tmp_ctx.work_dir / "40-select-log.json").read_text())
    assert [a["attempt"] for a in log["attempts"]] == [1, 2]
    assert log["attempts"][0]["problems"]


def test_run_is_fatal_after_max_attempts(tmp_ctx, monkeypatch):
    monkeypatch.setattr(select.time, "sleep", lambda s: None)
    save_artifact(tmp_ctx.work_dir / "30-scored.json", [_scored(1, ["L"])])
    with pytest.raises(SystemExit, match="no valid selection after 3"):
        select.run(tmp_ctx, call=lambda p, s: {"candidates": "nee"})


def test_run_requires_positive_items(tmp_ctx):
    save_artifact(tmp_ctx.work_dir / "30-scored.json", [_scored(1, ["L"], score=0)])
    with pytest.raises(SystemExit, match="no \\+1/\\+2 items"):
        select.run(tmp_ctx, call=lambda p, s: _payload())
