"""Contracts: canonical link, item identity, artifact round-trip (§4)."""

from datetime import datetime

from zonzijde.context import TZ
from zonzijde.contracts import (FeedItem, RejectedItem, canonical_link,
                                item_id, load_artifact, save_artifact)


def test_canonical_link_strips_fragment_and_tracking():
    assert (canonical_link("https://x.nl/a?utm_source=rss&utm_medium=web#top")
            == "https://x.nl/a")
    assert canonical_link("https://x.nl/a?id=7&fbclid=abc") == "https://x.nl/a?id=7"
    # Meaningful query parameters and their order survive.
    assert canonical_link("https://x.nl/a?b=2&a=1") == "https://x.nl/a?b=2&a=1"


def test_item_id_is_stable_and_tracking_invariant():
    a = item_id("https://x.nl/artikel")
    assert len(a) == 12
    assert a == item_id("https://x.nl/artikel?utm_source=nieuwsbrief")
    assert a != item_id("https://x.nl/ander-artikel")


def test_artifact_round_trip(tmp_path):
    item = FeedItem(
        id=item_id("https://x.nl/a"), source="gld", bron="Gld", scopes=["R"],
        title="Zonnebloemen bloeien vroeg", link="https://x.nl/a",
        summary="Een zomer vol zon.",
        published=datetime(2026, 7, 14, 9, 30, tzinfo=TZ),
        fetched=datetime(2026, 7, 18, 4, 31, 22, tzinfo=TZ))
    path = tmp_path / "10-items.json"
    save_artifact(path, [item])
    (loaded,) = load_artifact(path, FeedItem)
    assert loaded == item
    # Pretty-printed with the contract's stable key order (diffable in the PR).
    text = path.read_text(encoding="utf-8")
    assert text.index('"id"') < text.index('"source"') < text.index('"title"')
    assert "+02:00" in text


def test_rejected_item_carries_reason(tmp_path):
    item = RejectedItem(
        id="abc123def456", source="nos_algemeen", bron="NOS Alg", scopes=["N", "I"],
        title="t", link="https://x.nl/b", summary="", published=None,
        fetched=datetime(2026, 7, 18, tzinfo=TZ), reason="bucket:B2")
    path = tmp_path / "20-rejected.json"
    save_artifact(path, [item])
    (loaded,) = load_artifact(path, RejectedItem)
    assert loaded.reason == "bucket:B2"
