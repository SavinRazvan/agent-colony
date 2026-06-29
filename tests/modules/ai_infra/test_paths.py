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
    assert len(gates) == 2


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
