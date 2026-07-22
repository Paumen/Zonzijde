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
        version = int(meta["version"] if "version" in meta else meta["versie"])
    except (ValueError, KeyError, TypeError, yaml.YAMLError) as e:
        raise SystemExit(f"{path}: invalid version header: {e}")
    return Prompt(name=name, version=version, body=body.strip())


def system_base(brief_body: str, pipeline_body: str,
                stijlgids_body: str | None = None) -> str:
    parts = ["Je bent Claude, en werkt in de redactie van De Zonzijde.",
             f"<paper>\n{brief_body}\n</paper>",
             f"<pipeline>\n{pipeline_body}\n</pipeline>"]
    if stijlgids_body is not None:
        parts.append(f"<stijlgids>\n{stijlgids_body}\n</stijlgids>")
    return "\n\n".join(parts)
