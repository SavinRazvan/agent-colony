"""
File: test_pr_workflow_scripts.py
Path: tests/modules/pr_workflow/test_pr_workflow_scripts.py
Role: Verifies PR workflow scripts emit required actor attribution metadata.
Used By:
 - scripts/pr/prepare.py GATES (pytest -q)
Depends On:
 - scripts/pr/review.py
 - scripts/pr/prepare.py
 - scripts/pr/merge.py
 - scripts/pr/verify_publish.py
 - scripts/pr/local_workflow_paths.py
Notes:
 - Uses temporary directories to avoid mutating repository-local artifacts.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load_module(module_name: str, path: Path):
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _paths_module():
    return _load_module("local_workflow_paths", SCRIPTS_DIR / "local_workflow_paths.py")


def test_review_script_writes_actor_attribution(tmp_path: Path, monkeypatch) -> None:
    paths = _paths_module()
    module = _load_module("review_script", SCRIPTS_DIR / "review.py")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "review.py",
            "--pr",
            "123",
            "--actor",
            "Example Author",
            "--agents",
            "review-pr",
        ],
    )
    assert module.main() == 0

    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "review.md").read_text(
        encoding="utf-8"
    )
    assert "Action-By: Example Author" in content
    assert "Reviewed-By: Example Author" in content
    assert f"GitHub-User: {paths.DEFAULT_GITHUB_USER}" in content
    assert "Agent/s: review-pr" in content


def test_prepare_script_writes_actor_attribution(tmp_path: Path, monkeypatch) -> None:
    paths = _paths_module()
    module = _load_module("prepare_script", SCRIPTS_DIR / "prepare.py")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module,
        "resolve_gates",
        lambda _root=None: [["python3", "-c", "print('ok')"]],
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare.py",
            "--pr",
            "123",
            "--actor",
            "Example Author",
            "--agents",
            "review-pr | prepare-pr",
        ],
    )
    assert module.main() == 0

    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "prep.md").read_text(
        encoding="utf-8"
    )
    assert "Action-By: Example Author" in content
    assert "Prepared-By: Example Author" in content
    assert f"GitHub-User: {paths.DEFAULT_GITHUB_USER}" in content
    assert "Agent/s: review-pr | prepare-pr" in content


def test_merge_script_writes_actor_attribution(tmp_path: Path, monkeypatch) -> None:
    paths = _paths_module()
    module = _load_module("merge_script", SCRIPTS_DIR / "merge.py")

    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True, exist_ok=True)
    (wf / "review.md").write_text(
        "# Review Artifact (123)\n\n## Attribution\n- Action-By: Example Author\n",
        encoding="utf-8",
    )
    (wf / "prep.md").write_text(
        "# Prepare Artifact (123)\n\n## Attribution\n- Action-By: Example Author\n",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "_head_sha", lambda: "abc123")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge.py",
            "--pr",
            "123",
            "--actor",
            "Example Author",
            "--agents",
            "review-pr | prepare-pr | merge-pr",
        ],
    )
    assert module.main() == 0

    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "merge.md").read_text(
        encoding="utf-8"
    )
    assert "Action-By: Example Author" in content
    assert "Merged-By: Example Author" in content
    assert f"GitHub-User: {paths.DEFAULT_GITHUB_USER}" in content
    assert "Agent/s: review-pr | prepare-pr | merge-pr" in content


def test_verify_publish_script_passes_when_upstream_and_remote_exist(monkeypatch) -> None:
    module = _load_module("verify_publish_script_ok", SCRIPTS_DIR / "verify_publish.py")

    def _fake_run(cmd: list[str]):
        if cmd == ["git", "branch", "--show-current"]:
            return 0, "fix/test"
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "fix/test@{upstream}"]:
            return 0, "origin/fix/test"
        if cmd == ["git", "ls-remote", "--heads", "origin", "fix/test"]:
            return 0, "deadbeef\trefs/heads/fix/test"
        return 1, "unexpected command"

    monkeypatch.setattr(module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["verify_publish.py", "--branch", "fix/test"])
    assert module.main() == 0


def test_finalize_dry_run_exits_zero(monkeypatch) -> None:
    module = _load_module("finalize_script", SCRIPTS_DIR / "finalize.py")

    monkeypatch.setattr(module, "_current_branch", lambda: "main")
    monkeypatch.setattr(module, "_local_branch_exists", lambda _b: False)
    monkeypatch.setattr(module, "_remote_branch_exists", lambda _b: False)
    monkeypatch.setattr(
        sys,
        "argv",
        ["finalize.py", "--branch", "feature/test", "--dry-run"],
    )
    assert module.main() == 0


def test_resolve_gates_kit_dev_includes_drift_and_doc_facts() -> None:
    module = _load_module("prepare_gates", SCRIPTS_DIR / "prepare.py")
    gates = module.resolve_gates(REPO_ROOT)
    assert len(gates) == 4
    joined = " ".join(" ".join(cmd) for cmd in gates)
    assert "drift" in joined
    assert "check_doc_facts" in joined


def test_resolve_gates_consumer_universal_only(tmp_path: Path) -> None:
    module = _load_module("prepare_gates_consumer", SCRIPTS_DIR / "prepare.py")
    gates = module.resolve_gates(tmp_path)
    assert len(gates) == 2
    joined = " ".join(" ".join(cmd) for cmd in gates)
    assert "check_testing_artifacts" in joined
    assert "pytest" in joined
    assert "drift" not in joined
