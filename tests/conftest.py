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
