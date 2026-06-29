"""
File: integrate_cli.py
Path: .ai_infra/install/cursor_workflow/integrate_cli.py
Role: CLI handlers for integrate subcommands (integration validate).
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - .ai_infra/scripts/integration/validate.py
Notes:
 - Adds scripts/integration to sys.path for consumer installs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_validate(root: Path):
    integration_dir = root / ".ai_infra" / "scripts" / "integration"
    if not integration_dir.is_dir():
        raise FileNotFoundError(f"missing {integration_dir}")
    integration_str = str(integration_dir)
    if integration_str not in sys.path:
        sys.path.insert(0, integration_str)
    import validate

    return validate


def cmd_integrate_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        validate = _import_validate(root)
    except FileNotFoundError as exc:
        print(f"integrate validate: FAIL — {exc}", file=sys.stderr)
        return 1

    results = validate.run_checks(root)
    if args.json:
        import json

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
            "exit_code": validate.exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(validate.format_report(results))
    return validate.exit_code_for(results)


def register_integrate_subparser(sub: argparse._SubParsersAction) -> None:
    integrate = sub.add_parser(
        "integrate",
        help="MAS infrastructure integration checks",
    )
    integrate_sub = integrate.add_subparsers(dest="integrate_command", required=True)

    validate_cmd = integrate_sub.add_parser(
        "validate",
        help="Validate agent/registry/pipeline parity and user_settings schemas",
    )
    validate_cmd.add_argument("--directory", type=Path, default=".")
    validate_cmd.add_argument("--json", action="store_true", help="Emit JSON report")
    validate_cmd.set_defaults(func=cmd_integrate_validate)
