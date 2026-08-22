"""
File: drift_cli.py
Path: .ai_infra/install/agent_colony/drift_cli.py
Role: CLI handlers for drift subcommands (workflow drift validate).
Used By:
 - .ai_infra/install/agent_colony/cli.py
Depends On:
 - .ai_infra/scripts/workflow/check_drift.py
Notes:
 - Adds scripts/workflow to sys.path for consumer installs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_check_drift(root: Path):
    workflow_dir = root / ".ai_infra" / "scripts" / "workflow"
    if not workflow_dir.is_dir():
        raise FileNotFoundError(f"missing {workflow_dir}")
    workflow_str = str(workflow_dir)
    if workflow_str not in sys.path:
        sys.path.insert(0, workflow_str)
    import check_drift

    return check_drift


def cmd_drift_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        check_drift = _import_check_drift(root)
    except FileNotFoundError as exc:
        print(f"drift validate: FAIL — {exc}", file=sys.stderr)
        return 1

    profile = check_drift.resolve_profile(root, args.profile)
    results = check_drift.run_checks(root, args.profile)
    if args.json:
        import json

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
            "exit_code": check_drift.exit_code_for(results, profile=profile),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(check_drift.format_report(results, profile=profile))
    return check_drift.exit_code_for(results, profile=profile)


def register_drift_subparser(sub: argparse._SubParsersAction) -> None:
    drift = sub.add_parser(
        "drift",
        help="Operational workflow drift checks",
    )
    drift_sub = drift.add_subparsers(dest="drift_command", required=True)

    validate_cmd = drift_sub.add_parser(
        "validate",
        help="Validate plan/tracker/session coherence and handoff parity",
    )
    validate_cmd.add_argument("--directory", type=Path, default=".")
    validate_cmd.add_argument(
        "--profile",
        choices=("kit-dev", "consumer"),
        default=None,
        help="Override auto-detected profile",
    )
    validate_cmd.add_argument("--json", action="store_true", help="Emit JSON report")
    validate_cmd.set_defaults(func=cmd_drift_validate)
