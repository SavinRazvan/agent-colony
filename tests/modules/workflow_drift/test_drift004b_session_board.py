"""
File: test_drift004b_session_board.py
Path: tests/modules/workflow_drift/test_drift004b_session_board.py
Role: Tests for DRIFT-004b session-pointer Board vs export snapshot.
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

from drift_checks import (  # noqa: E402
    check_drift004b,
    drift_paths,
    _parse_session_board_field,
)


def _scaffold(
    tmp: Path,
    *,
    enabled: bool = True,
    policy: str = "board_only",
    board_cell: str = "",
    snapshot: dict | None = None,
    write_snapshot: bool = True,
) -> Path:
    planning = tmp / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    session = "# Session\n\n| Field | Value |\n|-------|--------|\n"
    if board_cell:
        session += f"| **Board** | {board_cell} |\n"
    (planning / "session-pointer.md").write_text(session, encoding="utf-8")
    (planning / "work-tracker.md").write_text(
        "# Work Tracker\n\n## Active\n\n(none)\n",
        encoding="utf-8",
    )
    (planning / "plan.md").write_text("# Plan\n\n## Current focus\n\n- x\n", encoding="utf-8")
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
        (gen / "project-board-snapshot.json").write_text(
            json.dumps(snapshot), encoding="utf-8"
        )
    return tmp


def test_parse_session_board_field() -> None:
    iid, st = _parse_session_board_field(
        "PVTI_lAHOBl46-84A9KZxzgzRK20 In progress"
    )
    assert iid == "PVTI_lAHOBl46-84A9KZxzgzRK20"
    assert "progress" in st.lower()


def test_parse_session_board_field_strips_markdown_backticks() -> None:
    iid, st = _parse_session_board_field(
        "`PVTI_lAHOBl46-84A9KZxzgzSsE0` Done"
    )
    assert iid == "PVTI_lAHOBl46-84A9KZxzgzSsE0"
    assert st.lower() == "done"


def test_drift004b_skips_without_snapshot(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        board_cell="PVTI_abc In progress",
        snapshot=None,
        write_snapshot=False,
    )
    result = check_drift004b(drift_paths(root))
    assert result.passed
    assert "skipped" in result.detail


def test_drift004b_skips_when_disabled(tmp_path: Path) -> None:
    root = _scaffold(
        tmp_path,
        enabled=False,
        board_cell="PVTI_abc In progress",
        snapshot={"items": []},
    )
    result = check_drift004b(drift_paths(root))
    assert result.passed
    assert "disabled" in result.detail


def test_drift004b_fails_stale_in_progress_vs_done(tmp_path: Path) -> None:
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_stale",
                "title": "Old",
                "status": "Done",
                "status_normalized": "done",
            }
        ],
    }
    root = _scaffold(
        tmp_path,
        board_cell="PVTI_stale In progress",
        snapshot=snap,
    )
    result = check_drift004b(drift_paths(root))
    assert not result.passed
    assert "PVTI_stale" in result.detail
    assert "done" in result.detail


def test_drift004b_passes_matching_in_progress(tmp_path: Path) -> None:
    snap = {
        "schema": "project-board-snapshot/v1",
        "items": [
            {
                "id": "PVTI_ok",
                "title": "Active",
                "status": "In progress",
                "status_normalized": "in_progress",
            }
        ],
    }
    root = _scaffold(
        tmp_path,
        board_cell="PVTI_ok In progress",
        snapshot=snap,
    )
    result = check_drift004b(drift_paths(root))
    assert result.passed
    assert "aligns" in result.detail


def test_drift004b_skips_without_board_item_id(tmp_path: Path) -> None:
    root = _scaffold(tmp_path, board_cell="", snapshot={"items": []})
    result = check_drift004b(drift_paths(root))
    assert result.passed
    assert "skipped" in result.detail


def test_drift004b_fails_missing_item(tmp_path: Path) -> None:
    snap = {"schema": "project-board-snapshot/v1", "items": []}
    root = _scaffold(
        tmp_path,
        board_cell="PVTI_gone In progress",
        snapshot=snap,
    )
    result = check_drift004b(drift_paths(root))
    assert not result.passed
    assert "missing" in result.detail
