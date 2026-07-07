"""
File: test_paths.py
Path: tests/modules/ai_infra/test_paths.py
Role: Tests for .ai_infra path resolution.
Used By:
 - pytest
Depends On:
 - .ai_infra/paths.py
Notes:
 - Verifies canonical .ai_infra/* paths.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_AI_INFRA = REPO_ROOT / ".ai_infra"
if str(_AI_INFRA) not in sys.path:
    sys.path.insert(0, str(_AI_INFRA))


def test_ui_local_workspace_canonical() -> None:
    from paths import ui_local_workspace

    ui = ui_local_workspace(REPO_ROOT)
    assert ui == (REPO_ROOT / ".ai_infra" / "templates" / "local-workspace").resolve()
    assert (ui / "exemplars" / "session-pointer.md").is_file()


def test_mcp_package_canonical() -> None:
    from paths import mcp_package_dir

    mcp = mcp_package_dir(REPO_ROOT)
    assert mcp == (REPO_ROOT / ".ai_infra" / "mcp_servers" / "workflow_mcp").resolve()
    assert (mcp / "server.py").is_file()


def test_workflow_mcp_import() -> None:
    from workflow_mcp.gates import load_gates

    gates = load_gates(REPO_ROOT)
    assert len(gates) == 4


def test_user_settings_templates_canonical() -> None:
    from paths import user_settings_templates

    templates = user_settings_templates(REPO_ROOT)
    assert templates == (
        REPO_ROOT / ".ai_infra" / "templates" / "user-settings" / "exemplars"
    ).resolve()
    assert (templates / "github.collaboration.yaml").is_file()


def test_docs_dir_canonical() -> None:
    from paths import docs_dir

    for name in ("governance", "operations", "roadmap", "handoff", "decisions", "architecture"):
        path = docs_dir(name, REPO_ROOT)
        assert path == (REPO_ROOT / ".ai_infra" / "docs" / name).resolve()
        assert path.is_dir()


def test_scripts_dir_canonical() -> None:
    from paths import scripts_dir

    for name in ("pr", "architecture", "install"):
        path = scripts_dir(name, REPO_ROOT)
        assert path == (REPO_ROOT / ".ai_infra" / "scripts" / name).resolve()
        assert path.is_dir()

    prepare = scripts_dir("pr", REPO_ROOT) / "prepare.py"
    assert prepare.is_file()


def test_kit_root_from_script() -> None:
    from paths import kit_root_from_script

    script = REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    assert kit_root_from_script(script) == REPO_ROOT


def test_kit_root_from_script_raises_when_no_marker(tmp_path: Path) -> None:
    from paths import kit_root_from_script

    with pytest.raises(FileNotFoundError, match="cannot infer kit root"):
        kit_root_from_script(tmp_path / "no_marker" / "script.py")


def test_kit_root_returns_repo_root() -> None:
    from paths import kit_root

    assert kit_root() == REPO_ROOT.resolve()


def test_ai_infra_dir_raises_when_missing(tmp_path: Path) -> None:
    from paths import ai_infra_dir

    with pytest.raises(FileNotFoundError, match="not found"):
        ai_infra_dir(tmp_path)


def test_ui_local_workspace_raises_when_missing(tmp_path: Path) -> None:
    from paths import ui_local_workspace

    (tmp_path / ".ai_infra").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        ui_local_workspace(tmp_path)


def test_user_settings_templates_raises_when_missing(tmp_path: Path) -> None:
    from paths import user_settings_templates

    (tmp_path / ".ai_infra").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        user_settings_templates(tmp_path)


def test_mcp_package_dir_raises_when_missing(tmp_path: Path) -> None:
    from paths import mcp_package_dir

    (tmp_path / ".ai_infra").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        mcp_package_dir(tmp_path)


def test_docs_dir_raises_when_missing(tmp_path: Path) -> None:
    from paths import docs_dir

    (tmp_path / ".ai_infra").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        docs_dir("governance", tmp_path)


def test_scripts_dir_raises_when_missing(tmp_path: Path) -> None:
    from paths import scripts_dir

    (tmp_path / ".ai_infra").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        scripts_dir("pr", tmp_path)


def test_pr_script_raises_when_missing(tmp_path: Path) -> None:
    from paths import pr_script

    (tmp_path / ".ai_infra" / "scripts" / "pr").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        pr_script("no-such-script.py", tmp_path)


def test_pr_script_resolves_existing_file() -> None:
    from paths import pr_script

    resolved = pr_script("prepare.py", REPO_ROOT)
    assert resolved.is_file()


def test_architecture_script_raises_when_missing(tmp_path: Path) -> None:
    from paths import architecture_script

    (tmp_path / ".ai_infra" / "scripts" / "architecture").mkdir(parents=True)
    with pytest.raises(FileNotFoundError, match="not found"):
        architecture_script("no-such-script.py", tmp_path)


def test_architecture_script_resolves_existing_file() -> None:
    from paths import architecture_script

    resolved = architecture_script("check_doc_facts.py", REPO_ROOT)
    assert resolved.is_file()


def test_pr_script_rel_returns_relative_path() -> None:
    from paths import pr_script_rel

    assert pr_script_rel("prepare.py") == ".ai_infra/scripts/pr/prepare.py"


def test_resolve_project_python_prefers_venv(tmp_path: Path) -> None:
    from paths import resolve_project_python

    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    venv_py = venv_bin / "python"
    venv_py.write_text("#!/bin/sh\n", encoding="utf-8")
    assert resolve_project_python(tmp_path) == str(venv_py)


def test_resolve_project_python_falls_back_to_sys_executable(tmp_path: Path) -> None:
    from paths import resolve_project_python

    assert resolve_project_python(tmp_path) == sys.executable
