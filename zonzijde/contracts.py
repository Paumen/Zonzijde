"""Data contracts for the stage artifacts (ARCHITECTURE §4).

Artifacts live in ``editions/<date>/work/``, are pretty-printed JSON with a
stable key order (the field order defined here), and validate against these
models. Item identity: ``id = sha1(canonical_link)[:12]``, assigned at S1 and
carried through the funnel.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field

Scope = Literal["L", "R", "N", "I"]

# Query parameters that vary per referrer without changing the article; kept
# out of the canonical link so the same article dedupes across feeds (PIPE-2).
_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {"fbclid", "gclid"}


def canonical_link(url: str) -> str:
    """Normalise a link just enough for identity: trim, drop the fragment and
    tracking parameters. Anything more aggressive risks merging distinct
    articles, so we stop here."""
    parts = urlsplit(url.strip())
    query = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if not (k.startswith(_TRACKING_PREFIXES) or k in _TRACKING_KEYS)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ""))


def item_id(link: str) -> str:
    return hashlib.sha1(canonical_link(link).encode("utf-8")).hexdigest()[:12]


class FeedItem(BaseModel):
    """One feed item — shape of ``10-items.json`` and ``20-filtered.json``."""

    id: str
    source: str
    bron: str
    scopes: list[Scope]
    title: str
    link: str
    summary: str
    published: datetime | None
    fetched: datetime


class RejectedItem(FeedItem):
    """``20-rejected.json`` entry: the item plus why it was rejected,
    e.g. ``duplicate`` or ``bucket:B2`` (PIPE-2, kept for auditability)."""

    reason: str


class ScoredItem(FeedItem):
    """``30-scored.json`` entry: item + direction score (PIPE-3). Items the
    scorer could not score are *absent* from the artifact — fail-closed."""

    score: int = Field(ge=-2, le=2)


class CandidateItem(BaseModel):
    """One source article backing a selected topic (PIPE-4 row). Dutch field
    names per the spec's column contract; ``id`` traces back to S1."""

    id: str
    bron: str
    titel: str
    samenvatting: str
    link: str


class Candidate(BaseModel):
    """``40-candidates.json`` entry (S4): one ranked topic per scope, with one
    row per source article covering it (PIPE-4)."""

    scope: Scope
    rank: int = Field(ge=1, le=5)
    topic: str
    items: list[CandidateItem] = Field(min_length=1)


FetchMethod = Literal["requests", "playwright"]


class ArticleText(CandidateItem):
    """``50-articles.json`` entry (S5): candidate item + full text (PIPE-5).
    ``ok=False`` means both fetch routes (plain request, then headless
    browser) were exhausted; the row stays in the file for the run report but
    never becomes writing material — there is no summary fallback,
    ``samenvatting`` is metadata here. ``method`` is the last route tried."""

    ok: bool
    method: FetchMethod
    text: str
    words: int
    links: list[str]
    note: str


Length = Literal["long", "standard", "short"]
ArticleType = Literal["news", "feature", "profile", "zoom-out", "zoom-in"]
OptionalKind = Literal["quote", "number", "side-story", "none"]


class OutlineSlot(BaseModel):
    """One planned article of ``60-outline.json`` (S6/PIPE-6). ``pos`` and
    ``role`` are assigned in code from the plan's ring order (ED-6), and
    ``source_date`` is derived from the sources' published dates (ED-3) —
    the model never dictates any of the three."""

    pos: int = Field(ge=1)
    scope: Scope
    role: Literal["front-hero", "body"]
    topic: str
    length: Length
    type: ArticleType
    angle: str
    devices: list[str]
    source_ids: list[str] = Field(min_length=1)
    location: str
    source_date: date | None


class OutlineIllustration(BaseModel):
    """The custom-illustration pick (EL-3): which slot it accompanies and a
    concrete drawable subject. S9 draws it; the editor judges it at the gate."""

    slot_pos: int = Field(ge=1)
    subject: str


class OptionalElement(BaseModel):
    """EL-5: at most one per edition — quote, number of the week, or side
    story; ``kind: none`` with empty content when the edition carries none."""

    kind: OptionalKind
    content: str


class EditionOutline(BaseModel):
    """``60-outline.json`` (S6): the edition plan per PIPE-6."""

    edition: date
    slots: list[OutlineSlot] = Field(min_length=1)
    illustration: OutlineIllustration
    optional_element: OptionalElement


class Draft(BaseModel):
    """``70-drafts.json`` entry (S7/PIPE-7): one written article. ``words``
    is computed from ``paragraphs`` in code, never taken from the model;
    ``location``/``source_date`` carry over from the outline slot (ED-3)."""

    pos: int = Field(ge=1)
    title: str
    location: str
    source_date: date | None
    paragraphs: list[str] = Field(min_length=1)
    words: int


class Review(BaseModel):
    """S8's findings for one article: unsupported facts found (and fixed or
    flagged, WR-2) plus language/title corrections — the correction log for
    the edition PR (PIPE-8)."""

    fact_issues: list[str]
    corrections: list[str]


class ReviewedArticle(Draft):
    """``80-reviewed.json`` entry (S8/PIPE-8): the corrected article + what
    the review changed."""

    review: Review


def save_artifact(path: Path, items: list[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [i.model_dump(mode="json") for i in items]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


M = TypeVar("M", bound=BaseModel)


def load_artifact(path: Path, model: type[M]) -> list[M]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [model.model_validate(d) for d in data]


def save_model(path: Path, model: BaseModel) -> None:
    """Like ``save_artifact`` for the single-object artifacts (the outline)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_model(path: Path, model: type[M]) -> M:
    return model.model_validate(json.loads(path.read_text(encoding="utf-8")))
