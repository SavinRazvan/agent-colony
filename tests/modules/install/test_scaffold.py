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
    assert (target / ".local" / "index-and-planning" / "current" / "session-pointer.md").is_file()
    assert not (target / ".cursor" / "agents" / "workflow-intelligence-mapper.md").exists()
    assert not (target / ".cursor" / "rules" / mod.ADAPTER_WALL_RULE).exists()
    assert not (target / "examples").exists()
    assert (target / "tests" / "modules" / "smoke" / "test_kit_installed.py").is_file()
    assert not (target / "tests" / "modules" / "install" / "test_scaffold.py").exists()


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
