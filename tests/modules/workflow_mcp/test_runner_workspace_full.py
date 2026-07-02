"""
File: test_runner_workspace_full.py
Path: tests/modules/workflow_mcp/test_runner_workspace_full.py
Role: Full-branch coverage for workflow_mcp/runner.py and workflow_mcp/workspace.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/mcp_servers/workflow_mcp/runner.py
 - .ai_infra/mcp_servers/workflow_mcp/workspace.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from workflow_mcp import runner, workspace

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_resolve_python_replaces_python_literal() -> None:
    assert runner.resolve_python(["python", "-c", "1"])[0] == sys.executable


def test_resolve_python_leaves_other_commands() -> None:
    assert runner.resolve_python(["ls", "-la"]) == ["ls", "-la"]


def test_resolve_script_path_legacy_prefix_not_canonical(tmp_path: Path) -> None:
    # legacy "scripts/x" with no canonical .ai_infra/scripts/x and no direct scripts/x file:
    # falls through to the final legacy-rewrite return.
    result = runner.resolve_script_path(tmp_path, "scripts/does/not/exist.py")
    assert result == tmp_path / ".ai_infra" / "scripts" / "does" / "not" / "exist.py"


def test_resolve_script_path_direct_hit(tmp_path: Path) -> None:
    direct = tmp_path / "some_script.py"
    direct.write_text("print('x')\n", encoding="utf-8")
    result = runner.resolve_script_path(tmp_path, "some_script.py")
    assert result == direct


def test_resolve_script_path_non_legacy_missing(tmp_path: Path) -> None:
    result = runner.resolve_script_path(tmp_path, "no/such/file.py")
    assert result == tmp_path / "no/such/file.py"


def test_run_script_not_found(tmp_path: Path) -> None:
    code, out = runner.run_script("nope.py", [], tmp_path)
    assert code == 1
    assert "Script not found" in out


def test_run_script_success() -> None:
    code, out = runner.run_script("scripts/pr/prepare.py", ["--help"], REPO_ROOT)
    assert code == 0
    assert out


def test_workspace_root_walks_up_from_subdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_ROOT", raising=False)
    sub = tmp_path / "a" / "b" / "c"
    sub.mkdir(parents=True)
    prepare = tmp_path / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    prepare.parent.mkdir(parents=True)
    prepare.write_text("", encoding="utf-8")
    monkeypatch.chdir(sub)
    assert workspace.workspace_root() == tmp_path.resolve()


def test_workspace_root_legacy_layout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_ROOT", raising=False)
    legacy = tmp_path / "scripts" / "pr" / "prepare.py"
    legacy.parent.mkdir(parents=True)
    legacy.write_text("", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    assert workspace.workspace_root() == tmp_path.resolve()


def test_workspace_root_no_match_returns_start(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_ROOT", raising=False)
    isolated = tmp_path / "isolated"
    isolated.mkdir()
    # Use a fake root with no parents containing prepare.py by monkeypatching Path.cwd.
    monkeypatch.setattr(workspace.Path, "cwd", staticmethod(lambda: isolated))
    assert workspace.workspace_root() == isolated.resolve()
