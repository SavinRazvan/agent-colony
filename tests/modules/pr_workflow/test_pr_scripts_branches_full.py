"""
File: test_pr_scripts_branches_full.py
Path: tests/modules/pr_workflow/test_pr_scripts_branches_full.py
Role: Fills branch-coverage gaps left by test_pr_workflow_scripts.py for
      merge.py, review.py, verify_publish.py, and prepare.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/{merge,review,verify_publish,prepare}.py
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


@contextmanager
def _without_path(entry: str) -> Iterator[None]:
    present = entry in sys.path
    if present:
        sys.path.remove(entry)
    try:
        yield
    finally:
        if entry not in sys.path:
            sys.path.insert(0, entry)


def _load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS_DIR / filename)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# merge.py
# ---------------------------------------------------------------------------


def test_merge_head_sha_real() -> None:
    module = _load_module("merge_full_1", "merge.py")
    sha = module._head_sha()
    assert isinstance(sha, str) and sha


def test_merge_current_branch_real() -> None:
    module = _load_module("merge_full_2", "merge.py")
    branch = module._current_branch()
    assert isinstance(branch, str) and branch


def test_artifact_matches_pr_missing_file(tmp_path: Path) -> None:
    module = _load_module("merge_full_3", "merge.py")
    ok, detail = module._artifact_matches_pr(tmp_path / "missing.md", "123")
    assert ok is False
    assert "missing" in detail


def test_artifact_matches_pr_mismatch(tmp_path: Path) -> None:
    module = _load_module("merge_full_4", "merge.py")
    path = tmp_path / "review.md"
    path.write_text("# Review Artifact (999)\n", encoding="utf-8")
    ok, detail = module._artifact_matches_pr(path, "123")
    assert ok is False
    assert "stale or mismatched" in detail


def test_artifact_matches_pr_os_error(tmp_path: Path) -> None:
    module = _load_module("merge_full_5", "merge.py")
    directory_as_file = tmp_path / "a-directory"
    directory_as_file.mkdir()
    ok, detail = module._artifact_matches_pr(directory_as_file, "123")
    assert ok is False
    assert "unable to read" in detail


def test_prep_status_blocks_merge_not_ready(tmp_path: Path) -> None:
    module = _load_module("merge_prep_not_ready", "merge.py")
    path = tmp_path / "prep.md"
    path.write_text(
        "# Prepare Artifact (123)\n\n## Status\n- NOT READY\n",
        encoding="utf-8",
    )
    ok, detail = module._prep_status_blocks_merge(path)
    assert ok is False
    assert "NOT READY" in detail


def test_prep_status_blocks_merge_skip_without_rationale(tmp_path: Path) -> None:
    module = _load_module("merge_prep_skip_no_rationale", "merge.py")
    path = tmp_path / "prep.md"
    path.write_text(
        "# Prepare Artifact (123)\n\n"
        "## Gate Results\n- gates: externally verified by agent\n\n"
        "## Status\n- PR is ready for /merge-pr\n",
        encoding="utf-8",
    )
    ok, detail = module._prep_status_blocks_merge(path)
    assert ok is False
    assert "Skip-Gates-Rationale" in detail


def test_prep_status_blocks_merge_skip_with_rationale(tmp_path: Path) -> None:
    module = _load_module("merge_prep_skip_ok", "merge.py")
    path = tmp_path / "prep.md"
    path.write_text(
        "# Prepare Artifact (123)\n\n"
        "## Gate Results\n- gates: externally verified by agent\n"
        "- Skip-Gates-Rationale: same SHA already ran resolve_gates\n"
        "- Externally-Verified-By: Test User\n\n"
        "## Status\n- PR is ready for /merge-pr\n",
        encoding="utf-8",
    )
    ok, detail = module._prep_status_blocks_merge(path)
    assert ok is True
    assert detail == "ok"


def test_prep_status_blocks_merge_missing_file(tmp_path: Path) -> None:
    module = _load_module("merge_prep_missing", "merge.py")
    ok, detail = module._prep_status_blocks_merge(tmp_path / "missing.md")
    assert ok is True
    assert detail == "ok"


def test_merge_main_attribution_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("merge_full_6", "merge.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module, "resolve_pr_attribution", lambda **kw: (_ for _ in ()).throw(ValueError("bad settings"))
    )
    monkeypatch.setattr(sys, "argv", ["merge.py", "--pr", "123", "--actor", "A", "--agents", "review-pr"])
    assert module.main() == 2


def test_merge_main_missing_review_and_prep(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("merge_full_7", "merge.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["merge.py", "--pr", "123", "--actor", "A", "--agents", "review-pr"])
    assert module.main() == 1


def test_merge_main_arch_impacting_missing_alignment(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("merge_full_8", "merge.py")
    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True)
    (wf / "review.md").write_text("# Review Artifact (123)\n", encoding="utf-8")
    (wf / "prep.md").write_text("# Prepare Artifact (123)\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["merge.py", "--pr", "123", "--actor", "A", "--agents", "review-pr", "--arch-impacting"],
    )
    assert module.main() == 1


def test_merge_main_check_only_pass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("merge_full_9", "merge.py")
    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True)
    (wf / "review.md").write_text("# Review Artifact (123)\n", encoding="utf-8")
    (wf / "prep.md").write_text("# Prepare Artifact (123)\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["merge.py", "--pr", "123", "--actor", "A", "--agents", "review-pr", "--check-only"],
    )
    assert module.main() == 0
    assert not (wf / "merge.md").exists()


# ---------------------------------------------------------------------------
# review.py
# ---------------------------------------------------------------------------


def test_review_main_attribution_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("review_full_1", "review.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module, "resolve_pr_attribution", lambda **kw: (_ for _ in ()).throw(ValueError("bad settings"))
    )
    monkeypatch.setattr(sys, "argv", ["review.py", "--pr", "123", "--actor", "A", "--agents", "review-pr"])
    assert module.main() == 2


def test_review_main_no_overwrite_skips_existing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("review_full_2", "review.py")
    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True)
    existing = wf / "review.md"
    existing.write_text("existing content\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        ["review.py", "--pr", "123", "--actor", "A", "--agents", "review-pr", "--no-overwrite"],
    )
    assert module.main() == 0
    assert existing.read_text(encoding="utf-8") == "existing content\n"


# ---------------------------------------------------------------------------
# verify_publish.py
# ---------------------------------------------------------------------------


def test_verify_publish_run_real() -> None:
    module = _load_module("verify_publish_full_1", "verify_publish.py")
    code, out = module._run(["git", "rev-parse", "--is-inside-work-tree"])
    assert code == 0
    assert out == "true"


def test_verify_publish_no_branch_arg_and_cannot_determine(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("verify_publish_full_2", "verify_publish.py")
    monkeypatch.setattr(module, "_run", lambda cmd: (1, "detached HEAD"))
    monkeypatch.setattr(sys, "argv", ["verify_publish.py"])
    assert module.main() == 1


def test_verify_publish_branch_whitespace_only_after_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("verify_publish_full_3", "verify_publish.py")
    monkeypatch.setattr(module, "_run", lambda cmd: (0, "   "))
    monkeypatch.setattr(sys, "argv", ["verify_publish.py"])
    assert module.main() == 1


def test_verify_publish_fails_all_checks(monkeypatch: pytest.MonkeyPatch) -> None:
    module = _load_module("verify_publish_full_4", "verify_publish.py")

    def _fake_run(cmd: list[str]):
        if cmd == ["git", "branch", "--show-current"]:
            return 0, "other-branch"
        if cmd[:4] == ["git", "rev-parse", "--abbrev-ref", "fix/test@{upstream}"]:
            return 1, ""
        if cmd == ["git", "ls-remote", "--heads", "origin", "fix/test"]:
            return 0, ""
        return 1, "unexpected"

    monkeypatch.setattr(module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["verify_publish.py", "--branch", "fix/test"])
    assert module.main() == 1


# ---------------------------------------------------------------------------
# prepare.py
# ---------------------------------------------------------------------------


def test_prepare_resolve_gate_cmd_replaces_python() -> None:
    module = _load_module("prepare_full_1", "prepare.py")
    resolved = module._resolve_gate_cmd(["python", "-c", "1"])
    assert resolved[0] == sys.executable


def test_prepare_resolve_gate_cmd_leaves_other() -> None:
    module = _load_module("prepare_full_2", "prepare.py")
    assert module._resolve_gate_cmd(["echo", "hi"]) == ["echo", "hi"]


def test_prepare_main_attribution_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("prepare_full_3", "prepare.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module, "resolve_pr_attribution", lambda **kw: (_ for _ in ()).throw(ValueError("bad settings"))
    )
    monkeypatch.setattr(sys, "argv", ["prepare.py", "--pr", "123", "--actor", "A", "--agents", "review-pr"])
    assert module.main() == 2


def test_prepare_main_skip_gates(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("prepare_full_4", "prepare.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare.py",
            "--pr",
            "123",
            "--actor",
            "A",
            "--agents",
            "review-pr",
            "--skip-gates",
            "--skip-gates-rationale",
            "verified externally",
        ],
    )
    assert module.main() == 0
    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "prep.md").read_text(encoding="utf-8")
    assert "externally verified" in content


def test_prepare_skip_gates_refused_for_arch_pipeline(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module("prepare_full_4b", "prepare.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "prepare.py",
            "--pr",
            "123",
            "--actor",
            "A",
            "--agents",
            "review-pr",
            "--pipeline",
            "architecture_impacting",
            "--skip-gates",
            "--skip-gates-rationale",
            "should fail",
        ],
    )
    assert module.main() == 2


def test_merge_pipeline_architecture_impacting_forces_alignment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module("merge_full_pipe_arch", "merge.py")
    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True)
    (wf / "review.md").write_text("# Review Artifact (123)\n", encoding="utf-8")
    (wf / "prep.md").write_text("# Prepare Artifact (123)\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "merge.py",
            "--pr",
            "123",
            "--actor",
            "A",
            "--agents",
            "review-pr",
            "--pipeline",
            "architecture_impacting",
            "--check-only",
        ],
    )
    assert module.main() == 1


def test_path_triggers_arch_impacting() -> None:
    paths_mod = _load_module("arch_paths_1", "arch_impacting_paths.py")
    assert paths_mod.path_triggers_arch_impacting([".cursor/rules/foo.mdc"]) is True
    assert paths_mod.path_triggers_arch_impacting(["README.md"]) is False
    assert (
        paths_mod.path_triggers_arch_impacting(
            [".ai_infra/scripts/workflow/audit_artifact_schema.py"]
        )
        is True
    )


def test_merge_path_trigger_forces_alignment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = _load_module("merge_full_path_trig", "merge.py")
    wf = tmp_path / ".local" / "workflow-artifacts" / "pr"
    wf.mkdir(parents=True)
    (wf / "review.md").write_text("# Review Artifact (123)\n", encoding="utf-8")
    (wf / "prep.md").write_text("# Prepare Artifact (123)\n", encoding="utf-8")
    status = (
        tmp_path
        / ".ai_infra"
        / "docs"
        / "handoff"
        / "IMPLEMENTATION-STATUS.md"
    )
    status.parent.mkdir(parents=True)
    status.write_text("# kit-dev\n", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        module,
        "branch_triggers_arch_impacting",
        lambda _root, **_kw: True,
    )
    monkeypatch.setattr(
        sys,
        "argv",
        ["merge.py", "--pr", "123", "--actor", "A", "--agents", "review-pr", "--check-only"],
    )
    assert module.main() == 1


def test_prepare_main_gate_failure(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    module = _load_module("prepare_full_5", "prepare.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(module, "resolve_gates", lambda _root=None: [["python3", "-c", "import sys; sys.exit(1)"]])
    monkeypatch.setattr(
        sys,
        "argv",
        ["prepare.py", "--pr", "123", "--actor", "A", "--agents", "review-pr"],
    )
    assert module.main() == 1
    content = (tmp_path / ".local" / "workflow-artifacts" / "pr" / "prep.md").read_text(encoding="utf-8")
    assert "NOT READY" in content
    assert "FAIL" in content


# ---------------------------------------------------------------------------
# __main__ guards + own sys.path bootstrap (merge/prepare/review)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("filename", ["merge.py", "prepare.py", "review.py"])
def test_script_main_guard_and_path_insert(
    filename: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sys, "argv", [filename, "--pr", "1", "--actor", "A", "--agents", "review-pr"]
    )
    with _without_path(str(SCRIPTS_DIR)):
        with pytest.raises(SystemExit):
            runpy.run_path(str(SCRIPTS_DIR / filename), run_name="__main__")
    assert str(SCRIPTS_DIR) in sys.path


def test_verify_publish_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["verify_publish.py", "--branch", "does-not-matter"])
    with pytest.raises(SystemExit):
        runpy.run_path(str(SCRIPTS_DIR / "verify_publish.py"), run_name="__main__")


def test_finalize_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "does-not-exist-xyz", "--dry-run"])
    with pytest.raises(SystemExit):
        runpy.run_path(str(SCRIPTS_DIR / "finalize.py"), run_name="__main__")
