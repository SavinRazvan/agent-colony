"""
File: drift_checks.py
Path: .ai_infra/scripts/workflow/drift_checks.py
Role: Individual DRIFT-001…008 check functions for workflow drift validation.
Used By:
 - .ai_infra/scripts/workflow/check_drift.py
Depends On:
 - subprocess, re, datetime (stdlib)
Notes:
 - Does not duplicate governance, integrate, or test-artifact scanners (ADR-007).
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Severity(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


@dataclass
class CheckResult:
    check_id: str
    severity: Severity
    passed: bool
    detail: str


@dataclass
class DriftPaths:
    root: Path
    planning_dir: Path
    plan: Path
    work_tracker: Path
    session_pointer: Path
    updates_log: Path
    test_index: Path
    implementation_status: Path


def drift_paths(root: Path) -> DriftPaths:
    planning = root / ".local" / "index-and-planning" / "current"
    return DriftPaths(
        root=root,
        planning_dir=planning,
        plan=planning / "plan.md",
        work_tracker=planning / "work-tracker.md",
        session_pointer=planning / "session-pointer.md",
        updates_log=planning / "updates-log.md",
        test_index=planning / "test-index.md",
        implementation_status=root / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md",
    )


def detect_profile(work_tracker_text: str, override: str | None = None) -> str:
    if override in ("kit-dev", "consumer"):
        return override
    if "STARTER-001" in work_tracker_text:
        return "consumer"
    return "kit-dev"


def _read(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def _extract_table_field(text: str, field: str) -> str:
    pattern = rf"\|\s*\*\*{re.escape(field)}\*\*\s*\|\s*([^|]+)\|"
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _extract_active_task(text: str) -> str | None:
    for line in text.splitlines():
        if "`in_progress`" in line:
            match = re.search(r"\*\*([^*]+)\*\*", line)
            if match:
                return match.group(1).strip()
    return None


def _count_in_progress(text: str) -> int:
    return text.count("`in_progress`")


def _extract_plan_focus(text: str) -> str:
    match = re.search(
        r"## Current focus\s*\n(.*?)(?:\n## |\Z)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    return match.group(1) if match else ""


def _parse_implementation_test_count(text: str) -> int | None:
    match = re.search(r"\*\*Tests:\*\*\s*(\d+)", text)
    return int(match.group(1)) if match else None


def _collect_pytest_count(root: Path) -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
    )
    combined = proc.stdout + proc.stderr
    match = re.search(r"(\d+)\s+tests?\s+collected", combined)
    return int(match.group(1)) if match else -1


def _parse_owned_test_paths(text: str) -> list[str]:
    if "## Current index" in text:
        text = text.split("## Current index", 1)[1]
    paths: list[str] = []
    for line in text.splitlines():
        if "Owned tests:" not in line:
            continue
        raw = line.split("Owned tests:", 1)[1]
        quoted = re.findall(r"`([^`]+)`", raw)
        candidates = quoted if quoted else [p.strip() for p in raw.split(",") if p.strip()]
        for part in candidates:
            part = part.strip().strip("`")
            if not part or "..." in part or part.startswith("<"):
                continue
            paths.append(part)
    return paths


def _path_exists(root: Path, rel: str) -> bool:
    rel = rel.strip()
    if not rel:
        return True
    if "*" in rel:
        return bool(list(root.glob(rel)))
    return (root / rel).exists()


def _git_porcelain(root: Path) -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.stdout.strip()


def check_drift001(paths: DriftPaths) -> CheckResult:
    passed = paths.planning_dir.is_dir()
    return CheckResult(
        check_id="DRIFT-001",
        severity=Severity.P0,
        passed=passed,
        detail=(
            "planning dir exists"
            if passed
            else f"missing {paths.planning_dir.relative_to(paths.root)}"
        ),
    )


def check_drift002(paths: DriftPaths) -> CheckResult:
    text = _read(paths.work_tracker)
    count = _count_in_progress(text)
    passed = count <= 1
    return CheckResult(
        check_id="DRIFT-002",
        severity=Severity.P0,
        passed=passed,
        detail=f"in_progress count={count}" if passed else f"too many in_progress ({count})",
    )


def check_drift003(paths: DriftPaths) -> CheckResult:
    tracker = _read(paths.work_tracker)
    plan = _read(paths.plan)
    active = _extract_active_task(tracker)
    focus = _extract_plan_focus(plan)
    if active is None:
        passed = True
        detail = "no active in_progress task"
    elif active.lower() in focus.lower():
        passed = True
        detail = f"active task {active!r} found in plan Current focus"
    else:
        passed = False
        detail = f"active task {active!r} not in plan Current focus"
    return CheckResult(
        check_id="DRIFT-003",
        severity=Severity.P1,
        passed=passed,
        detail=detail,
    )


def check_drift004(paths: DriftPaths) -> CheckResult:
    session = _read(paths.session_pointer)
    plan = _read(paths.plan)
    phase = _extract_table_field(session, "Phase").lower()
    nxt = _extract_table_field(session, "Next").lower()
    focus = _extract_plan_focus(plan).lower()
    if not phase and not nxt:
        return CheckResult(
            check_id="DRIFT-004",
            severity=Severity.P1,
            passed=True,
            detail="session-pointer Phase/Next empty — skipped",
        )
    phase_ok = not phase or any(token in focus for token in phase.split() if len(token) > 3)
    next_ok = not nxt or any(token in focus for token in nxt.split() if len(token) > 3)
    passed = phase_ok or next_ok or not focus.strip()
    detail_parts: list[str] = []
    if not passed:
        detail_parts.append(f"Phase={phase!r} Next={next!r} not reflected in plan focus")
    else:
        detail_parts.append("session-pointer aligns with plan focus")
    return CheckResult(
        check_id="DRIFT-004",
        severity=Severity.P1,
        passed=passed,
        detail="; ".join(detail_parts),
    )


def check_drift005(paths: DriftPaths) -> CheckResult:
    status_text = _read(paths.implementation_status)
    doc_count = _parse_implementation_test_count(status_text)
    if doc_count is None:
        return CheckResult(
            check_id="DRIFT-005",
            severity=Severity.P1,
            passed=False,
            detail="IMPLEMENTATION-STATUS missing **Tests:** count",
        )
    actual = _collect_pytest_count(paths.root)
    if actual < 0:
        return CheckResult(
            check_id="DRIFT-005",
            severity=Severity.P1,
            passed=False,
            detail="pytest --collect-only failed",
        )
    passed = doc_count == actual
    return CheckResult(
        check_id="DRIFT-005",
        severity=Severity.P1,
        passed=passed,
        detail=(
            f"test count matches ({actual})"
            if passed
            else f"doc={doc_count} pytest={actual}"
        ),
    )


def check_drift006(paths: DriftPaths) -> CheckResult:
    text = _read(paths.test_index)
    owned = _parse_owned_test_paths(text)
    if not owned:
        return CheckResult(
            check_id="DRIFT-006",
            severity=Severity.P2,
            passed=True,
            detail="no Owned tests entries in test-index",
        )
    missing: list[str] = []
    for rel in owned:
        for part in re.split(r",\s*", rel):
            part = part.strip().strip("`")
            if not part:
                continue
            if not _path_exists(paths.root, part):
                missing.append(part)
    passed = not missing
    return CheckResult(
        check_id="DRIFT-006",
        severity=Severity.P2,
        passed=passed,
        detail=(
            "all Owned tests paths resolve"
            if passed
            else f"missing: {', '.join(missing)}"
        ),
    )


def check_drift007(paths: DriftPaths) -> CheckResult:
    porcelain = _git_porcelain(paths.root)
    if not porcelain:
        return CheckResult(
            check_id="DRIFT-007",
            severity=Severity.P2,
            passed=True,
            detail="git tree clean — skipped",
        )
    if not paths.updates_log.is_file():
        return CheckResult(
            check_id="DRIFT-007",
            severity=Severity.P2,
            passed=False,
            detail="git dirty but updates-log missing",
        )
    age_days = (time.time() - paths.updates_log.stat().st_mtime) / 86400
    passed = age_days <= 7
    return CheckResult(
        check_id="DRIFT-007",
        severity=Severity.P2,
        passed=passed,
        detail=(
            f"updates-log touched {age_days:.1f}d ago"
            if passed
            else f"updates-log stale ({age_days:.1f}d) with dirty tree"
        ),
    )


def check_drift008(paths: DriftPaths) -> CheckResult:
    required = [paths.session_pointer, paths.plan, paths.work_tracker]
    missing = [p.relative_to(paths.root) for p in required if not p.is_file()]
    passed = not missing
    return CheckResult(
        check_id="DRIFT-008",
        severity=Severity.P2,
        passed=passed,
        detail=(
            "scaffold trackers present"
            if passed
            else f"missing: {', '.join(str(m) for m in missing)}"
        ),
    )


KIT_DEV_CHECKS = (
    check_drift001,
    check_drift002,
    check_drift003,
    check_drift004,
    check_drift005,
    check_drift006,
    check_drift007,
    check_drift008,
)

CONSUMER_CHECKS = (
    check_drift005,
    check_drift008,
)
