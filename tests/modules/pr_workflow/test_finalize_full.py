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


def test_main_blocks_empty_branch(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "   "])
    assert finalize_module.main() == 1


def test_main_blocks_main_branch(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "main"])
    assert finalize_module.main() == 1


def test_main_checkout_fails(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "other-branch")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (1, "checkout failed"))
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_pull_fails(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")

    def _fake_run(cmd: list[str]):
        if cmd[:2] == ["git", "pull"]:
            return 1, "pull failed"
        return 0, ""

    monkeypatch.setattr(finalize_module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_fetch_prune_fails(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")

    def _fake_run(cmd: list[str]):
        if cmd[:2] == ["git", "fetch"]:
            return 1, "fetch failed"
        return 0, ""

    monkeypatch.setattr(finalize_module, "_run", _fake_run)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_full_dry_run_with_delete_merged_local(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
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
    finalize_module, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda b: True)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda b: True)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x"])
    assert finalize_module.main() == 1


def test_main_local_and_remote_absent_logs_info(finalize_module, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(finalize_module, "_current_branch", lambda: "main")
    monkeypatch.setattr(finalize_module, "_run", lambda cmd: (0, ""))
    monkeypatch.setattr(finalize_module, "_local_branch_exists", lambda b: False)
    monkeypatch.setattr(finalize_module, "_remote_branch_exists", lambda b: False)
    monkeypatch.setattr(sys, "argv", ["finalize.py", "--branch", "feature/x", "--dry-run"])
    assert finalize_module.main() == 0
