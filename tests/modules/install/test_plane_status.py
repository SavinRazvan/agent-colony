"""
File: test_plane_status.py
Path: tests/modules/install/test_plane_status.py
Role: Tests for three-plane readiness assessment.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/plane_status.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PLANE_STATUS_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "plane_status.py"


def _load_plane_status():
    spec = importlib.util.spec_from_file_location("plane_status", PLANE_STATUS_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["plane_status"] = module
    spec.loader.exec_module(module)
    return module


def test_kit_repo_planes_ready() -> None:
    plane_status = _load_plane_status()
    status = plane_status.assess_planes(REPO_ROOT, profile="with_mcp")
    assert status.all_ready
    assert not status.missing


def test_empty_dir_planes_missing(tmp_path: Path) -> None:
    plane_status = _load_plane_status()
    status = plane_status.assess_planes(tmp_path)
    assert not status.all_ready


def test_assess_planes_require_venv_missing_runtime(tmp_path: Path) -> None:
    plane_status = _load_plane_status()
    # Minimal path layout so only venv gate fails when require_venv=True.
    for rel in (
        ".cursor/agents/implementer.md",
        ".ai_infra/scripts/pr/prepare.py",
        ".local/index-and-planning/current/session-pointer.md",
        "AGENTS.md",
        ".ai_infra/bootstrap.py",
        ".ai_infra/paths.py",
        ".ai_infra/manifest.yaml",
        "agent_colony/__main__.py",
        ".ai_infra/install/agent_colony/cli.py",
        ".ai_infra/scripts/architecture/check_governance_consistency.py",
        ".ai_infra/mcp_servers/agent_colony_mcp/server.py",
        "requirements-mcp.txt",
    ):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("x\n", encoding="utf-8")
    (tmp_path / ".ai_infra" / "install-contract.json").write_text(
        (REPO_ROOT / ".ai_infra" / "install-contract.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    ok = plane_status.assess_planes(tmp_path, profile="with_mcp", require_venv=False)
    assert ok.runtime is True
    bad = plane_status.assess_planes(tmp_path, profile="with_mcp", require_venv=True)
    assert bad.runtime is False
    assert ".venv/bin/python" in bad.missing
    (tmp_path / ".venv" / "bin").mkdir(parents=True)
    (tmp_path / ".venv" / "bin" / "python").write_text("", encoding="utf-8")
    good = plane_status.assess_planes(tmp_path, profile="with_mcp", require_venv=True)
    assert good.runtime is True
    assert good.all_ready


def test_plane_for_path_tests_prefix() -> None:
    plane_status = _load_plane_status()
    assert plane_status._plane_for_path("tests/modules/foo.py") == "infrastructure"


def test_plane_for_path_fallback_infrastructure() -> None:
    plane_status = _load_plane_status()
    assert plane_status._plane_for_path("some/other/path.txt") == "infrastructure"


def test_format_plane_report_truncates_missing_over_twelve() -> None:
    plane_status = _load_plane_status()
    status = plane_status.PlaneStatus(
        cursor_contract=False,
        infrastructure=False,
        runtime=False,
        missing=tuple(f"path-{i}" for i in range(15)),
    )
    report = plane_status.format_plane_report(status)
    assert "... +3 more" in report
