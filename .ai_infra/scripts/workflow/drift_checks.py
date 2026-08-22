"""
File: drift_checks.py
Path: .ai_infra/scripts/workflow/drift_checks.py
Role: Individual DRIFT-001…013 (+004b) check functions for workflow drift validation.
Used By:
 - .ai_infra/scripts/workflow/check_drift.py
Depends On:
 - subprocess, re, datetime (stdlib)
Notes:
 - Does not duplicate governance, integrate, or test-artifact scanners (ADR-007).
 - DRIFT-014–016 token-efficiency checks (ADR-007 overlap table).
"""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

_AI_INFRA = Path(__file__).resolve().parents[2]
if str(_AI_INFRA) not in sys.path:
    sys.path.insert(0, str(_AI_INFRA))
from paths import resolve_project_python  # noqa: E402

_INSTALL_PKG = _AI_INFRA / "install" / "agent_colony"
if str(_INSTALL_PKG) not in sys.path:
    sys.path.insert(0, str(_INSTALL_PKG))
from markdown_sections import section_block as _section_block  # noqa: E402


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


def _resolve_updates_log(root: Path) -> Path:
    current = root / ".local" / "index-and-planning" / "current" / "updates-log.md"
    history = root / ".local" / "index-and-planning" / "history" / "updates-log.md"
    return current if current.is_file() else history if history.is_file() else current


def drift_paths(root: Path) -> DriftPaths:
    planning = root / ".local" / "index-and-planning" / "current"
    return DriftPaths(
        root=root,
        planning_dir=planning,
        plan=planning / "plan.md",
        work_tracker=planning / "work-tracker.md",
        session_pointer=planning / "session-pointer.md",
        updates_log=_resolve_updates_log(root),
        test_index=planning / "test-index.md",
        implementation_status=root / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md",
    )


def detect_profile(
    work_tracker_text: str, override: str | None = None, *, board_only: bool = False
) -> str:
    """
    Resolve drift profile.

    - Explicit override wins.
    - Consumer installs (STARTER-001): `consumer-board` when board_only, else `consumer`.
    - Kit product repo stays `kit-dev` even when board_only is enabled.
    """
    if override in ("kit-dev", "consumer", "consumer-board"):
        return override
    if "STARTER-001" in work_tracker_text:
        return "consumer-board" if board_only else "consumer"
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
    for line in _section_block(text, "Active").splitlines():
        if "`in_progress`" in line:
            match = re.search(r"\*\*([^*]+)\*\*", line)
            if match:
                return match.group(1).strip()
    return None


def _count_in_progress(text: str) -> int:
    return _section_block(text, "Active").count("`in_progress`")


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
        [resolve_project_python(root), "-m", "pytest", "--collect-only", "-q"],
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
            if not part or "..." in part or any(ch in part for ch in "<>{}"):
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


def _git_ls_files(root: Path) -> list[str]:
    if not (root / ".git").is_dir():
        return []
    proc = subprocess.run(
        ["git", "ls-files"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode != 0:
        return []
    return [line.strip() for line in proc.stdout.splitlines() if line.strip()]


def _is_tracked_runtime_path(rel: str) -> bool:
    if rel.startswith(".local/"):
        return True
    if rel.startswith(".venv/"):
        return True
    if rel == ".cursor/mcp.user.json":
        return True
    if rel == ".env":
        return True
    if rel.startswith(".env.") and rel != ".env.example":
        return True
    return False


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
    ssot, _ = _load_ssot_policy(paths)
    if isinstance(ssot, dict) and str(ssot.get("sync_policy") or "") == "board_only":
        return CheckResult(
            check_id="DRIFT-003",
            severity=Severity.P1,
            passed=True,
            detail="board_only — tracker Active skipped",
        )
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
        detail_parts.append(f"Phase={phase!r} Next={nxt!r} not reflected in plan focus")
    else:
        detail_parts.append("session-pointer aligns with plan focus")
    return CheckResult(
        check_id="DRIFT-004",
        severity=Severity.P1,
        passed=passed,
        detail="; ".join(detail_parts),
    )


_ACTIVE_POINTER_STATUSES = frozenset(
    {"in_progress", "in_review", "ready", "todo", "backlog"}
)
_DONE_POINTER_STATUSES = frozenset({"done", "complete", "completed", "closed"})


def _normalize_status_token(raw: str) -> str:
    return re.sub(r"\s+", "_", (raw or "").strip().lower())


def _parse_session_board_field(board_cell: str) -> tuple[str | None, str]:
    """Return (item_id, status_claim) from session-pointer Board cell."""
    cell = (board_cell or "").strip()
    if not cell:
        return None, ""
    m = re.search(r"(PVTI_[A-Za-z0-9_-]+)", cell)
    if not m:
        return None, ""
    item_id = m.group(1)
    # Strip markdown backticks left when cell is like `PVTI_…` Done
    rest = (cell[: m.start()] + cell[m.end() :]).strip(" -–—|,;`")
    return item_id, rest


def _load_ssot_policy(paths: DriftPaths) -> tuple[dict | None, str]:
    """Load project_ssot dict or None + skip/fail reason."""
    collab = paths.root / ".local" / "user_settings" / "github.collaboration.yaml"
    if not collab.is_file():
        return None, "no github.collaboration.yaml — skipped"
    try:
        import yaml
    except ImportError:
        return None, "PyYAML missing — skipped"
    try:
        data = yaml.safe_load(collab.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return None, f"cannot parse collab YAML: {exc}"
    if not isinstance(data, dict):
        return None, "collab YAML not a mapping — skipped"
    ssot = data.get("project_ssot")
    if not isinstance(ssot, dict) or not ssot.get("enabled"):
        return None, "project_ssot disabled or absent — skipped"
    return ssot, "ok"


def check_drift004b(paths: DriftPaths) -> CheckResult:
    """
    Advisory: session-pointer Board id/Status vs export snapshot (board_only).
    Catches stale 'In progress' pointers when the card is already Done.
    """
    ssot, ssot_detail = _load_ssot_policy(paths)
    if ssot is None:
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail=ssot_detail,
        )
    policy = str(ssot.get("sync_policy") or "")
    if policy != "board_only":
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail=f"sync_policy={policy!r} — board/session check skipped",
        )

    session = _read(paths.session_pointer)
    board_cell = _extract_table_field(session, "Board")
    item_id, status_claim = _parse_session_board_field(board_cell)
    if not item_id:
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail="no Board item id in session-pointer — skipped",
        )

    snapshot, snap_detail = _load_board_snapshot(paths)
    if snapshot is None:
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail=f"skipped — {snap_detail}",
        )

    items = snapshot.get("items") if isinstance(snapshot.get("items"), list) else []
    match: dict | None = None
    for item in items:
        if isinstance(item, dict) and str(item.get("id") or "") == item_id:
            match = item
            break
    if match is None:
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=False,
            detail=f"session Board {item_id} missing from export snapshot",
        )

    snap_status = _normalize_status_token(
        str(
            match.get("status_normalized")
            or match.get("status")
            or ""
        )
    )
    pointer_status = _normalize_status_token(status_claim)
    if not pointer_status:
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail=f"Board {item_id} present in snapshot (status={snap_status or 'unknown'})",
        )

    if (
        pointer_status in _ACTIVE_POINTER_STATUSES
        and snap_status in _DONE_POINTER_STATUSES
    ):
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=False,
            detail=(
                f"session Board {item_id} claims {pointer_status} "
                f"but snapshot is {snap_status}"
            ),
        )

    if pointer_status == snap_status or (
        pointer_status in _DONE_POINTER_STATUSES
        and snap_status in _DONE_POINTER_STATUSES
    ):
        return CheckResult(
            check_id="DRIFT-004b",
            severity=Severity.P1,
            passed=True,
            detail=f"session Board {item_id} status aligns with snapshot ({snap_status})",
        )

    return CheckResult(
        check_id="DRIFT-004b",
        severity=Severity.P1,
        passed=False,
        detail=(
            f"session Board {item_id} status={pointer_status} "
            f"vs snapshot={snap_status}"
        ),
    )


def check_drift005(paths: DriftPaths) -> CheckResult:
    if not paths.implementation_status.is_file():
        return CheckResult(
            check_id="DRIFT-005",
            severity=Severity.P2,
            passed=True,
            detail="IMPLEMENTATION-STATUS absent — test count check skipped (consumer install)",
        )
    status_text = _read(paths.implementation_status)
    doc_count = _parse_implementation_test_count(status_text)
    if doc_count is None:
        return CheckResult(
            check_id="DRIFT-005",
            severity=Severity.P1,
            passed=False,
            detail="IMPLEMENTATION-STATUS present but missing **Tests:** count",
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


def check_drift009(paths: DriftPaths) -> CheckResult:
    """Advisory: board_only SSOT must not dual-write tracker in_progress."""
    collab = paths.root / ".local" / "user_settings" / "github.collaboration.yaml"
    if not collab.is_file():
        return CheckResult(
            check_id="DRIFT-009",
            severity=Severity.P1,
            passed=True,
            detail="no github.collaboration.yaml — skipped",
        )
    try:
        import yaml
    except ImportError:
        return CheckResult(
            check_id="DRIFT-009",
            severity=Severity.P1,
            passed=True,
            detail="PyYAML missing — skipped",
        )
    try:
        data = yaml.safe_load(collab.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            check_id="DRIFT-009",
            severity=Severity.P1,
            passed=False,
            detail=f"cannot parse collab YAML: {exc}",
        )
    ssot = data.get("project_ssot") if isinstance(data, dict) else None
    if not isinstance(ssot, dict) or not ssot.get("enabled"):
        return CheckResult(
            check_id="DRIFT-009",
            severity=Severity.P1,
            passed=True,
            detail="project_ssot disabled or absent — skipped",
        )
    policy = str(ssot.get("sync_policy") or "")
    if policy != "board_only":
        return CheckResult(
            check_id="DRIFT-009",
            severity=Severity.P1,
            passed=True,
            detail=f"sync_policy={policy!r} — dual-write check skipped",
        )
    tracker = _read(paths.work_tracker)
    count = len(re.findall(r"`in_progress`", _section_block(tracker, "Active")))
    passed = count == 0
    return CheckResult(
        check_id="DRIFT-009",
        severity=Severity.P1,
        passed=passed,
        detail=(
            "board_only: no competing tracker in_progress"
            if passed
            else f"board_only dual-write risk: {count} tracker in_progress under Active — use board Status only"
        ),
    )


def _load_board_snapshot(paths: DriftPaths) -> tuple[dict | None, str]:
    """Load read-only export if present; else None + reason."""
    snap = (
        paths.root
        / ".local"
        / "generated-data"
        / "project-board-snapshot.json"
    )
    if not snap.is_file():
        return None, "no project-board-snapshot.json (run: python -m agent_colony project export)"
    try:
        import json

        data = json.loads(snap.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return None, f"cannot read snapshot: {exc}"
    if not isinstance(data, dict):
        return None, "snapshot is not an object"
    return data, "ok"


def _open_pr_bodies(repo: str) -> tuple[list[dict], str | None]:
    """Return open PRs as dicts with number, url, body — or error."""
    import json
    import subprocess

    cmd = [
        "gh",
        "pr",
        "list",
        "--repo",
        repo,
        "--state",
        "open",
        "--json",
        "number,url,body,title",
        "--limit",
        "50",
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=45, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], str(exc)
    if proc.returncode != 0:
        return [], (proc.stderr or proc.stdout or "gh pr list failed").strip()
    try:
        data = json.loads(proc.stdout or "[]")
    except json.JSONDecodeError as exc:
        return [], f"invalid JSON from gh pr list: {exc}"
    if not isinstance(data, list):
        return [], "gh pr list did not return a list"
    return [p for p in data if isinstance(p, dict)], None


def check_drift010(paths: DriftPaths) -> CheckResult:
    """
    Advisory: board Status vs open PRs / stale In progress (board_only).
    Uses read-only snapshot when present; skips offline without failing P0.
    """
    collab = paths.root / ".local" / "user_settings" / "github.collaboration.yaml"
    if not collab.is_file():
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail="no github.collaboration.yaml — skipped",
        )
    try:
        import yaml
    except ImportError:
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail="PyYAML missing — skipped",
        )
    try:
        data = yaml.safe_load(collab.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=False,
            detail=f"cannot parse collab YAML: {exc}",
        )
    ssot = data.get("project_ssot") if isinstance(data, dict) else None
    if not isinstance(ssot, dict) or not ssot.get("enabled"):
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail="project_ssot disabled or absent — skipped",
        )
    policy = str(ssot.get("sync_policy") or "")
    if policy != "board_only":
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail=f"sync_policy={policy!r} — board/PR check skipped",
        )

    snapshot, snap_detail = _load_board_snapshot(paths)
    if snapshot is None:
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail=f"skipped — {snap_detail}",
        )

    items = snapshot.get("items") if isinstance(snapshot.get("items"), list) else []
    repo = str(ssot.get("default_repo") or "")
    if not repo:
        proj = snapshot.get("project") if isinstance(snapshot.get("project"), dict) else {}
        repo = str(proj.get("default_repo") or "")

    open_prs: list[dict] = []
    pr_err: str | None = None
    if repo:
        open_prs, pr_err = _open_pr_bodies(repo)
        if pr_err:
            return CheckResult(
                check_id="DRIFT-010",
                severity=Severity.P1,
                passed=True,
                detail=f"skipped — cannot list open PRs: {pr_err}",
            )

    # Build set of Board-Item ids referenced by open PRs + PR numbers mentioned
    open_item_ids: set[str] = set()
    open_pr_nums: set[str] = set()
    for pr in open_prs:
        open_pr_nums.add(str(pr.get("number") or ""))
        body = str(pr.get("body") or "")
        m = re.search(r"(?i)Board-Item:\s*(PVTI_[A-Za-z0-9_-]+)", body)
        if m:
            open_item_ids.add(m.group(1))

    findings: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id") or "")
        status = str(
            item.get("status_normalized")
            or str(item.get("status") or "").strip().lower().replace(" ", "_")
        )
        title = str(item.get("title") or item_id)
        excerpt = str(item.get("body_excerpt") or "")

        if status == "in_review":
            if repo and not pr_err and not open_prs:
                findings.append(f"WARN in_review with 0 open PRs: {title} ({item_id})")
                continue
            # In review should have an open PR referencing this item or mentioning the card
            linked = item_id in open_item_ids
            mentioned = any(
                f"/pull/{n}" in excerpt or f"#{n}" in excerpt for n in open_pr_nums if n
            )
            if open_prs and not linked and not mentioned:
                # Also OK if any open PR body mentions this item id
                if not any(item_id and item_id in str(p.get("body") or "") for p in open_prs):
                    findings.append(f"in_review without open PR: {title} ({item_id})")

        if status == "in_progress":
            # Stale if no open PR references this card and Notes lack a recent handoff marker
            linked = item_id in open_item_ids
            has_pr_mention = any(
                f"/pull/{n}" in excerpt or f"#{n}" in excerpt for n in open_pr_nums if n
            )
            if open_prs is not None and repo and not linked and not has_pr_mention:
                # Soft stale signal: In progress with no PR link when repo has open PRs elsewhere
                # Only flag when there are open PRs in the repo but none tied to this card —
                # and excerpt has no "next=" handoff (still actively worked mid-slice is OK).
                if "next=" not in excerpt.lower() and "Merged:" not in excerpt:
                    # Don't flag every In progress — only when excerpt looks abandoned (empty Notes)
                    if not excerpt.strip() or excerpt.strip() in ("...", "(TBD)"):
                        findings.append(
                            f"stale in_progress (empty Notes, no open PR link): {title} ({item_id})"
                        )

    # Merged-but-not-Done is hard without merged PR list; use Notes heuristic:
    # if Status still in_review/in_progress but body has Merged: line → drift
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(
            item.get("status_normalized")
            or str(item.get("status") or "").strip().lower().replace(" ", "_")
        )
        excerpt = str(item.get("body_excerpt") or "")
        if status in ("in_review", "in_progress") and "Merged:" in excerpt:
            findings.append(
                f"merged-but-not-done: {item.get('title')} ({item.get('id')})"
            )

    if not findings:
        return CheckResult(
            check_id="DRIFT-010",
            severity=Severity.P1,
            passed=True,
            detail="board Status vs open PRs — no mismatches",
        )
    return CheckResult(
        check_id="DRIFT-010",
        severity=Severity.P1,
        passed=False,
        detail="; ".join(findings[:5]) + (f" (+{len(findings) - 5} more)" if len(findings) > 5 else ""),
    )


# Live kit agent ids (post B-safe rename). Keep in sync with AGENTS.md / DOC-008.
LIVE_KIT_AGENT_IDS: frozenset[str] = frozenset(
    {
        "auditor",
        "board",
        "drift-guard",
        "implementer",
        "integrator",
        "researcher",
        "test-runner",
        "verifier",
    }
)


def check_drift011(paths: DriftPaths) -> CheckResult:
    """
    Goal/doctrine pulse (falsifiable): `.cursor/agents/*.md` basenames must equal
    the eight live kit agent ids. Missing/extra agents = doctrine drift.
    """
    agents_dir = paths.root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return CheckResult(
            check_id="DRIFT-011",
            severity=Severity.P1,
            passed=False,
            detail=".cursor/agents/ missing — cannot verify agent roster",
        )
    on_disk = {p.stem for p in agents_dir.glob("*.md") if p.is_file()}
    missing = sorted(LIVE_KIT_AGENT_IDS - on_disk)
    extra = sorted(on_disk - LIVE_KIT_AGENT_IDS)
    if not missing and not extra:
        return CheckResult(
            check_id="DRIFT-011",
            severity=Severity.P1,
            passed=True,
            detail=f"agent roster coherent ({len(LIVE_KIT_AGENT_IDS)} live ids)",
        )
    parts: list[str] = []
    if missing:
        parts.append(f"missing={','.join(missing)}")
    if extra:
        parts.append(f"extra={','.join(extra)}")
    return CheckResult(
        check_id="DRIFT-011",
        severity=Severity.P1,
        passed=False,
        detail="; ".join(parts),
    )


def check_drift012(paths: DriftPaths) -> CheckResult:
    """Advisory: .local/plans/ must not host live/current plan SSOT under board_only."""
    collab = paths.root / ".local" / "user_settings" / "github.collaboration.yaml"
    if not collab.is_file():
        return CheckResult(
            check_id="DRIFT-012",
            severity=Severity.P2,
            passed=True,
            detail="no github.collaboration.yaml — skipped",
        )
    try:
        import yaml
    except ImportError:
        return CheckResult(
            check_id="DRIFT-012",
            severity=Severity.P2,
            passed=True,
            detail="PyYAML missing — skipped",
        )
    try:
        data = yaml.safe_load(collab.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            check_id="DRIFT-012",
            severity=Severity.P2,
            passed=False,
            detail=f"cannot parse collab YAML: {exc}",
        )
    ssot = data.get("project_ssot") if isinstance(data, dict) else None
    if not isinstance(ssot, dict) or not ssot.get("enabled"):
        return CheckResult(
            check_id="DRIFT-012",
            severity=Severity.P2,
            passed=True,
            detail="project_ssot disabled — skipped",
        )
    if str(ssot.get("sync_policy") or "") != "board_only":
        return CheckResult(
            check_id="DRIFT-012",
            severity=Severity.P2,
            passed=True,
            detail="sync_policy not board_only — skipped",
        )

    plans_dir = paths.root / ".local" / "plans"
    issues: list[str] = []
    if plans_dir.is_dir():
        for path in plans_dir.iterdir():
            if path.is_file() and "current" in path.name.lower():
                issues.append(f"live-plan filename: {path.name}")
        index = plans_dir / "index.md"
        if index.is_file():
            for line in index.read_text(encoding="utf-8").splitlines():
                lower = line.lower()
                if lower.startswith("|") and " active " in f" {lower} ":
                    issues.append("index row marks plan as active")

    passed = not issues
    return CheckResult(
        check_id="DRIFT-012",
        severity=Severity.P2,
        passed=passed,
        detail=(
            "board_only: .local/plans/ is snapshot-only"
            if passed
            else "; ".join(issues)
        ),
    )


_RECOVERY_HINT = (
    "recovery: .ai_infra/docs/operations/upgrade-kit.md "
    "(git rm -r --cached .local .venv)"
)


def check_drift013(paths: DriftPaths) -> CheckResult:
    """Fail when git index tracks private runtime paths (.local/, secrets, venv)."""
    tracked = _git_ls_files(paths.root)
    if not tracked and not (paths.root / ".git").is_dir():
        return CheckResult(
            check_id="DRIFT-013",
            severity=Severity.P1,
            passed=True,
            detail="not a git repo — skipped",
        )
    forbidden = sorted(p for p in tracked if _is_tracked_runtime_path(p))
    if forbidden:
        sample = ", ".join(forbidden[:5])
        suffix = f" (+{len(forbidden) - 5} more)" if len(forbidden) > 5 else ""
        return CheckResult(
            check_id="DRIFT-013",
            severity=Severity.P1,
            passed=False,
            detail=f"tracked runtime paths: {sample}{suffix}; {_RECOVERY_HINT}",
        )
    return CheckResult(
        check_id="DRIFT-013",
        severity=Severity.P1,
        passed=True,
        detail="no tracked .local/, .venv/, .env, or mcp.user.json",
    )


def check_drift011b(paths: DriftPaths) -> CheckResult:
    """
    Consumer advisory: extra `.cursor/agents/*.md` beyond the eight kit ids.
    Always passes; surfaces integrator extensions that full upgrade may overwrite.
    """
    agents_dir = paths.root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return CheckResult(
            check_id="DRIFT-011b",
            severity=Severity.P2,
            passed=True,
            detail=".cursor/agents/ missing — skipped",
        )
    on_disk = {p.stem for p in agents_dir.glob("*.md") if p.is_file()}
    extra = sorted(on_disk - LIVE_KIT_AGENT_IDS)
    if not extra:
        return CheckResult(
            check_id="DRIFT-011b",
            severity=Severity.P2,
            passed=True,
            detail=f"no extra agents ({len(LIVE_KIT_AGENT_IDS)} kit ids only)",
        )
    return CheckResult(
        check_id="DRIFT-011b",
        severity=Severity.P2,
        passed=True,
        detail=(
            f"extra integrator agents (advisory): {','.join(extra)} — "
            "commit team-owned; full update may overwrite non-payload files"
        ),
    )


TOKEN_EFFICIENCY_ANCHOR = "token-efficiency.md"

LITE_AGENT_ALLOWLIST: frozenset[str] = frozenset(
    {
        "board",
        "implementer",
        "test-runner",
        "verifier",
        "drift-guard",
        "integrator",
    }
)

LITE_SKILL_ALLOWLIST: frozenset[str] = frozenset(
    {
        "board-ssot",
        "implementer-loop",
        "evidence-first",
        "test-coverage",
        "workflow-activate",
        "mcp-connect",
    }
)


def _load_install_profile(root: Path) -> str | None:
    marker = root / ".local" / "generated-data" / "install-profile.json"
    if not marker.is_file():
        return None
    try:
        import json

        data = json.loads(marker.read_text(encoding="utf-8"))
        return str(data.get("profile") or "") or None
    except (json.JSONDecodeError, OSError):
        return None


def _expected_agent_ids(paths: DriftPaths) -> set[str]:
    profile = _load_install_profile(paths.root)
    if profile == "consumer_lite":
        return set(LITE_AGENT_ALLOWLIST)
    if paths.implementation_status.is_file():
        return set(LIVE_KIT_AGENT_IDS)
    agents_dir = paths.root / ".cursor" / "agents"
    if agents_dir.is_dir():
        return {p.stem for p in agents_dir.glob("*.md") if p.is_file()}
    return set(LIVE_KIT_AGENT_IDS)


def check_drift014(paths: DriftPaths) -> CheckResult:
    """Token-efficiency anchor in installed agent cards (profile-aware)."""
    agents_dir = paths.root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        if not paths.implementation_status.is_file():
            return CheckResult(
                check_id="DRIFT-014",
                severity=Severity.P1,
                passed=True,
                detail=".cursor/agents/ missing — skipped (consumer install)",
            )
        return CheckResult(
            check_id="DRIFT-014",
            severity=Severity.P1,
            passed=False,
            detail="missing .cursor/agents/",
        )
    expected = _expected_agent_ids(paths)
    missing_anchor: list[str] = []
    for agent_id in sorted(expected):
        path = agents_dir / f"{agent_id}.md"
        if not path.is_file():
            missing_anchor.append(f"{agent_id}: missing file")
            continue
        if TOKEN_EFFICIENCY_ANCHOR not in path.read_text(encoding="utf-8"):
            missing_anchor.append(agent_id)
    if missing_anchor:
        return CheckResult(
            check_id="DRIFT-014",
            severity=Severity.P1,
            passed=False,
            detail=f"missing token-efficiency anchor: {', '.join(missing_anchor[:8])}",
        )
    return CheckResult(
        check_id="DRIFT-014",
        severity=Severity.P1,
        passed=True,
        detail=f"token-efficiency anchor in {len(expected)} agent card(s)",
    )


def check_drift015(paths: DriftPaths) -> CheckResult:
    """Kit-dev: WARN when plugin cache rules duplicate workspace rule basenames."""
    import glob
    home = Path.home()
    cache_glob = str(home / ".cursor" / "plugins" / "cache" / "agent-colony" / "agent-colony" / "*" / "rules" / "*.mdc")
    cache_rules = {Path(p).name for p in glob.glob(cache_glob)}
    ws_rules_dir = paths.root / ".cursor" / "rules"
    if not ws_rules_dir.is_dir() or not cache_rules:
        return CheckResult(
            check_id="DRIFT-015",
            severity=Severity.P2,
            passed=True,
            detail="plugin/workspace rule dup check skipped (no cache or no workspace rules)",
        )
    ws_names = {p.name for p in ws_rules_dir.glob("*.mdc")}
    overlap = sorted(cache_rules & ws_names)
    if overlap:
        return CheckResult(
            check_id="DRIFT-015",
            severity=Severity.P2,
            passed=True,
            detail=f"WARN plugin+workspace rule basename overlap: {', '.join(overlap[:6])}",
        )
    return CheckResult(
        check_id="DRIFT-015",
        severity=Severity.P2,
        passed=True,
        detail="no plugin/workspace rule basename overlap",
    )


def check_drift016(paths: DriftPaths) -> CheckResult:
    """Thin-index § headings exist for skills present on disk (profile-aware)."""
    if str(_INSTALL_PKG) not in sys.path:
        sys.path.insert(0, str(_INSTALL_PKG))
    import doc_cli  # noqa: E402

    allowlist: set[str] | None = None
    if _load_install_profile(paths.root) == "consumer_lite":
        allowlist = set(LITE_SKILL_ALLOWLIST)
    rows = doc_cli._parse_thin_index_rows(paths.root)
    if not rows:
        if not paths.implementation_status.is_file():
            return CheckResult(
                check_id="DRIFT-016",
                severity=Severity.P1,
                passed=True,
                detail="thin-index absent — skipped (consumer install)",
            )
        return CheckResult(
            check_id="DRIFT-016",
            severity=Severity.P1,
            passed=False,
            detail="token-efficiency thin-index table missing or empty",
        )
    failures: list[str] = []
    skipped = 0
    for row in rows:
        skill_id = row["skill"]
        if allowlist is not None and skill_id not in allowlist:
            skipped += 1
            continue
        if doc_cli._find_skill_path(paths.root, skill_id) is None:
            if allowlist is not None:
                skipped += 1
                continue
            failures.append(f"{skill_id}: missing on disk")
            continue
        failures.extend(doc_cli._validate_skill_prefer(paths.root, skill_id, row["prefer"]))
    if failures:
        return CheckResult(
            check_id="DRIFT-016",
            severity=Severity.P1,
            passed=False,
            detail=f"thin-index failures ({len(failures)}): {failures[0]}",
        )
    return CheckResult(
        check_id="DRIFT-016",
        severity=Severity.P1,
        passed=True,
        detail=f"thin-index parity ok (skipped={skipped})",
    )


KIT_DEV_CHECKS = (
    check_drift001,
    check_drift002,
    check_drift003,
    check_drift004,
    check_drift004b,
    check_drift005,
    check_drift006,
    check_drift007,
    check_drift008,
    check_drift009,
    check_drift010,
    check_drift011,
    check_drift012,
    check_drift013,
    check_drift014,
    check_drift015,
    check_drift016,
)

CONSUMER_CHECKS = (
    check_drift005,
    check_drift008,
    check_drift013,
    check_drift011b,
    check_drift014,
    check_drift016,
)

CONSUMER_BOARD_CHECKS = (
    check_drift005,
    check_drift008,
    check_drift009,
    check_drift010,
    check_drift012,
    check_drift013,
    check_drift011b,
    check_drift014,
    check_drift016,
)
