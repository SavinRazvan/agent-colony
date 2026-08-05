"""
File: test_drift012_plan_snapshots.py
Path: tests/modules/workflow_drift/test_drift012_plan_snapshots.py
Role: Tests for DRIFT-012 .local/plans live-plan misuse guard.
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

from drift_checks import check_drift012, drift_paths  # noqa: E402


def _board_only_root(tmp: Path) -> Path:
    settings = tmp / ".local" / "user_settings"
    settings.mkdir(parents=True)
    data = {
        "version": 1,
        "owner": {"display_name": "T", "github_user": "@t"},
        "project_ssot": {"enabled": True, "sync_policy": "board_only"},
        "commit_provenance": {"ai_disclosure_mode": "none"},
        "pr_collaboration": {"pipelines": {"default": {"agents": ["review-pr"]}}},
    }
    (settings / "github.collaboration.yaml").write_text(yaml.safe_dump(data), encoding="utf-8")
    return tmp


def test_drift012_passes_when_plans_dir_absent(tmp_path: Path) -> None:
    root = _board_only_root(tmp_path)
    result = check_drift012(drift_paths(root))
    assert result.passed
    assert result.check_id == "DRIFT-012"


def test_drift012_fails_on_current_plan_filename(tmp_path: Path) -> None:
    root = _board_only_root(tmp_path)
    plans = root / ".local" / "plans"
    plans.mkdir(parents=True)
    (plans / "current.plan.md").write_text("# Current\n", encoding="utf-8")
    result = check_drift012(drift_paths(root))
    assert not result.passed
    assert "current.plan.md" in result.detail
