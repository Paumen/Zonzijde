"""Data contracts for the stage artifacts (ARCHITECTURE §4).

Artifacts live in ``editions/<date>/work/``, are pretty-printed JSON with a
stable key order (the field order defined here), and validate against these
models. Item identity: ``id = sha1(canonical_link)[:12]``, assigned at S1 and
carried through the funnel.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
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


FetchMethod = Literal["requests", "playwright", "alt-source"]


class ArticleText(CandidateItem):
    """``50-articles.json`` entry (S5): candidate item + full text (PIPE-5).
    ``ok=False`` means all fetch routes were exhausted; the row stays in the
    file for the run report but never becomes writing material — there is no
    summary fallback, ``samenvatting`` is metadata here. ``method`` is the
    last route tried; for ``alt-source`` the substitute URL is in ``note``."""

    ok: bool
    method: FetchMethod
    text: str
    words: int
    links: list[str]
    note: str


def save_artifact(path: Path, items: list[BaseModel]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = [i.model_dump(mode="json") for i in items]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


M = TypeVar("M", bound=BaseModel)


def load_artifact(path: Path, model: type[M]) -> list[M]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return [model.model_validate(d) for d in data]
