"""Prompt loader: version header parsing over the real prompt files."""

import pytest

from tests.conftest import REPO_ROOT
from zonzijde.prompts import load_prompt


@pytest.mark.parametrize("name", ["brief", "score", "select", "outline", "write"])
def test_real_prompts_have_version_headers(name):
    prompt = load_prompt(REPO_ROOT, name)
    assert prompt.version >= 1
    assert prompt.body and not prompt.body.startswith("---")


def test_score_prompt_body_is_the_canonical_wording():
    body = load_prompt(REPO_ROOT, "score").body
    assert body.startswith("Je beoordeelt nieuwsberichten.")
    assert "maximaal 0" in body  # promo cap (PIPE-3)


def test_missing_header_is_fatal(tmp_path):
    (tmp_path / "config" / "prompts").mkdir(parents=True)
    (tmp_path / "config" / "prompts" / "kaal.md").write_text("geen header")
    with pytest.raises(SystemExit, match="missing YAML version header"):
        load_prompt(tmp_path, "kaal")
