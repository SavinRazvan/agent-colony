"""
File: test_seed_kit_workspace.py
Path: tests/modules/ci/test_seed_kit_workspace.py
Role: Tests for CI workspace seed script.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/ci/seed_kit_workspace.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "ci"
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

import seed_kit_workspace as skw
from seed_kit_workspace import seed_kit_workspace


def _import_local_workflow_paths_for_test(root: Path):
    pr_scripts = root / ".ai_infra" / "scripts" / "pr"
    pr_str = str(pr_scripts)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import local_workflow_paths

    return local_workflow_paths


def _copy_ci_fixture_tree(tmp_path: Path) -> None:
    import shutil

    kit_dev = REPO_ROOT / ".ai_infra/templates/local-workspace/ci/kit-dev"
    shutil.copytree(
        kit_dev,
        tmp_path / ".ai_infra/templates/local-workspace/ci/kit-dev",
    )
    pages = REPO_ROOT / ".ai_infra/templates/local-workspace/pages.json"
    pages_dst = tmp_path / ".ai_infra/templates/local-workspace/pages.json"
    pages_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pages, pages_dst)
    pr_scripts = REPO_ROOT / ".ai_infra/scripts/pr"
    pr_dst = tmp_path / ".ai_infra/scripts/pr"
    pr_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pr_scripts / "local_workflow_paths.py", pr_dst / "local_workflow_paths.py")


def test_seed_kit_workspace_creates_planning_artifacts(tmp_path: Path) -> None:
    _copy_ci_fixture_tree(tmp_path)
    seed_kit_workspace(tmp_path)
    current = tmp_path / ".local/index-and-planning/current"
    assert current.is_dir()
    assert (current / "test-plan.md").is_file()
    assert (current / "test-index.md").is_file()
    assert "Module:" in (current / "test-index.md").read_text(encoding="utf-8")
    assert (tmp_path / ".local/user_settings/github.collaboration.yaml").is_file()


def test_seed_kit_workspace_creates_artifact_buckets(tmp_path: Path) -> None:
    _copy_ci_fixture_tree(tmp_path)
    stubs_src = REPO_ROOT / ".ai_infra/templates/local-workspace/artifact-stubs"
    stubs_dst = tmp_path / ".ai_infra/templates/local-workspace/artifact-stubs"
    shutil.copytree(stubs_src, stubs_dst)
    ui_src = REPO_ROOT / ".ai_infra/templates/local-workspace"
    ui_dst = tmp_path / ".ai_infra/templates/local-workspace"
    for name in (
        "index.html",
        "implementation-control-center.html",
        "site-nav.js",
        "local-shell.css",
        "local-markdown.js",
    ):
        shutil.copy2(ui_src / name, ui_dst / name)
    pr_scripts = REPO_ROOT / ".ai_infra/scripts/pr"
    pr_dst = tmp_path / ".ai_infra/scripts/pr"
    pr_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pr_scripts / "local_workflow_paths.py", pr_dst / "local_workflow_paths.py")

    seed_kit_workspace(tmp_path)

    lwp = _import_local_workflow_paths_for_test(tmp_path)
    for bucket in lwp.ARTIFACT_STUB_BUCKET_NAMES:
        assert (tmp_path / ".local" / "workflow-artifacts" / bucket).is_dir()
        assert (tmp_path / ".local" / "workflow-artifacts" / bucket / "README.md").is_file()

    dash = tmp_path / ".local" / "agents-control-center" / "dashboards"
    assert (dash / "index.html").is_file()
    assert (dash / "local-markdown.js").is_file()


def test_seed_passes_check_testing_artifacts(tmp_path: Path) -> None:
    import shutil
    import subprocess

    for rel in (
        ".ai_infra/templates/local-workspace/ci/kit-dev",
        ".ai_infra/templates/local-workspace/pages.json",
        ".ai_infra/scripts/pr/check_testing_artifacts.py",
        "tests/modules",
    ):
        src = REPO_ROOT / rel
        dst = tmp_path / rel
        if src.is_dir():
            shutil.copytree(src, dst)
        elif src.is_file():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    seed_kit_workspace(tmp_path)
    proc = subprocess.run(
        [sys.executable, str(tmp_path / ".ai_infra/scripts/pr/check_testing_artifacts.py")],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_fixture_root_missing_profile_raises(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="missing CI fixtures"):
        skw.fixture_root(tmp_path, "no-such-profile")


def test_seed_kit_workspace_missing_fixture_tracker_raises(tmp_path: Path) -> None:
    _copy_ci_fixture_tree(tmp_path)
    fixtures = tmp_path / ".ai_infra/templates/local-workspace/ci/kit-dev"
    (fixtures / "test-plan.md").unlink()
    with pytest.raises(FileNotFoundError, match="missing fixture tracker"):
        seed_kit_workspace(tmp_path)


def test_seed_kit_workspace_skips_existing_readme_stub(tmp_path: Path) -> None:
    _copy_ci_fixture_tree(tmp_path)
    stubs_src = REPO_ROOT / ".ai_infra/templates/local-workspace/artifact-stubs"
    stubs_dst = tmp_path / ".ai_infra/templates/local-workspace/artifact-stubs"
    shutil.copytree(stubs_src, stubs_dst)
    pr_scripts = REPO_ROOT / ".ai_infra/scripts/pr"
    pr_dst = tmp_path / ".ai_infra/scripts/pr"
    pr_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pr_scripts / "local_workflow_paths.py", pr_dst / "local_workflow_paths.py")

    lwp = _import_local_workflow_paths_for_test(tmp_path)
    bucket = lwp.ARTIFACT_STUB_BUCKET_NAMES[0]
    existing = tmp_path / ".local" / "workflow-artifacts" / bucket / "README.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("pre-existing\n", encoding="utf-8")

    seed_kit_workspace(tmp_path)
    assert existing.read_text(encoding="utf-8") == "pre-existing\n"


def test_seed_kit_workspace_copies_coverage_exemplar(tmp_path: Path) -> None:
    _copy_ci_fixture_tree(tmp_path)
    exemplars_src = REPO_ROOT / ".ai_infra/templates/local-workspace/exemplars"
    exemplars_dst = tmp_path / ".ai_infra/templates/local-workspace/exemplars"
    shutil.copytree(exemplars_src, exemplars_dst)

    seed_kit_workspace(tmp_path)

    coverage_dst = tmp_path / ".local/index-and-planning/current/coverage-index.md"
    assert coverage_dst.is_file()


def test_main_success(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _copy_ci_fixture_tree(tmp_path)
    code = skw.main(["--directory", str(tmp_path), "--profile", "kit-dev"])
    assert code == 0
    captured = capsys.readouterr()
    assert "seed_kit_workspace: PASS profile=kit-dev" in captured.out


def test_main_missing_fixtures_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = skw.main(["--directory", str(tmp_path), "--profile", "does-not-exist"])
    assert code == 1
    captured = capsys.readouterr()
    assert "seed_kit_workspace: FAIL" in captured.out


def test_main_guard_via_runpy(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    _copy_ci_fixture_tree(tmp_path)
    monkeypatch.setattr(sys, "argv", ["seed_kit_workspace.py", "--directory", str(tmp_path)])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(
            str(REPO_ROOT / ".ai_infra" / "scripts" / "ci" / "seed_kit_workspace.py"),
            run_name="__main__",
        )
    assert exc_info.value.code == 0
