from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

_ORIGIN = time.perf_counter()


def now_ms() -> int:
    return int((time.perf_counter() - _ORIGIN) * 1000)


def record_fase(work_dir: Path, name: str, started: datetime,
                elapsed_ms: int) -> None:
    path = work_dir / "timeline.json"
    fases: dict = {}
    if path.is_file():
        try:
            loaded = json.loads(path.read_text(encoding="utf-8")).get("fases")
        except ValueError:
            loaded = None
        if isinstance(loaded, dict):
            fases = loaded
    fases[name] = {"started_at": started.isoformat(), "elapsed_ms": elapsed_ms}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"fases": fases}, indent=2) + "\n",
                    encoding="utf-8")
