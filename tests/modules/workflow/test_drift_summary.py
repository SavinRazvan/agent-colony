"""
File: test_drift_summary.py
Path: tests/modules/workflow/test_drift_summary.py
Role: Tests drift validate --summary output.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/check_drift.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_WORKFLOW) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW))

import check_drift  # noqa: E402


def test_drift_summary_format() -> None:
    results = check_drift.run_checks(REPO_ROOT, "kit-dev")
    line = check_drift.format_summary(results, profile="kit-dev")
    assert line.startswith("drift validate:")
    assert "profile=kit-dev" in line


def test_drift_main_summary(capsys: pytest.CaptureFixture[str]) -> None:
    code = check_drift.main(["--directory", str(REPO_ROOT), "--profile", "kit-dev", "--summary"])
    out = capsys.readouterr().out.strip()
    assert "drift validate:" in out
    assert code in (0, 1)
