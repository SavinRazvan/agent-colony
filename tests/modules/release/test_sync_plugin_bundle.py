"""
File: test_sync_plugin_bundle.py
Path: tests/modules/release/test_sync_plugin_bundle.py
Role: Tests for plugin bundle sync and parity check.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/release/sync_plugin_bundle.py
Notes:
 - Uses temporary output dirs; does not require the committed agents/rules/skills tree.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SYNC_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "release" / "sync_plugin_bundle.py"


def _load_sync():
    spec = importlib.util.spec_from_file_location("sync_plugin_bundle", SYNC_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["sync_plugin_bundle"] = module
    spec.loader.exec_module(module)
    return module


def test_sync_builds_plugin_and_payload(tmp_path: Path) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    assert (plugin_dir / "agents" / "implementer.md").is_file()
    assert (plugin_dir / "skills" / "workflow-activate" / "SKILL.md").is_file()
    assert (plugin_dir / "skills" / "review-pr" / "SKILL.md").is_file()
    assert (payload_dir / ".ai_infra" / "scripts" / "pr" / "prepare.py").is_file()
    assert (payload_dir / "cursor_workflow" / "__main__.py").is_file()
    assert (payload_dir / ".cursor" / "agents" / "implementer.md").is_file()
    assert (payload_dir / "LICENSE").is_file()
    assert (payload_dir / "NOTICE").is_file()


def test_check_bundle_passes_after_sync(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    monkeypatch.setattr(mod, "PLUGIN_DIR", plugin_dir)
    monkeypatch.setattr(mod, "PAYLOAD_DIR", payload_dir)

    errors = mod.check_bundle("with_mcp")
    assert errors == []


def test_payload_skills_do_not_overlap_agents_skills(tmp_path: Path) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    cursor_names = {
        p.name for p in (payload_dir / ".cursor" / "skills").iterdir() if p.is_dir()
    }
    agents_names = {
        p.name for p in (payload_dir / ".agents" / "skills").iterdir() if p.is_dir()
    }
    overlap = sorted(cursor_names & agents_names)
    assert overlap == [], f"payload must not duplicate skill folders: {overlap}"
    assert (plugin_dir / "skills" / "review-pr" / "SKILL.md").is_file()
    assert not (payload_dir / ".cursor" / "skills" / "review-pr").exists()


def test_payload_install_verify_green(tmp_path: Path) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    target = tmp_path / "consumer"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    scaffold_path = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"
    spec = importlib.util.spec_from_file_location("scaffold", scaffold_path)
    assert spec is not None and spec.loader is not None
    scaffold = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scaffold)

    log = scaffold.scaffold(
        target,
        payload_dir,
        profile="with_mcp",
        with_venv=True,
        with_mcp_json=True,
        verify=True,
    )
    assert "VERIFY PASS: all gates green" in "\n".join(log)


def test_payload_install_dry_run(tmp_path: Path) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    target = tmp_path / "consumer"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    scaffold_path = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"
    spec = importlib.util.spec_from_file_location("scaffold", scaffold_path)
    assert spec is not None and spec.loader is not None
    scaffold = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(scaffold)

    log = scaffold.scaffold(
        target,
        payload_dir,
        profile="with_mcp",
        dry_run=True,
        with_mcp_json=True,
    )
    joined = "\n".join(log)
    assert ".ai_infra" in joined
    assert ".cursor" in joined
    assert "SCAFFOLD DONE" in joined


def test_sync_payload_excludes_maintainer_only_fixtures(tmp_path: Path) -> None:
    """Consumer payload must not ship kit-dev-only ci/ fixtures or maintainer docs.

    Covers AA-test-001: exclusion filters in consumer_bundle_paths.py
    (ignore_local_workspace_ci, ignore_operations_maintainer) were only
    covered indirectly by scaffold/purity tests; assert the concrete
    excluded paths directly here.
    """
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    payload_dir = tmp_path / "payload"
    mod.sync_plugin_surface(plugin_dir)
    mod.sync_payload(payload_dir, plugin_dir, profile="with_mcp")

    local_workspace = payload_dir / ".ai_infra" / "templates" / "local-workspace"
    assert local_workspace.is_dir()
    assert not (local_workspace / "ci").exists(), (
        "kit-dev-only ci/ fixtures must not ship to consumer payload"
    )

    operations = payload_dir / ".ai_infra" / "docs" / "operations"
    assert operations.is_dir()
    assert not (operations / "documentation-maintenance-checklist.md").exists(), (
        "maintainer-only documentation-maintenance-checklist.md must not ship to consumer payload"
    )


def test_plugin_canonical_skills_not_overwritten_by_stubs(tmp_path: Path) -> None:
    mod = _load_sync()
    plugin_dir = tmp_path / "plugin"
    mod.sync_plugin_surface(plugin_dir)

    enterprise = (plugin_dir / "skills" / "auditor-protocol" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "Evidence contract" in enterprise
    assert len(enterprise.splitlines()) > 200

    orchestration = (plugin_dir / "skills" / "audit-orchestration" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert "verify-all" in orchestration or "auditor" in orchestration

    drift = (plugin_dir / "skills" / "drift-audit" / "SKILL.md").read_text(encoding="utf-8")
    assert "drift validate" in drift.lower()

    assert (plugin_dir / "skills" / "review-pr" / "SKILL.md").is_file()
    assert (plugin_dir / "skills" / "workflow-activate" / "SKILL.md").is_file()
    assert (plugin_dir / "skills" / "pr-workflow" / "SKILL.md").is_file()
