"""
File: test_integrate_validate.py
Path: tests/modules/integration/test_integrate_validate.py
Role: Tests for integrate validate P0 checks.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/integration/validate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
INTEGRATION_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "integration"
if str(INTEGRATION_DIR) not in sys.path:
    sys.path.insert(0, str(INTEGRATION_DIR))

from validate import exit_code_for, run_checks


def test_integrate_validate_passes_on_kit_repo() -> None:
    results = run_checks(REPO_ROOT)
    p0_failures = [r for r in results if not r.passed and r.severity.value == "P0"]
    assert not p0_failures, "\n".join(f"{r.check_id}: {r.detail}" for r in p0_failures)
    assert exit_code_for(results) == 0


def test_missing_anchor_fails_p0(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    agent = tmp_path / ".cursor" / "agents" / "implementer.md"
    agent.write_text("# implementer\n\nNo anchor\n", encoding="utf-8")
    results = run_checks(tmp_path)
    int001 = next(r for r in results if r.check_id == "INT-001")
    assert not int001.passed
    assert exit_code_for(results) == 1


def test_orphan_registry_id_fails_p0(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    registry = tmp_path / ".cursor" / "mcp.registry.yaml.example"
    data = yaml.safe_load(registry.read_text(encoding="utf-8"))
    data["servers"]["workflow-kit"]["agents"].append("nonexistent-agent")
    registry.write_text(yaml.dump(data), encoding="utf-8")
    results = run_checks(tmp_path)
    int002 = next(r for r in results if r.check_id == "INT-002")
    assert not int002.passed
    assert "nonexistent-agent" in int002.detail


def test_invalid_github_collaboration_schema_fails_p0(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    bad = tmp_path / ".local" / "user_settings" / "github.collaboration.yaml"
    bad.write_text("version: 1\n", encoding="utf-8")
    results = run_checks(tmp_path)
    int006 = next(r for r in results if r.check_id == "INT-006")
    assert not int006.passed


def test_plugin_parity_skipped_on_consumer_profile(tmp_path: Path) -> None:
    _copy_minimal_kit(tmp_path)
    results = run_checks(tmp_path)
    int009 = next(r for r in results if r.check_id == "INT-009")
    int011 = next(r for r in results if r.check_id == "INT-011")
    assert int009.passed
    assert "consumer profile" in int009.detail
    assert int011.passed
    assert "consumer profile" in int011.detail


def _copy_minimal_kit(target: Path) -> None:
    import shutil

    for rel in (
        ".cursor/agents",
        ".cursor/mcp.registry.yaml.example",
        ".ai_infra/scripts/pr",
        ".ai_infra/scripts/integration",
        ".ai_infra/schemas",
        ".ai_infra/templates/user-settings/exemplars",
        ".ai_infra/templates/agent-integration",
        ".ai_infra/manifest.yaml",
        ".ai_infra/bootstrap.py",
        ".ai_infra/paths.py",
    ):
        src = REPO_ROOT / rel
        dst = target / rel
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    settings_dir = target / ".local" / "user_settings"
    settings_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        REPO_ROOT / ".ai_infra/templates/user-settings/exemplars/github.collaboration.yaml",
        settings_dir / "github.collaboration.yaml",
    )
    content = (settings_dir / "github.collaboration.yaml").read_text(encoding="utf-8")
    content = content.replace("Your Full Name", "Test User").replace("@yourhandle", "@testuser")
    (settings_dir / "github.collaboration.yaml").write_text(content, encoding="utf-8")
