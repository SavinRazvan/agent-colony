"""
File: verify_cli.py
Path: .ai_infra/install/cursor_workflow/verify_cli.py
Role: CLI handlers for verify subcommands (maintainer verify-all matrix).
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - .ai_infra/scripts/architecture/verify_all.py
Notes:
 - Mirrors kit-quality.yml gate matrix for local maintainer runs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_verify_all(root: Path):
    arch_dir = root / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        raise FileNotFoundError(f"missing {arch_dir}")
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import verify_all

    return verify_all


def cmd_verify_all(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        verify_all = _import_verify_all(root)
    except FileNotFoundError as exc:
        print(f"verify all: FAIL — {exc}", file=sys.stderr)
        return 1

    preflight = args.preflight_out
    if preflight is None and args.write_preflight:
        preflight = root / ".local" / "workflow-artifacts" / "audit" / "preflight.json"

    results = verify_all.run_verify_all(root, sys.executable)
    if preflight is not None:
        verify_all.write_preflight_json(results, preflight)
    if args.json:
        import json

        payload = {
            "steps": [
                {"name": r.name, "exit_code": r.exit_code, "command": r.command}
                for r in results
            ],
            "exit_code": verify_all.exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(verify_all.format_report(results))
    return verify_all.exit_code_for(results)


def register_verify_subparser(sub: argparse._SubParsersAction) -> None:
    verify = sub.add_parser("verify", help="Maintainer verification matrix")
    verify_sub = verify.add_subparsers(dest="verify_command", required=True)

    all_cmd = verify_sub.add_parser(
        "all",
        help="Run sync-plugin, gates, drift, integrate, check-plugin, health, contributors",
    )
    all_cmd.add_argument("--directory", type=Path, default=".")
    all_cmd.add_argument("--json", action="store_true", help="Emit JSON report")
    all_cmd.add_argument(
        "--write-preflight",
        action="store_true",
        help="Write .local/workflow-artifacts/audit/preflight.json",
    )
    all_cmd.add_argument(
        "--preflight-out",
        type=Path,
        default=None,
        help="Custom preflight JSON path",
    )
    all_cmd.set_defaults(func=cmd_verify_all)
