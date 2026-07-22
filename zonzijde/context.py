from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from functools import cached_property
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from pydantic import BaseModel

TZ = ZoneInfo("Europe/Amsterdam")


class Source(BaseModel):
    id: str
    bron: str
    url: str | None = None
    builder: str | None = None
    scopes: list[str]


@dataclass
class RunContext:
    root: Path
    edition: date
    window_days: int | None = None
    _edition_cfg: dict = field(init=False, default_factory=dict)

    def __post_init__(self) -> None:
        cfg_path = self.root / "config" / "edition.yaml"
        if not cfg_path.is_file():
            raise SystemExit(
                f"config/edition.yaml not found under {self.root} — run from the repo root."
            )
        self._edition_cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        if self.window_days is None:
            try:
                self.window_days = int(self._edition_cfg["window"]["days"])
            except (KeyError, TypeError, ValueError) as e:
                raise SystemExit(f"invalid or missing window.days in config/edition.yaml: {e}")

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
    def enrich_cfg(self) -> dict:
        return self._edition_cfg.get("enrich", {})

    def fase_cfg(self, name: str) -> dict:
        return self._edition_cfg.get(name, {})

    @property
    def edition_cfg(self) -> dict:
        cfg = self._edition_cfg.get("edition")
        if not cfg:
            raise SystemExit("edition section missing from config/edition.yaml")
        return cfg

    def llm_cfg(self, fase: str) -> dict:
        llm = self._edition_cfg.get("llm") or {}
        cfg = (llm.get("fases") or {}).get(fase)
        if not cfg or "model" not in cfg:
            raise SystemExit(
                f"llm.fases.{fase}.model missing from config/edition.yaml")
        return cfg

    @property
    def edition_dir(self) -> Path:
        return self.root / "editions" / self.edition.isoformat()

    @property
    def work_dir(self) -> Path:
        return self.edition_dir / "work"

    @property
    def window_start(self) -> datetime:
        d = self.edition - timedelta(days=self.window_days)
        return datetime(d.year, d.month, d.day, tzinfo=TZ)

    def now(self) -> datetime:
        return datetime.now(TZ)
