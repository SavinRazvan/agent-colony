"""
File: check_drift.py
Path: .ai_infra/scripts/workflow/check_drift.py
Role: Machine-enforced operational workflow drift checks (drift validate).
Used By:
 - cursor_workflow drift validate
 - scripts/integration/validate.py (INT-012)
 - workflow_mcp workflow_drift_validate
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
Notes:
 - Exit code 1 when any P0 check fails; P1/P2 are advisory in output only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        ensure_paths_import(__file__)
        break

from drift_checks import (  # noqa: E402
    CONSUMER_CHECKS,
    KIT_DEV_CHECKS,
    CheckResult,
    Severity,
    detect_profile,
    drift_paths,
)


def run_checks(root: Path | None = None, profile: str | None = None) -> list[CheckResult]:
    project_root = (root or Path.cwd()).resolve()
    paths = drift_paths(project_root)
    tracker_text = paths.work_tracker.read_text(encoding="utf-8") if paths.work_tracker.is_file() else ""
    resolved = detect_profile(tracker_text, profile)
    checks = CONSUMER_CHECKS if resolved == "consumer" else KIT_DEV_CHECKS
    return [check(paths) for check in checks]


def format_report(results: list[CheckResult], *, profile: str = "kit-dev") -> str:
    lines: list[str] = [f"profile: {profile}"]
    p0_fail = p1_fail = p2_fail = 0
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        if not result.passed:
            if result.severity == Severity.P0:
                p0_fail += 1
            elif result.severity == Severity.P1:
                p1_fail += 1
            else:
                p2_fail += 1
        lines.append(f"[{result.severity.value}] {result.check_id} {status}: {result.detail}")
    lines.append(
        f"summary: p0_fail={p0_fail} p1_fail={p1_fail} p2_fail={p2_fail} total={len(results)}"
    )
    return "\n".join(lines)


def exit_code_for(results: list[CheckResult]) -> int:
    return 1 if any(not r.passed and r.severity == Severity.P0 for r in results) else 0


def resolve_profile(root: Path, override: str | None) -> str:
    paths = drift_paths(root)
    tracker_text = paths.work_tracker.read_text(encoding="utf-8") if paths.work_tracker.is_file() else ""
    return detect_profile(tracker_text, override)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Operational workflow drift validate")
    parser.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Project root (default: current directory)",
    )
    parser.add_argument(
        "--profile",
        choices=("kit-dev", "consumer"),
        default=None,
        help="Override auto-detected profile",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    args = parser.parse_args(argv)

    project_root = args.directory.resolve()
    profile = resolve_profile(project_root, args.profile)
    results = run_checks(project_root, args.profile)

    if args.json:
        payload = {
            "profile": profile,
            "results": [
                {
                    "check_id": r.check_id,
                    "severity": r.severity.value,
                    "passed": r.passed,
                    "detail": r.detail,
                }
                for r in results
            ],
            "exit_code": exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(format_report(results, profile=profile))
    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
