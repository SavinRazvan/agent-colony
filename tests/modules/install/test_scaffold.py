"""
File: test_scaffold.py
Path: tests/modules/install/test_scaffold.py
Role: Tests for manifest-driven install scaffold.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/install/scaffold.py
Notes:
 - Uses temporary directories; does not modify kit root.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold", SCAFFOLD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_scaffold_dry_run_lists_copies(tmp_path: Path) -> None:
    mod = _load_scaffold()
    log = mod.scaffold(tmp_path / "out", REPO_ROOT, dry_run=True)
    joined = "\n".join(log)
    assert ".ai_infra" in joined
    assert ".cursor" in joined
    assert "session-pointer.md" in joined
    assert "project.config.yaml.example" in joined
    assert "minimal smoke" in joined
    assert "examples" not in joined


def test_scaffold_creates_core_layout(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    assert (target / ".cursor" / "agents" / "implementer.md").is_file()
    assert (target / ".ai_infra" / "scripts" / "pr" / "prepare.py").is_file()
    assert (target / ".ai_infra" / "scripts" / "install" / "scaffold.py").is_file()
    assert (target / ".local" / "index-and-planning" / "current" / "session-pointer.md").is_file()
    assert not (target / ".cursor" / "agents" / "workflow-intelligence-mapper.md").exists()
    assert not (target / ".cursor" / "rules" / mod.ADAPTER_WALL_RULE).exists()
    assert not (target / "examples").exists()
    assert (target / "tests" / "modules" / "smoke" / "test_kit_installed.py").is_file()
    assert not (target / "tests" / "modules" / "install" / "test_scaffold.py").exists()
    smoke = (target / "tests" / "modules" / "smoke" / "test_kit_installed.py").read_text(
        encoding="utf-8"
    )
    assert "workflow-artifacts/drift" in smoke


def test_scaffold_creates_workflow_artifact_buckets(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    lwp = mod._load_local_workflow_paths(REPO_ROOT)
    for bucket in lwp.ARTIFACT_STUB_BUCKET_NAMES:
        assert (target / ".local" / "workflow-artifacts" / bucket).is_dir()
        assert (target / ".local" / "workflow-artifacts" / bucket / "README.md").is_file()


def test_scaffold_creates_agents_md(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    agents = target / "AGENTS.md"
    assert agents.is_file()
    text = agents.read_text(encoding="utf-8")
    assert "local-workspace-layout" in text
    assert "Artifact tiers" in text or "artifact tiers" in text.lower()


def test_scaffold_creates_dashboards(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    dash = target / ".local" / "agents-control-center" / "dashboards"
    assert (dash / "index.html").is_file()
    assert (dash / "implementation-control-center.html").is_file()
    assert (dash / "site-nav.js").is_file()
    assert (dash / "local-shell.css").is_file()


def test_scaffold_reactivate_preserves_trackers(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    plan = target / ".local" / "index-and-planning" / "current" / "plan.md"
    plan.write_text("# Custom plan\n\nLive slice content.\n", encoding="utf-8")
    agents = target / "AGENTS.md"
    agents.write_text("# Custom AGENTS\n", encoding="utf-8")
    mod.scaffold(target, REPO_ROOT)
    assert "Custom plan" in plan.read_text(encoding="utf-8")
    assert "Custom AGENTS" in agents.read_text(encoding="utf-8")


def test_scaffold_creates_tracker_extras(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    current = target / ".local" / "index-and-planning" / "current"
    history = target / ".local" / "index-and-planning" / "history"
    assert (current / "coverage-index.md").is_file()
    assert (history / "updates-log.md").is_file()


def test_scaffold_pages_json_includes_artifact_tabs(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    pages = json.loads(
        (target / ".local" / "agents-control-center" / "config" / "pages.json").read_text(
            encoding="utf-8"
        )
    )
    page_ids = {page["id"] for page in pages["pages"]}
    assert {"pr-review", "drift-audit", "ea-audit"}.issubset(page_ids)


def test_scaffold_creates_user_settings_worksheets(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    settings = target / ".local" / "user_settings"
    assert (settings / "github.collaboration.yaml").is_file()
    assert (settings / "mcp.agents.yaml").is_file()
    assert (settings / "README.md").is_file()
    github = (settings / "github.collaboration.yaml").read_text(encoding="utf-8")
    assert "owner:" in github
    assert "commit_provenance:" in github


def test_scaffold_rejects_same_source_and_target() -> None:
    mod = _load_scaffold()
    with pytest.raises(ValueError, match="must differ"):
        mod.scaffold(REPO_ROOT, REPO_ROOT)


def test_scaffold_copies_project_config_example(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    example = target / ".ai_infra" / "project.config.yaml.example"
    assert example.is_file()
    text = example.read_text(encoding="utf-8")
    assert "gates:" in text
    assert "prepare.py" in text


def test_sanity_check_passes_on_fresh_scaffold(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    log: list[str] = []
    errors = mod._sanity_check(target, log, with_tests=False)
    assert errors == []


def test_sanity_check_rejects_full_kit_tests_tree(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT, with_tests=True)
    log: list[str] = []
    errors = mod._sanity_check(target, log, with_tests=False)
    assert any("full kit tests tree" in err for err in errors)
