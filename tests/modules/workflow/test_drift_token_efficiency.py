"""
File: test_drift_token_efficiency.py
Path: tests/modules/workflow/test_drift_token_efficiency.py
Role: Negative fixtures for DRIFT-014 token-efficiency anchors.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_DRIFT = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_DRIFT) not in sys.path:
    sys.path.insert(0, str(_DRIFT))

import drift_checks  # noqa: E402


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
