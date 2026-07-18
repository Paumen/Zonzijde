import shutil
from datetime import date
from pathlib import Path

import pytest

from zonzijde.context import RunContext

REPO_ROOT = Path(__file__).resolve().parent.parent


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
