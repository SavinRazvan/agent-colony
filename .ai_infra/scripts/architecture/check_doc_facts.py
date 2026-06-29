"""
File: check_doc_facts.py
Path: .ai_infra/scripts/architecture/check_doc_facts.py
Role: Machine-enforced canonical doc vs repo fact checks (doc validate).
Used By:
 - cursor_workflow doc validate
 - cursor_workflow gates
 - scripts/integration/validate.py (INT-013)
 - workflow_mcp workflow_doc_facts_validate
Depends On:
 - .ai_infra/scripts/architecture/doc_facts_checks.py
Notes:
 - Exit code 1 when any P0 or P1 check fails; P2 advisory in output only.
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

from doc_facts_checks import (  # noqa: E402
    KIT_DEV_CHECKS,
    CheckResult,
    Severity,
    doc_facts_paths,
    is_kit_dev,
)


def run_checks(root: Path | None = None) -> list[CheckResult]:
    project_root = (root or Path.cwd()).resolve()
    if not is_kit_dev(project_root):
        return [
            CheckResult(
                check_id="DOC-000",
                severity=Severity.P2,
                passed=True,
                detail="consumer profile — doc facts skipped",
            )
        ]
    paths = doc_facts_paths(project_root)
    return [check(paths) for check in KIT_DEV_CHECKS]


def format_report(results: list[CheckResult]) -> str:
    lines: list[str] = []
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
    return (
        1
        if any(
            not result.passed and result.severity in (Severity.P0, Severity.P1)
            for result in results
        )
        else 0
    )


def write_preflight_json(results: list[CheckResult], output: Path) -> None:
    payload = {
        "command": "python -m cursor_workflow doc validate",
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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Canonical doc vs repo fact checks")
    parser.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Project root (default: current directory)",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON report")
    parser.add_argument(
        "--preflight-out",
        type=Path,
        default=None,
        help="Write JSON preflight artifact (default: skip)",
    )
    args = parser.parse_args(argv)

    results = run_checks(args.directory.resolve())
    if args.preflight_out is not None:
        write_preflight_json(results, args.preflight_out)
    if args.json:
        payload = {
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
        print(format_report(results))
    return exit_code_for(results)


if __name__ == "__main__":
    raise SystemExit(main())
