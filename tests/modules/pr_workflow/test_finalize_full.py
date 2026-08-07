"""
File: test_finalize_full.py
Path: tests/modules/pr_workflow/test_finalize_full.py
Role: Full-branch coverage for finalize.py (post-merge branch cleanup script).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/pr/finalize.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "pr"


def _load_finalize():
    spec = importlib.util.spec_from_file_location("finalize_full", SCRIPTS_DIR / "finalize.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def finalize_module():
    return _load_finalize()


# ---------------------------------------------------------------------------
# Real (read-only) subprocess helpers
# ---------------------------------------------------------------------------


def test_run_real_command(finalize_module) -> None:
    code, out = finalize_module._run(["git", "rev-parse", "--is-inside-work-tree"])
    assert code == 0
    assert out == "true"


def test_current_branch_failure_returns_unknown(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, "error"))
    assert finalize_module._current_branch() == "unknown"


def test_current_branch_real() -> None:
    module = _load_finalize()
    branch = module._current_branch()
    assert isinstance(branch, str) and branch


def test_local_branch_exists_false_for_bogus_name(finalize_module) -> None:
    assert finalize_module._local_branch_exists("definitely-not-a-real-branch-xyz") is False


def test_remote_branch_exists_false_for_bogus_name(finalize_module) -> None:
    assert finalize_module._remote_branch_exists("definitely-not-a-real-branch-xyz") is False


def test_list_local_merged_branches_failure_returns_empty(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, ""))
    assert finalize_module._list_local_merged_branches() == []


def test_list_local_merged_branches_parses_star_and_strips(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, "* main\n  feature/a\n\n"))
    assert finalize_module._list_local_merged_branches() == ["main", "feature/a"]


# ---------------------------------------------------------------------------
# _run_step / _finish
# ---------------------------------------------------------------------------


def test_run_step_dry_run(finalize_module) -> None:
    logs: list[str] = []
    failures: list[str] = []
    ok = finalize_module._run_step(["echo", "hi"], "step", failures, logs, dry_run=True)
    assert ok is True
    assert not failures
    assert any("DRY-RUN" in line for line in logs)


def test_run_step_success(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, "output text"))
    logs: list[str] = []
    failures: list[str] = []
    ok = finalize_module._run_step(["echo", "hi"], "step", failures, logs)
    assert ok is True
    assert not failures
    assert "output text" in logs


def test_run_step_failure(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, "boom"))
    logs: list[str] = []
    failures: list[str] = []
    ok = finalize_module._run_step(["false"], "step", failures, logs)
    assert ok is False
    assert "step failed (exit=1)" in failures[0]


def test_finish_with_failures(finalize_module, capsys: pytest.CaptureFixture[str]) -> None:
    code = finalize_module._finish(["log1"], ["bad thing"])
    assert code == 1
    out = capsys.readouterr().out
    assert "[FAIL] bad thing" in out


def test_finish_dry_run_pass(finalize_module, capsys: pytest.CaptureFixture[str]) -> None:
    code = finalize_module._finish(["log1"], [], dry_run=True)
    assert code == 0
    assert "dry-run completed" in capsys.readouterr().out


def test_finish_real_pass(finalize_module, capsys: pytest.CaptureFixture[str]) -> None:
    code = finalize_module._finish(["log1"], [], dry_run=False)
    assert code == 0
    assert "cleanup completed" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


def test_main_blocks_empty_branch(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "   "])
    assert finalize_module.main() == 1


def test_main_blocks_main_branch(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "main"])
    assert finalize_module.main() == 1


def test_main_checkout_fails(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "other-branch")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, "checkout failed"))
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_pull_fails(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")

    def _fake_run(cmd: list[str]):
        if cmd[:2] == ["git", "pull"]:
            return 1, "pull failed"
        return 0, ""

    monkeypatch.setattr(finalize_module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_fetch_prune_fails(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")

    def _fake_run(cmd: list[str]):
        if cmd[:2] == ["git", "fetch"]:
            return 1, "fetch failed"
        return 0, ""

    monkeypatch.setattr(finalize_module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_full_dry_run_with_delete_merged_local(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda b: True)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda b: True)
    monkeypatch.setattr(
        finalize_module,
        "_list_local_merged_branches",
        lambda: ["main", "feature/x", "chore/stale"],
    )
    monkeypatch.setattr(
        sys, "argv", ["finalize.py", "--branch", "feature/x", "--delete-merged-local", "--dry-run"]
    )
    assert finalize_module.main() == 0


def test_main_local_and_remote_still_exist_after_non_dry_run(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda b: True)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda b: True)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_local_and_remote_absent_logs_info(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda b: False)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda b: False)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x", "--dry-run"])
    assert finalize_module.main() == 0


# ---------------------------------------------------------------------------
# _maybe_close_linked_issue
# ---------------------------------------------------------------------------


def test_maybe_close_linked_issue_skips_no_pr(finalize_module) -> None:
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref=None, dry_run=False, cleanup_ok=True
    )
    assert status == "SKIPPED"
    assert "no --pr" in detail


def test_maybe_close_linked_issue_skips_unknown_pr(finalize_module) -> None:
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref="unknown", dry_run=False, cleanup_ok=True
    )
    assert status == "SKIPPED"


def test_maybe_close_linked_issue_skips_cleanup_failed(finalize_module) -> None:
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=False, cleanup_ok=False
    )
    assert status == "SKIPPED"
    assert "cleanup did not fully succeed" in detail


def test_maybe_close_linked_issue_deferred_on_nonzero_exit(
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, "boom"))
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=False, cleanup_ok=True
    )
    assert status == "DEFERRED"
    assert detail == "boom"


def test_maybe_close_linked_issue_deferred_on_exception(
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _boom(cmd: list[str]) -> tuple[int, str]:
        raise RuntimeError("subprocess exploded")

    monkeypatch.setattr(finalize_module, "_run", _boom)
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=False, cleanup_ok=True
    )
    assert status == "DEFERRED"
    assert "invocation failed" in detail


def test_maybe_close_linked_issue_skipped_from_cli_output(
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        finalize_module,
        "_run",
        lambda cmd: (0, "close-linked-issue: SKIPPED — flag disabled"),
    )
    status, _detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=False, cleanup_ok=True
    )
    assert status == "SKIPPED"


def test_maybe_close_linked_issue_dry_run_from_cli_output(
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        finalize_module,
        "_run",
        lambda cmd: (0, "close-linked-issue: DRY-RUN — would close issue #1"),
    )
    status, _detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=True, cleanup_ok=True
    )
    assert status == "DRY-RUN"


def test_maybe_close_linked_issue_pass_from_cli_output(
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str]) -> tuple[int, str]:
        calls.append(cmd)
        return 0, "close-linked-issue: PASS — closed issue #1 (org/repo)"

    monkeypatch.setattr(finalize_module, "_run", _fake_run)
    status, detail = finalize_module._maybe_close_linked_issue(
        pr_ref="123", dry_run=False, cleanup_ok=True
    )
    assert status == "PASS"
    assert "closed issue #1" in detail
    assert calls[0] == [
        calls[0][0],
        "-m",
        "agent_colony",
        "project",
        "close-linked-issue",
        "--pr",
        "123",
    ]


def test_main_writes_finalize_md_pass(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda _b: False)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda _b: False)

    monkeypatch.setattr(
        sys,
        "argv",
        [
            "finalize.py",
            "--pr",
            "123",
            "--branch",
            "feature/x",
            "--actor",
            "Example Author",
            "--agents",
            "full-pr-workflow",
        ],
    )
    assert finalize_module.main() == 0

    finalize_md = (
        tmp_path / ".local" / "workflow-artifacts" / "pr" / "finalize.md"
    )
    assert finalize_md.is_file()
    text = finalize_md.read_text(encoding="utf-8")
    assert "Finalize Artifact (123)" in text
    assert "## Attribution" in text
    assert "Action-By: Example Author" in text
    assert "## Cleanup Results" in text
    assert "## Linked Issue Closure" in text


def test_main_writes_finalize_md_issue_closure_skipped_no_pr(
    finalize_module, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda _b: False)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda _b: False)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 0

    finalize_md = tmp_path / ".local" / "workflow-artifacts" / "pr" / "finalize.md"
    text = finalize_md.read_text(encoding="utf-8")
    assert "## Linked Issue Closure" in text
    assert "- Status: SKIPPED" in text
    assert "no --pr provided" in text
