import shutil
from datetime import date, datetime
from pathlib import Path

import pytest

from zonzijde.context import TZ, RunContext
from zonzijde.contracts import ArticleText, Candidate, OutlineSlot, ScoredItem

REPO_ROOT = Path(__file__).resolve().parent.parent


# ----- shared builders for the S6–S8 tests ----------------------------------

def make_article(n: int, ok: bool = True, words: int = 400) -> ArticleText:
    text = ("woord " * words).strip() if ok else ""
    return ArticleText(
        id=f"{n:012d}", bron=f"Bron{n}", titel=f"Titel {n}", samenvatting="S",
        link=f"https://x.nl/{n}", ok=ok, method="requests", text=text,
        words=words if ok else 0, links=[], note="" if ok else "blocked")


def make_candidate(scope: str, rank: int, ns: list[int]) -> Candidate:
    return Candidate(
        scope=scope, rank=rank, topic=f"Topic {ns[0]}",
        items=[{"id": f"{n:012d}", "bron": f"Bron{n}", "titel": f"Titel {n}",
                "samenvatting": "S", "link": f"https://x.nl/{n}"} for n in ns])


def make_scored(n: int, scope: str, day: int = 15) -> ScoredItem:
    return ScoredItem(
        id=f"{n:012d}", source="s", bron=f"Bron{n}", scopes=[scope],
        title=f"Titel {n}", link=f"https://x.nl/{n}", summary="S",
        published=datetime(2026, 7, day, 9, 0, tzinfo=TZ),
        fetched=datetime(2026, 7, 18, 6, 0, tzinfo=TZ), score=2)


def make_slot(pos: int, scope: str, n: int, length: str = "standard") -> OutlineSlot:
    return OutlineSlot(
        pos=pos, scope=scope, role="front-hero" if pos == 1 else "body",
        topic=f"Topic {n}", length=length, type="news", angle="gewoon nieuws",
        devices=[], source_ids=[f"{n:012d}"], location="Wijchen",
        source_date=date(2026, 7, 15))


@pytest.fixture
def ctx() -> RunContext:
    # Real repo config: exercises sources.yaml / filters.yaml / edition.yaml
    # loading and validation as part of every test that uses the context.
    return RunContext(root=REPO_ROOT, edition=date(2026, 7, 26))


@pytest.fixture
def tmp_ctx(tmp_path) -> RunContext:
    # Real config, throwaway root: stages can write work/ artifacts freely.
    shutil.copytree(REPO_ROOT / "config", tmp_path / "config")
    ctx = RunContext(root=tmp_path, edition=date(2026, 7, 26))
    ctx.work_dir.mkdir(parents=True)
    return ctx
