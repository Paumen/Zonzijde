"""Run context: repo paths, config loading, and the candidate window.

Every stage receives one ``RunContext``; the CLI builds it once. Runs are
anchored to the repo root (``config/`` and ``editions/`` live there), which is
the directory the CLI is invoked from — same convention as ``tools/``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel

from .contracts import Scope

TZ = ZoneInfo("Europe/Amsterdam")


class Source(BaseModel):
    """One entry of ``config/sources.yaml`` (SRC-1)."""

    id: str
    bron: str
    url: str | None = None
    builder: str | None = None
    scopes: list[Scope]


@dataclass
class RunContext:
    root: Path
    edition: date
    window_days: int | None = None  # None = config default (SRC-4)
    _edition_cfg: dict = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        cfg_path = self.root / "config" / "edition.yaml"
        if not cfg_path.is_file():
            raise SystemExit(
                f"config/edition.yaml not found under {self.root} — run from the repo root."
            )
        self._edition_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
        if self.window_days is None:
            self.window_days = int(self._edition_cfg["window"]["days"])

    @cached_property
    def sources(self) -> list[Source]:
        raw = yaml.safe_load((self.root / "config" / "sources.yaml").read_text(encoding="utf-8"))
        return [Source.model_validate(s) for s in raw["sources"]]

    @cached_property
    def buckets(self) -> dict[str, str]:
        raw = yaml.safe_load((self.root / "config" / "filters.yaml").read_text(encoding="utf-8"))
        return dict(raw["buckets"])

    @property
    def fetch_cfg(self) -> dict:
        return self._edition_cfg.get("fetch", {})

    @property
    def edition_dir(self) -> Path:
        return self.root / "editions" / self.edition.isoformat()

    @property
    def work_dir(self) -> Path:
        return self.edition_dir / "work"

    @property
    def window_start(self) -> datetime:
        """Start of the candidate window (SRC-4): midnight Amsterdam time,
        ``window_days`` before the edition date."""
        d = self.edition - timedelta(days=self.window_days)
        return datetime(d.year, d.month, d.day, tzinfo=TZ)

    def now(self) -> datetime:
        return datetime.now(TZ)
