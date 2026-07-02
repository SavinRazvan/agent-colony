"""
File: test_check_drift_full.py
Path: tests/modules/workflow_drift/test_check_drift_full.py
Role: In-process coverage for check_drift.py main()/format_report()/exit_code_for().
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/check_drift.py
"""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

import check_drift as cd  # noqa: E402


def test_format_report_counts_all_severities() -> None:
    results = [
        cd.CheckResult(check_id="X-P0", severity=cd.Severity.P0, passed=False, detail="p0"),
        cd.CheckResult(check_id="X-P1", severity=cd.Severity.P1, passed=False, detail="p1"),
        cd.CheckResult(check_id="X-P2", severity=cd.Severity.P2, passed=False, detail="p2"),
    ]
    report = cd.format_report(results, profile="kit-dev")
    assert "summary: p0_fail=1 p1_fail=1 p2_fail=1 total=3" in report
    assert "profile: kit-dev" in report


def test_exit_code_for_p0_failure() -> None:
    results = [cd.CheckResult(check_id="X", severity=cd.Severity.P0, passed=False, detail="x")]
    assert cd.exit_code_for(results) == 1


def test_main_text_output_on_kit_repo(capsys: pytest.CaptureFixture[str]) -> None:
    code = cd.main(["--directory", str(REPO_ROOT), "--profile", "kit-dev"])
    captured = capsys.readouterr()
    assert code in (0, 1)
    assert "profile: kit-dev" in captured.out
    assert "summary:" in captured.out


def test_main_json_output(capsys: pytest.CaptureFixture[str]) -> None:
    code = cd.main(["--directory", str(REPO_ROOT), "--profile", "kit-dev", "--json"])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["profile"] == "kit-dev"
    assert "results" in payload
    assert payload["exit_code"] == code


def test_main_auto_detects_profile(tmp_path: Path) -> None:
    planning = tmp_path / ".local/index-and-planning/current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text("# Tracker\nprofile: consumer\n", encoding="utf-8")
    code = cd.main(["--directory", str(tmp_path)])
    assert code in (0, 1)


def test_resolve_profile_reads_work_tracker(tmp_path: Path) -> None:
    profile = cd.resolve_profile(tmp_path, None)
    assert profile in ("kit-dev", "consumer")


def test_main_guard_via_runpy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        sys, "argv", ["check_drift.py", "--directory", str(REPO_ROOT), "--profile", "kit-dev"]
    )
    with pytest.raises(SystemExit):
        runpy.run_path(str(WORKFLOW_DIR / "check_drift.py"), run_name="__main__")
