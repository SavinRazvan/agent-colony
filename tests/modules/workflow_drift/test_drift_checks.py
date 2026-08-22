"""
File: test_drift_checks.py
Path: tests/modules/workflow_drift/test_drift_checks.py
Role: Unit tests for DRIFT-001…008 check functions.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
"""

from __future__ import annotations

import sys
import time
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_DIR))

from drift_checks import (  # noqa: E402
    _parse_owned_test_paths,
    _path_exists,
    LIVE_KIT_AGENT_IDS,
    check_drift001,
    check_drift002,
    check_drift003,
    check_drift004,
    check_drift005,
    check_drift006,
    check_drift007,
    check_drift008,
    check_drift011,
    check_drift011b,
    check_drift013,
    detect_profile,
    drift_paths,
)


def _write_planning(tmp: Path) -> None:
    planning = tmp / ".local" / "index-and-planning" / "current"
    planning.mkdir(parents=True)
    (planning / "plan.md").write_text(
        "# Plan\n\n## Current focus\n\n- **DRIFT-GUARD** feature work\n",
        encoding="utf-8",
    )
    (planning / "work-tracker.md").write_text(
        "# Work Tracker\n\n## Active\n\n"
        "- [ ] `in_progress` **DRIFT-GUARD**\n\n## Completed\n",
        encoding="utf-8",
    )
    (planning / "session-pointer.md").write_text(
        "| Field | Value |\n| **Phase** | DRIFT-GUARD |\n| **Next** | Slice 2 |\n",
        encoding="utf-8",
    )
    (planning / "updates-log.md").write_text("# Updates\n", encoding="utf-8")
    (planning / "test-index.md").write_text(
        "- Module: `demo`\n  - Owned tests: `tests/modules/demo/test_demo.py`\n",
        encoding="utf-8",
    )


def _write_board_only_collab(tmp: Path) -> None:
    settings = tmp / ".local" / "user_settings"
    settings.mkdir(parents=True, exist_ok=True)
    (settings / "github.collaboration.yaml").write_text(
        "version: 1\n"
        "owner:\n"
        "  display_name: T\n"
        "  github_user: \"@t\"\n"
        "project_ssot:\n"
        "  enabled: true\n"
        "  sync_policy: board_only\n"
        "commit_provenance:\n"
        "  ai_disclosure_mode: none\n",
        encoding="utf-8",
    )


def test_drift001_passes_when_planning_dir_exists(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    result = check_drift001(drift_paths(tmp_path))
    assert result.passed
    assert result.check_id == "DRIFT-001"


def test_drift001_fails_when_planning_missing(tmp_path: Path) -> None:
    result = check_drift001(drift_paths(tmp_path))
    assert not result.passed


def test_drift002_fails_on_multiple_in_progress(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    tracker = tmp_path / ".local/index-and-planning/current/work-tracker.md"
    tracker.write_text(
        "# Work Tracker\n\n## Active\n\n"
        "- [ ] `in_progress` **DRIFT-GUARD**\n"
        "- [ ] `in_progress` **OTHER**\n\n## Completed\n",
        encoding="utf-8",
    )
    result = check_drift002(drift_paths(tmp_path))
    assert not result.passed


def test_drift002_ignores_in_progress_outside_active(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    tracker = tmp_path / ".local/index-and-planning/current/work-tracker.md"
    tracker.write_text(
        "# Work Tracker\n\n## Active\n\n(none)\n\n## Rule\n\n- [ ] `in_progress` **OTHER**\n",
        encoding="utf-8",
    )
    result = check_drift002(drift_paths(tmp_path))
    assert result.passed
    assert "count=0" in result.detail


def test_drift003_passes_when_active_in_plan(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    result = check_drift003(drift_paths(tmp_path))
    assert result.passed


def test_drift003_skips_board_only_tracker(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    _write_board_only_collab(tmp_path)
    result = check_drift003(drift_paths(tmp_path))
    assert result.passed
    assert "board_only" in result.detail


def test_drift003_fails_when_active_not_in_plan(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    plan = tmp_path / ".local/index-and-planning/current/plan.md"
    plan.write_text("# Plan\n\n## Current focus\n\n- unrelated work\n", encoding="utf-8")
    result = check_drift003(drift_paths(tmp_path))
    assert not result.passed


def test_drift005_skips_when_implementation_status_absent(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    result = check_drift005(drift_paths(tmp_path))
    assert result.passed
    assert result.check_id == "DRIFT-005"
    assert "skipped" in result.detail


def test_drift005_fails_when_implementation_status_missing_test_count(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    handoff = tmp_path / ".ai_infra/docs/handoff"
    handoff.mkdir(parents=True)
    (handoff / "IMPLEMENTATION-STATUS.md").write_text("# Status\n\nNo test count here.\n", encoding="utf-8")
    result = check_drift005(drift_paths(tmp_path))
    assert not result.passed
    assert "missing **Tests:** count" in result.detail


def test_drift005_matches_doc_and_pytest(tmp_path: Path, monkeypatch) -> None:
    _write_planning(tmp_path)
    handoff = tmp_path / ".ai_infra/docs/handoff"
    handoff.mkdir(parents=True)
    (handoff / "IMPLEMENTATION-STATUS.md").write_text("**Tests:** 42\n", encoding="utf-8")

    class FakeProc:
        stdout = "42 tests collected"
        stderr = ""

    monkeypatch.setattr(
        "drift_checks.subprocess.run",
        lambda *a, **k: FakeProc(),
    )
    result = check_drift005(drift_paths(tmp_path))
    assert result.passed


def test_drift005_fails_on_mismatch(tmp_path: Path, monkeypatch) -> None:
    _write_planning(tmp_path)
    handoff = tmp_path / ".ai_infra/docs/handoff"
    handoff.mkdir(parents=True)
    (handoff / "IMPLEMENTATION-STATUS.md").write_text("**Tests:** 10\n", encoding="utf-8")

    class FakeProc:
        stdout = "42 tests collected"
        stderr = ""

    monkeypatch.setattr(
        "drift_checks.subprocess.run",
        lambda *a, **k: FakeProc(),
    )
    result = check_drift005(drift_paths(tmp_path))
    assert not result.passed
    assert "doc=10" in result.detail


def test_drift008_requires_scaffold_trackers(tmp_path: Path) -> None:
    result = check_drift008(drift_paths(tmp_path))
    assert not result.passed
    _write_planning(tmp_path)
    result = check_drift008(drift_paths(tmp_path))
    assert result.passed


def test_detect_profile_consumer_on_starter_exemplar() -> None:
    assert detect_profile("STARTER-001 placeholder") == "consumer"
    assert detect_profile("STARTER-001 placeholder", board_only=True) == "consumer-board"
    assert detect_profile("normal kit work") == "kit-dev"
    assert detect_profile("normal kit work", board_only=True) == "kit-dev"


def test_drift004_reports_next_field_not_builtin(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    planning = tmp_path / ".local" / "index-and-planning" / "current"
    (planning / "session-pointer.md").write_text(
        "| **Phase** | unrelated-phase |\n| **Next** | unrelated-next |\n",
        encoding="utf-8",
    )
    result = check_drift004(drift_paths(tmp_path))
    assert not result.passed
    assert "unrelated-next" in result.detail
    assert "built-in function next" not in result.detail


def test_drift005_fails_when_pytest_collection_fails(tmp_path: Path, monkeypatch) -> None:
    _write_planning(tmp_path)
    handoff = tmp_path / ".ai_infra/docs/handoff"
    handoff.mkdir(parents=True)
    (handoff / "IMPLEMENTATION-STATUS.md").write_text("**Tests:** 10\n", encoding="utf-8")

    class FakeProc:
        stdout = "no test count here"
        stderr = "collection error"

    monkeypatch.setattr("drift_checks.subprocess.run", lambda *a, **k: FakeProc())
    result = check_drift005(drift_paths(tmp_path))
    assert not result.passed
    assert "collect-only failed" in result.detail


def test_parse_owned_test_paths_skips_ellipsis_and_angle_entries() -> None:
    text = "- Module: `demo`\n  - Owned tests: `tests/a.py`, `...`, `<placeholder>`\n"
    assert _parse_owned_test_paths(text) == ["tests/a.py"]


def test_path_exists_blank_rel_is_true(tmp_path: Path) -> None:
    assert _path_exists(tmp_path, "   ") is True


def test_drift006_reports_missing_owned_test_paths(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    test_index = tmp_path / ".local/index-and-planning/current/test-index.md"
    test_index.write_text(
        "- Module: `demo`\n  - Owned tests: `tests/does_not_exist.py`\n",
        encoding="utf-8",
    )
    result = check_drift006(drift_paths(tmp_path))
    assert not result.passed
    assert "tests/does_not_exist.py" in result.detail


def test_drift006_skips_blank_comma_parts(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    real_test = tmp_path / "tests" / "modules" / "demo" / "test_demo.py"
    real_test.parent.mkdir(parents=True)
    real_test.write_text("# demo\n", encoding="utf-8")
    test_index = tmp_path / ".local/index-and-planning/current/test-index.md"
    test_index.write_text(
        "- Module: `demo`\n"
        "  - Owned tests: `tests/modules/demo/test_demo.py, `\n",
        encoding="utf-8",
    )
    result = check_drift006(drift_paths(tmp_path))
    assert result.passed


def test_drift006_passes_when_no_owned_entries(tmp_path: Path) -> None:
    _write_planning(tmp_path)
    test_index = tmp_path / ".local/index-and-planning/current/test-index.md"
    test_index.write_text("- Module: `demo`\n  - no owned tests here\n", encoding="utf-8")
    result = check_drift006(drift_paths(tmp_path))
    assert result.passed
    assert "no Owned tests entries" in result.detail


def test_drift007_fails_when_updates_log_missing(tmp_path: Path, monkeypatch) -> None:
    _write_planning(tmp_path)
    updates_log = tmp_path / ".local/index-and-planning/current/updates-log.md"
    updates_log.unlink()

    class FakeProc:
        stdout = " M some-file.py\n"
        stderr = ""

    monkeypatch.setattr("drift_checks.subprocess.run", lambda *a, **k: FakeProc())
    result = check_drift007(drift_paths(tmp_path))
    assert not result.passed


def test_drift007_reads_history_updates_log_when_current_missing(
    tmp_path: Path, monkeypatch
) -> None:
    _write_planning(tmp_path)
    current = tmp_path / ".local/index-and-planning/current/updates-log.md"
    current.unlink()
    history = tmp_path / ".local/index-and-planning/history"
    history.mkdir(parents=True)
    updates_log = history / "updates-log.md"
    updates_log.write_text("# Updates\n", encoding="utf-8")

    class FakeProc:
        stdout = " M some-file.py\n"
        stderr = ""

    monkeypatch.setattr("drift_checks.subprocess.run", lambda *a, **k: FakeProc())
    result = check_drift007(drift_paths(tmp_path))
    assert result.passed
    assert "touched" in result.detail


def test_drift007_passes_when_updates_log_recent(tmp_path: Path, monkeypatch) -> None:
    import os

    _write_planning(tmp_path)
    updates_log = tmp_path / ".local/index-and-planning/current/updates-log.md"
    os.utime(updates_log, None)  # now

    class FakeProc:
        stdout = " M some-file.py\n"
        stderr = ""

    monkeypatch.setattr("drift_checks.subprocess.run", lambda *a, **k: FakeProc())
    result = check_drift007(drift_paths(tmp_path))
    assert result.passed
    assert "touched" in result.detail


def test_drift007_fails_when_updates_log_stale(tmp_path: Path, monkeypatch) -> None:
    import os

    _write_planning(tmp_path)
    updates_log = tmp_path / ".local/index-and-planning/current/updates-log.md"
    old = time.time() - (30 * 86400)
    os.utime(updates_log, (old, old))

    class FakeProc:
        stdout = " M some-file.py\n"
        stderr = ""

    monkeypatch.setattr("drift_checks.subprocess.run", lambda *a, **k: FakeProc())
    result = check_drift007(drift_paths(tmp_path))
    assert not result.passed
    assert "stale" in result.detail


def test_drift_validate_passes_p0_on_kit_repo() -> None:
    if str(WORKFLOW_DIR) not in sys.path:
        sys.path.insert(0, str(WORKFLOW_DIR))
    import check_drift

    results = check_drift.run_checks(REPO_ROOT)
    p0_failures = [r for r in results if not r.passed and r.severity.value == "P0"]
    assert not p0_failures, "\n".join(f"{r.check_id}: {r.detail}" for r in p0_failures)
    assert check_drift.exit_code_for(results) == 0
    drift011 = next(r for r in results if r.check_id == "DRIFT-011")
    assert drift011.passed, drift011.detail


def test_drift011_passes_with_live_roster(tmp_path: Path) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    for name in LIVE_KIT_AGENT_IDS:
        (agents / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    result = check_drift011(drift_paths(tmp_path))
    assert result.passed
    assert result.check_id == "DRIFT-011"


def test_drift011_fails_when_agent_missing(tmp_path: Path) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    for name in LIVE_KIT_AGENT_IDS - {"researcher"}:
        (agents / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    result = check_drift011(drift_paths(tmp_path))
    assert not result.passed
    assert "missing=researcher" in result.detail


def test_drift011_fails_on_extra_agent(tmp_path: Path) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    for name in LIVE_KIT_AGENT_IDS:
        (agents / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    (agents / "ghost-agent.md").write_text("# ghost\n", encoding="utf-8")
    result = check_drift011(drift_paths(tmp_path))
    assert not result.passed
    assert "extra=ghost-agent" in result.detail


def test_drift013_passes_when_runtime_untracked(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".local" / "user_settings").mkdir(parents=True)
    (tmp_path / ".local" / "user_settings" / "github.collaboration.yaml").write_text(
        "version: 1\n", encoding="utf-8"
    )
    result = check_drift013(drift_paths(tmp_path))
    assert result.passed
    assert result.check_id == "DRIFT-013"


def test_drift013_fails_when_local_tracked(tmp_path: Path) -> None:
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    secret = tmp_path / ".local" / "tracked.txt"
    secret.parent.mkdir(parents=True)
    secret.write_text("oops\n", encoding="utf-8")
    subprocess.run(["git", "add", ".local/tracked.txt"], cwd=tmp_path, check=True, capture_output=True)
    result = check_drift013(drift_paths(tmp_path))
    assert not result.passed
    assert "tracked runtime paths" in result.detail
    assert "upgrade-kit.md" in result.detail


def test_drift013_tracked_local_fails_consumer_exit(tmp_path: Path) -> None:
    import check_drift

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    planning = tmp_path / ".local/index-and-planning/current"
    planning.mkdir(parents=True)
    (planning / "work-tracker.md").write_text("# Tracker\n\n## Active\n\n(none)\n", encoding="utf-8")
    tracked = tmp_path / ".local" / "tracked.txt"
    tracked.write_text("oops\n", encoding="utf-8")
    subprocess.run(["git", "add", ".local/tracked.txt"], cwd=tmp_path, check=True, capture_output=True)
    code = check_drift.main(["--directory", str(tmp_path), "--profile", "consumer"])
    assert code == 1


def test_drift011b_advisory_extra_agent(tmp_path: Path) -> None:
    agents = tmp_path / ".cursor" / "agents"
    agents.mkdir(parents=True)
    for name in LIVE_KIT_AGENT_IDS:
        (agents / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    (agents / "security-reviewer.md").write_text("# extra\n", encoding="utf-8")
    result = check_drift011b(drift_paths(tmp_path))
    assert result.passed
    assert "extra integrator agents" in result.detail
    assert "security-reviewer" in result.detail
