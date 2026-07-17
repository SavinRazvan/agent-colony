"""
File: test_gates_full.py
Path: tests/modules/workflow_mcp/test_gates_full.py
Role: Full-branch coverage for workflow_mcp/gates.py (prepare.py GATES loader).
Used By:
 - pytest
Depends On:
 - .ai_infra/mcp_servers/workflow_mcp/gates.py
"""

from __future__ import annotations

from pathlib import Path

import pytest

from workflow_mcp import gates

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_load_prepare_module_missing_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="prepare.py not found"):
        gates._load_prepare_module(tmp_path)


def test_load_prepare_module_legacy_layout(tmp_path: Path) -> None:
    legacy = tmp_path / "scripts" / "pr" / "prepare.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("GATES = [['echo', 'ok']]\n", encoding="utf-8")
    module = gates._load_prepare_module(tmp_path)
    assert module.GATES == [["echo", "ok"]]


def test_load_gates_default_root() -> None:
    result = gates.load_gates()
    assert isinstance(result, list)
    assert len(result) >= 1


def test_load_gates_plain_gates_list_no_resolve(tmp_path: Path) -> None:
    canonical = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("GATES = [['echo', 'a'], ['echo', 'b']]\n", encoding="utf-8")
    result = gates.load_gates(tmp_path)
    assert result == [["echo", "a"], ["echo", "b"]]


def test_load_gates_invalid_gates_type_raises(tmp_path: Path) -> None:
    canonical = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    canonical.parent.mkdir(parents=True)
    canonical.write_text("GATES = 'not-a-list'\n", encoding="utf-8")
    with pytest.raises(ValueError, match="GATES must be a list"):
        gates.load_gates(tmp_path)
