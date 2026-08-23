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
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAFFOLD_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"


def _load_scaffold():
    module_name = f"scaffold_test_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, SCAFFOLD_PATH)
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
    assert "SKIP consumer smoke test file" in joined
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
    assert not (target / "tests" / "modules" / "smoke" / "test_kit_installed.py").exists()
    assert not (target / "tests" / "modules" / "install" / "test_scaffold.py").exists()


def test_scaffold_keep_smoke_test_opt_in(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT, keep_smoke_test=True)
    smoke = target / "tests" / "modules" / "smoke" / "test_kit_installed.py"
    assert smoke.is_file()
    assert "workflow-artifacts/drift" in smoke.read_text(encoding="utf-8")


def test_scaffold_writes_runtime_gitignore_and_starter(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    gi = (target / ".gitignore").read_text(encoding="utf-8")
    assert ".local/" in gi
    assert ".venv/" in gi
    assert ".cursor/mcp.user.json" in gi
    tracker = (
        target / ".local" / "index-and-planning" / "current" / "work-tracker.md"
    ).read_text(encoding="utf-8")
    assert "STARTER-001" in tracker


def test_scaffold_creates_workflow_artifact_buckets(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    lwp = mod._load_local_workflow_paths(REPO_ROOT)
    for bucket in lwp.ARTIFACT_STUB_BUCKET_NAMES:
        assert (target / ".local" / "workflow-artifacts" / bucket).is_dir()
        assert (target / ".local" / "workflow-artifacts" / bucket / "README.md").is_file()


def test_scaffold_creates_local_canvas_plan_buckets(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    lwp = mod._load_local_workflow_paths(REPO_ROOT)
    assert (target / lwp.LOCAL_CANVASES_DIR).is_dir()
    assert (target / lwp.LOCAL_PLANS_DIR).is_dir()
    assert (target / lwp.LOCAL_CANVASES_INDEX).is_file()
    assert (target / lwp.LOCAL_PLANS_INDEX).is_file()
    assert (target / lwp.LOCAL_CANVASES_DIR / "README.md").is_file()
    assert (target / lwp.LOCAL_PLANS_DIR / "README.md").is_file()


def test_scaffold_creates_agents_md(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    agents = target / "AGENTS.md"
    assert agents.is_file()
    text = agents.read_text(encoding="utf-8")
    assert "local-workspace-layout" in text
    assert "Artifact tiers" in text or "artifact tiers" in text.lower()


def test_scaffold_does_not_create_agents_control_center(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    assert not (target / ".local" / "agents-control-center").exists()


def test_scaffold_removes_preexisting_agents_control_center(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    acc = target / ".local" / "agents-control-center" / "dashboards"
    acc.mkdir(parents=True)
    (acc / "index.html").write_text("<!-- stale -->\n", encoding="utf-8")
    mod.scaffold(target, REPO_ROOT)
    assert not (target / ".local" / "agents-control-center").exists()
    assert (target / ".local" / "index-and-planning" / "current" / "plan.md").is_file()


def test_remove_deprecated_agents_control_center_dry_run(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    acc = target / ".local" / "agents-control-center"
    acc.mkdir(parents=True)
    log = mod.remove_deprecated_agents_control_center(target, dry_run=True)
    assert acc.is_dir()
    assert any("DRY-RUN rmtree" in line for line in log)


def test_scaffold_artifact_tab_placeholders(tmp_path: Path) -> None:
    mod = _load_scaffold()
    ui_root = REPO_ROOT / ".ai_infra" / "templates" / "local-workspace"
    target = tmp_path / "project"
    (target / ".local" / "workflow-artifacts" / "pr").mkdir(parents=True)
    log: list[str] = []
    mod._scaffold_artifact_readme_stubs(ui_root, target, False, log, ("pr", "alignment", "drift"))
    assert (target / ".local" / "workflow-artifacts" / "pr" / "review.md").is_file()
    assert (target / ".local" / "workflow-artifacts" / "pr" / "finalize.md").is_file()
    assert (target / ".local" / "workflow-artifacts" / "alignment" / "alignment-audit.md").is_file()
    assert (target / ".local" / "workflow-artifacts" / "drift" / "drift-audit.md").is_file()
    assert any("review.md" in line for line in log)


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


def test_scaffold_reactivate_preserves_user_settings(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    github = target / ".local" / "user_settings" / "github.collaboration.yaml"
    github.write_text("owner:\n  display_name: Custom User\n", encoding="utf-8")
    mod.scaffold(target, REPO_ROOT)
    assert "Custom User" in github.read_text(encoding="utf-8")


def test_scaffold_does_not_ship_ci_kit_dev_fixtures(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    ci = target / ".ai_infra" / "templates" / "local-workspace" / "ci"
    assert not ci.exists(), "ci/kit-dev fixtures must not ship to consumer installs"


def test_scaffold_creates_user_settings_worksheets(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    settings = target / ".local" / "user_settings"
    assert (settings / "github.collaboration.yaml").is_file()
    assert (settings / "mcp.agents.yaml").is_file()
    assert (settings / "README.md").is_file()
    overlay = settings / "board-shell.schema.yaml"
    assert overlay.is_file(), "consumer activate should seed minimal board-shell overlay"
    assert "minimal-two-view" in overlay.read_text(encoding="utf-8")
    github = (settings / "github.collaboration.yaml").read_text(encoding="utf-8")
    assert "owner:" in github
    assert "commit_provenance:" in github


def test_scaffold_skips_board_shell_overlay_on_kit_dev(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "kit-dev"
    mod.scaffold(target, REPO_ROOT, with_tests=True)
    overlay = target / ".local" / "user_settings" / "board-shell.schema.yaml"
    assert not overlay.is_file()
    assert (target / "tests" / "modules" / "install" / "test_scaffold.py").is_file()


def test_scaffold_rejects_same_source_and_target() -> None:
    mod = _load_scaffold()
    with pytest.raises(ValueError, match="must differ"):
        mod.scaffold(REPO_ROOT, REPO_ROOT)


def test_scaffold_kit_version_from_source_when_run_from_consumer_context(
    tmp_path: Path,
) -> None:
    """Consumer update runs scaffold.py from target; stamp must use source manifest."""
    target = tmp_path / "consumer"
    shutil.copytree(REPO_ROOT / ".ai_infra", target / ".ai_infra")
    stale_manifest = yaml.safe_load(
        (REPO_ROOT / ".ai_infra" / "manifest.yaml").read_text(encoding="utf-8")
    )
    stale_manifest["kit_version"] = "0.1.0"
    (target / ".ai_infra" / "manifest.yaml").write_text(
        yaml.safe_dump(stale_manifest, sort_keys=False),
        encoding="utf-8",
    )
    (target / ".ai_infra" / ".kit-version").write_text("0.1.0\n", encoding="utf-8")

    script = target / ".ai_infra" / "scripts" / "install" / "scaffold.py"
    proc = subprocess.run(
        [
            sys.executable,
            str(script),
            "--target",
            str(target),
            "--source",
            str(REPO_ROOT),
            "--profile",
            "with_mcp",
            "--with-mcp-json",
        ],
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr or proc.stdout

    expected = yaml.safe_load(
        (REPO_ROOT / ".ai_infra" / "manifest.yaml").read_text(encoding="utf-8")
    )["kit_version"]
    stamp = (target / ".ai_infra" / ".kit-version").read_text(encoding="utf-8").strip()
    assert stamp == expected
    assert stamp != "0.1.0"


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


def test_sync_kit_ui_templates_same_source_target_returns_empty() -> None:
    mod = _load_scaffold()
    assert mod.sync_kit_ui_templates(REPO_ROOT, REPO_ROOT) == []


def test_sync_kit_ui_templates_no_ai_infra_returns_empty(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "bare"
    target.mkdir()
    assert mod.sync_kit_ui_templates(REPO_ROOT, target) == []


def test_sync_kit_ui_templates_is_noop_after_icc_removal(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    assert mod.sync_kit_ui_templates(REPO_ROOT, target) == []
    assert mod.sync_kit_ui_templates(REPO_ROOT, target, dry_run=True) == []


def test_sync_activate_runtime_same_source_target_returns_empty() -> None:
    mod = _load_scaffold()
    assert mod.sync_activate_runtime(REPO_ROOT, REPO_ROOT) == []


def test_sync_activate_runtime_no_ai_src_returns_empty(tmp_path: Path) -> None:
    mod = _load_scaffold()
    source = tmp_path / "no-ai-infra"
    source.mkdir()
    target = tmp_path / "project"
    mod.scaffold(target, REPO_ROOT)
    assert mod.sync_activate_runtime(source, target) == []
