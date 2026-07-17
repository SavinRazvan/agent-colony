"""
File: test_drift_cli.py
Path: tests/modules/workflow_drift/test_drift_cli.py
Role: Tests for check_drift CLI entry and cursor_workflow drift validate wiring.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/check_drift.py
 - .ai_infra/install/cursor_workflow/drift_cli.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"


def test_check_drift_main_json(tmp_path: Path) -> None:
    planning = tmp_path / ".local/index-and-planning/current"
    planning.mkdir(parents=True)
    (planning / "plan.md").write_text("# Plan\n\n## Current focus\n\n- ok\n", encoding="utf-8")
    (planning / "work-tracker.md").write_text("# Tracker\n\n## Active\n\n(none)\n", encoding="utf-8")
    (planning / "session-pointer.md").write_text("| **Phase** | ok |\n", encoding="utf-8")
    (planning / "updates-log.md").write_text("# log\n", encoding="utf-8")
    handoff = tmp_path / ".ai_infra/docs/handoff"
    handoff.mkdir(parents=True)
    (handoff / "IMPLEMENTATION-STATUS.md").write_text("**Tests:** 1\n", encoding="utf-8")
    (planning / "test-index.md").write_text("- Module: x\n  - Owned tests: `tests/x.py`\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(WORKFLOW_DIR / "check_drift.py"),
            "--directory",
            str(tmp_path),
            "--profile",
            "kit-dev",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode in (0, 1)
    assert "DRIFT-001" in proc.stdout


def test_cursor_workflow_drift_validate_on_kit_repo() -> None:
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "cursor_workflow",
            "drift",
            "validate",
            "--directory",
            str(REPO_ROOT),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0
    assert "DRIFT-005" in proc.stdout


def test_cursor_workflow_drift_validate_consumer_profile_skips_drift005(tmp_path: Path) -> None:
    planning = tmp_path / ".local/index-and-planning/current"
    planning.mkdir(parents=True)
    (planning / "plan.md").write_text("# Plan\n", encoding="utf-8")
    (planning / "work-tracker.md").write_text("# Tracker\n", encoding="utf-8")
    (planning / "session-pointer.md").write_text("# Pointer\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(WORKFLOW_DIR / "check_drift.py"),
            "--directory",
            str(tmp_path),
            "--profile",
            "consumer",
        ],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert proc.returncode == 0
    assert "profile: consumer" in proc.stdout
    assert "DRIFT-005" in proc.stdout
    assert "PASS" in proc.stdout
    assert "skipped" in proc.stdout.lower()
