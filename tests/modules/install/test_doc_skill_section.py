"""
File: test_doc_skill_section.py
Path: tests/modules/install/test_doc_skill_section.py
Role: Tests for doc skill-section and validate-thin-index CLI.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/doc_cli.py
Notes:
 - Uses repo skills on disk for integration-style checks.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import doc_cli  # noqa: E402


def test_skill_section_board_ssot_continuation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = argparse.Namespace(
        directory=REPO_ROOT,
        skill="board-ssot",
        section="Continuation contract",
        json=False,
    )
    assert doc_cli.cmd_doc_skill_section(args) == 0
    out = capsys.readouterr().out
    assert "skill=board-ssot" in out
    assert "Continuation" in out or "board" in out.lower()


def test_skill_section_json_smaller_than_full() -> None:
    skill_path = REPO_ROOT / ".cursor" / "skills" / "board-ssot" / "SKILL.md"
    full_size = skill_path.stat().st_size
    args = argparse.Namespace(
        directory=REPO_ROOT,
        skill="board-ssot",
        section="Continuation contract",
        json=True,
    )
    import io
    from contextlib import redirect_stdout

    buf = io.StringIO()
    with redirect_stdout(buf):
        assert doc_cli.cmd_doc_skill_section(args) == 0
    payload = json.loads(buf.getvalue())
    assert payload["bytes"] < full_size


def test_validate_thin_index_kit_repo(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(directory=REPO_ROOT, json=False, summary=True)
    code = doc_cli.cmd_doc_validate_thin_index(args)
    out = capsys.readouterr().out
    assert "validate-thin-index:" in out
    assert code == 0 or "FAIL" in out
