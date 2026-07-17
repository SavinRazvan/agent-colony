"""
File: test_drift009_board_ssot.py
Path: tests/modules/workflow_drift/test_drift009_board_ssot.py
Role: Tests for DRIFT-009 board_only dual-write guard.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

from drift_checks import check_drift009, drift_paths  # noqa: E402


def _scaffold(tmp: Path, *, enabled: bool, policy: str, tracker_active: str) -> Path:
    planning = tmp / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text(
        f"# Work Tracker\n\n## Active\n\n{tracker_active}\n\n## Completed\n",
        encoding="utf-8",
    )
    settings = tmp / ".local" / "user_settings"
    settings.mkdir(parents=True)
    data = {
        "version": 1,
        "owner": {"display_name": "T", "github_user": "@t"},
        "project_ssot": {"enabled": enabled, "sync_policy": policy},
        "commit_provenance": {"ai_disclosure_mode": "none"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    (settings / "github.collaboration.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    return tmp


def test_drift009_passes_when_no_tracker_in_progress(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, enabled=True, policy="board_only", tracker_active="(none)")
    result = check_drift009(drift_paths(root))
    assert result.passed
    assert result.check_id == "DRIFT-009"


def test_drift009_fails_on_dual_write(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        enabled=True,
        policy="board_only",
        tracker_active="- [ ] `in_progress` **BAD**",
    )
    result = check_drift009(drift_paths(root))
    assert not result.passed


def test_drift009_skips_when_disabled(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        enabled=False,
        policy="board_only",
        tracker_active="- [ ] `in_progress` **OK**",
    )
    result = check_drift009(drift_paths(root))
    assert result.passed
