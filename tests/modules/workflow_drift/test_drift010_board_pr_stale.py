"""
File: test_drift010_board_pr_stale.py
Path: tests/modules/workflow_drift/test_drift010_board_pr_stale.py
Role: Tests for DRIFT-010 board Status vs open PRs / stale In progress.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

from drift_checks import check_drift010, drift_paths  # noqa: E402


def _scaffold(
    tmp: Path,
    *,
    enabled: bool = True,
    policy: str = "board_only",
    snapshot: dict | None = None,
    write_snapshot: bool = True,
) -> Path:
    planning = tmp / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text(
        "# Work Tracker\n\n## Active\n\n(none)\n",
        encoding="utf-8",
    )
    settings = tmp / ".local" / "user_settings"
    settings.mkdir(parents=True)
    data = {
        "version": 1,
        "owner": {"display_name": "T", "github_user": "@t"},
        "project_ssot": {
            "enabled": enabled,
            "sync_policy": policy,
            "default_repo": "SavinRazvan/mas-workflow-kit-project-ssot",
        },
        "commit_provenance": {"ai_disclosure_mode": "none"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    (settings / "github.collaboration.yaml").write_text(
        yaml.safe_dump(data), encoding="utf-8"
    )
    if write_snapshot and snapshot is not None:
        gen = tmp / ".local" / "generated-data"
        gen.mkdir(parents=True)
        (gen / "board-snapshot.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
    return tmp


def test_drift010_skips_without_snapshot(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, snapshot=None, write_snapshot=False)
    result = check_drift010(drift_paths(root))
    assert result.passed
    assert "skipped" in result.detail


def test_drift010_skips_when_disabled(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, enabled=False, snapshot={"items": []})
    result = check_drift010(drift_paths(root))
    assert result.passed
    assert "disabled" in result.detail


def test_drift010_detects_merged_but_not_done(
    monkeypatch, tmp_path: Path
) -> None:
    snap = {
        "schema": "board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_x",
                "title": "Left open",
                "status": "In review",
                "status_normalized": "in_review",
                "body_excerpt": "Merged: https://github.com/o/r/pull/1 @ abc",
            }
        ],
    }
    root = _scaffold(tmp_path, snapshot=snap)
    monkeypatch.setattr(
        "drift_checks._open_pr_bodies",
        lambda repo: ([], None),
    )
    result = check_drift010(drift_paths(root))
    assert not result.passed
    assert "merged-but-not-done" in result.detail


def test_drift010_passes_clean_board(monkeypatch, tmp_path: Path) -> None:
    snap = {
        "schema": "board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_ok",
                "title": "Done card",
                "status": "Done",
                "status_normalized": "done",
                "body_excerpt": "Merged: url @ sha",
            }
        ],
    }
    root = _scaffold(tmp_path, snapshot=snap)
    monkeypatch.setattr(
        "drift_checks._open_pr_bodies",
        lambda repo: ([], None),
    )
    result = check_drift010(drift_paths(root))
    assert result.passed
