"""Versioned prompt files in ``config/prompts/`` (ARCHITECTURE §6).

Each prompt is a markdown file with a YAML front-matter header carrying at
least ``version``. The body is the canonical prompt text; the version is
recorded in stage logs (and later ``edition.json``) so output changes are
attributable to prompt changes.
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import yaml


class Prompt(NamedTuple):
    name: str
    version: int
    body: str


def load_prompt(root: Path, name: str) -> Prompt:
    path = root / "config" / "prompts" / f"{name}.md"
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise SystemExit(f"{path}: missing YAML version header")
    try:
        _, header, body = text.split("---", 2)
        meta = yaml.safe_load(header)
        version = int(meta["version"])
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        raise SystemExit(f"{path}: invalid version header: {e}")
    return Prompt(name=name, version=version, body=body.strip())
