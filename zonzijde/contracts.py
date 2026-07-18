from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal, TypeVar
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import BaseModel, Field

_TRACKING_PREFIXES = ("utm_",)
_TRACKING_KEYS = {"fbclid", "gclid"}


def canonical_link(url: str) -> str:
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
    id: str
    source: str
    bron: str
    scopes: list[str]
    title: str
    link: str
    summary: str
    published: datetime | None
    fetched: datetime


class RejectedItem(FeedItem):
    reason: str


class ScoredItem(FeedItem):
    score: int = Field(ge=-2, le=2)


class CandidateItem(BaseModel):
    id: str
    bron: str
    titel: str
    samenvatting: str
    link: str


class Candidate(BaseModel):
    scope: str
    topic: str
    items: list[CandidateItem] = Field(min_length=1)


FetchMethod = Literal["requests", "playwright"]


class ArticleText(CandidateItem):
    ok: bool
    method: FetchMethod
    text: str
    words: int
    links: list[str]
    note: str


Length = Literal["long", "standard", "short"]


class OutlineSlot(BaseModel):
    pos: int = Field(ge=1)
    scope: str
    topic: str
    length: Length
    devices: list[str]
    source_ids: list[str] = Field(min_length=1)
    location: str
    source_date: date | None


class EditionOutline(BaseModel):
    edition: date
    slots: list[OutlineSlot] = Field(min_length=1)


class Draft(BaseModel):
    pos: int = Field(ge=1)
    title: str
    location: str
    source_date: date | None
    text: str
    words: int


class Review(BaseModel):
    fact_issues: list[str]
    corrections: list[str]


class ReviewedArticle(Draft):
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
    path.parent.mkdir(parents=True, exist_ok=True)
    data = model.model_dump(mode="json")
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_model(path: Path, model: type[M]) -> M:
    return model.model_validate(json.loads(path.read_text(encoding="utf-8")))
