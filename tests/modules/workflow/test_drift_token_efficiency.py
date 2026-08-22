"""
File: test_drift_token_efficiency.py
Path: tests/modules/workflow/test_drift_token_efficiency.py
Role: Negative fixtures for DRIFT-014 token-efficiency anchors and DRIFT-015/016 token checks.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_DRIFT = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
_SCAFFOLD_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "install"
if str(_DRIFT) not in sys.path:
    sys.path.insert(0, str(_DRIFT))
if str(_SCAFFOLD_DIR) not in sys.path:
    sys.path.insert(0, str(_SCAFFOLD_DIR))

import drift_checks  # noqa: E402
import scaffold  # noqa: E402


def test_drift014_fails_when_agent_missing_token_anchor(tmp_path: Path) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    (agents / "implementer.md").write_text(
        "# implementer\n\nNo token-efficiency link here.\n",
        encoding="utf-8",
    )
    paths = drift_checks.drift_paths(tmp_path)
    result = drift_checks.check_drift014(paths)
    assert result.check_id == "DRIFT-014"
    assert not result.passed
    assert "implementer" in result.detail


def test_drift015_warns_on_plugin_workspace_rule_overlap(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules = tmp_path / ".cursor" / "rules"
    rules.mkdir(parents=True)
    (rules / "test-rule.mdc").write_text("---\nalwaysApply: true\n---\n", encoding="utf-8")
    cache_path = "/fake/cache/agent-colony/agent-colony/abc/rules/test-rule.mdc"

    def fake_glob(pattern: str) -> list[str]:
        if "plugins/cache" in pattern:
            return [cache_path]
        return []

    monkeypatch.setattr(glob, "glob", fake_glob)
    paths = drift_checks.drift_paths(tmp_path)
    result = drift_checks.check_drift015(paths)
    assert result.check_id == "DRIFT-015"
    assert result.passed
    assert "WARN" in result.detail
    assert "test-rule.mdc" in result.detail


def test_drift016_skips_skills_outside_lite_allowlist(tmp_path: Path) -> None:
    scaffold.scaffold(
        tmp_path,
        REPO_ROOT,
        profile="consumer_lite",
        dry_run=False,
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    marker = tmp_path / ".local" / "generated-data" / "install-profile.json"
    data = json.loads(marker.read_text(encoding="utf-8"))
    assert data["profile"] == "consumer_lite"

    paths = drift_checks.drift_paths(tmp_path)
    result = drift_checks.check_drift016(paths)
    assert result.check_id == "DRIFT-016"
    assert result.passed
    assert "skipped=" in result.detail
    skipped = int(result.detail.split("skipped=")[1].rstrip(")"))
    assert skipped > 0
