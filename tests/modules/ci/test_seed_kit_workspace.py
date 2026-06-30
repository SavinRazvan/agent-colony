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

REPO_ROOT = Path(__file__).resolve().parents[3]
CI_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "ci"
if str(CI_DIR) not in sys.path:
    sys.path.insert(0, str(CI_DIR))

from seed_kit_workspace import seed_kit_workspace


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
    pr_scripts = REPO_ROOT / ".ai_infra/scripts/pr"
    pr_dst = tmp_path / ".ai_infra/scripts/pr"
    pr_dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(pr_scripts / "local_workflow_paths.py", pr_dst / "local_workflow_paths.py")

    seed_kit_workspace(tmp_path)

    for bucket in (
        "pr",
        "alignment",
        "drift",
        "enterprise-architecture-audit",
        "release",
        "audit",
    ):
        assert (tmp_path / ".local/workflow-artifacts" / bucket).is_dir()
    assert (tmp_path / ".local/workflow-artifacts/drift/README.md").is_file()


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
