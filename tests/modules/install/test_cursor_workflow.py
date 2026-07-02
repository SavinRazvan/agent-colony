"""
File: test_cursor_workflow.py
Path: tests/modules/install/test_cursor_workflow.py
Role: Tests for cursor_workflow CLI.
Used By:
 - pytest
Depends On:
 - cursor_workflow/cli.py
Notes:
 - install dry-run only; gates uses mocked subprocess (no nested pytest).
"""

from __future__ import annotations

from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_install_dry_run(tmp_path: Path) -> None:
    from cursor_workflow.cli import main

    code = main(
        [
            "install",
            "--target",
            str(tmp_path / "out"),
            "--source",
            str(REPO_ROOT),
            "--dry-run",
            "--with-tests",
        ]
    )
    assert code == 0


def test_gates_invokes_five_steps(monkeypatch: pytest.MonkeyPatch) -> None:
    from cursor_workflow.cli import cmd_gates, kit_root

    calls: list[list[str]] = []

    def fake_run(cmd: list[str], cwd: Path) -> int:
        calls.append(cmd)
        return 0

    # cmd_gates is loaded from .ai_infra/install/.../cli.py via root shim
    monkeypatch.setitem(cmd_gates.__globals__, "_run", fake_run)

    class Args:
        directory = kit_root()

    assert cmd_gates(Args()) == 0
    assert len(calls) == 5
    assert "check_testing_artifacts.py" in calls[0][-1]
    assert calls[1][1:3] == ["-m", "pytest"]
    assert "check_governance_consistency.py" in calls[2][-1]
    assert "check_debrand.py" in calls[3][-1]
    assert "check_doc_facts.py" in calls[4][-1]


def test_version_in_package() -> None:
    import cursor_workflow

    assert cursor_workflow.__version__ == "0.4.0"
