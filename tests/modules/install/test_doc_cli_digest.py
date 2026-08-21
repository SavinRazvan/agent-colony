"""
File: test_doc_cli_digest.py
Path: tests/modules/install/test_doc_cli_digest.py
Role: Tests for doc roster-digest and doc summarize CLI.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/doc_cli.py
Notes:
 - No live network; uses tmp_path agent stubs.
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


def test_roster_digest_text(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / "implementer.md").write_text(
        "---\nname: implementer\ndescription: Does slices.\n---\n# Implementer\n",
        encoding="utf-8",
    )
    (agents / "board.md").write_text(
        "---\nname: board\ndescription: Owns board SSOT.\n---\n# Board\n",
        encoding="utf-8",
    )
    args = argparse.Namespace(directory=tmp_path, json=False)
    assert doc_cli.cmd_doc_roster_digest(args) == 0
    out = capsys.readouterr().out
    assert "agents=2" in out
    assert "implementer" in out
    assert "board" in out


def test_roster_digest_json(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / "verifier.md").write_text(
        "---\ndescription: Checks claims.\n---\n",
        encoding="utf-8",
    )
    args = argparse.Namespace(directory=tmp_path, json=True)
    assert doc_cli.cmd_doc_roster_digest(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["count"] == 1
    assert payload["agents"][0]["id"] == "verifier"


def test_summarize_skips_html_comments(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = tmp_path / "notes.md"
    doc.write_text(
        "<!--\nhidden\n-->\n\n# Title\n\nBody line\n\n",
        encoding="utf-8",
    )
    args = argparse.Namespace(
        directory=tmp_path, path="notes.md", lines=10, json=False
    )
    assert doc_cli.cmd_doc_summarize(args) == 0
    out = capsys.readouterr().out
    assert "# Title" in out
    assert "Body line" in out
    assert "hidden" not in out
