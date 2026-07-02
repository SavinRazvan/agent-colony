"""
File: doc_cli.py
Path: .ai_infra/install/cursor_workflow/doc_cli.py
Role: CLI handlers for doc subcommands (canonical doc fact validation).
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - .ai_infra/scripts/architecture/check_doc_facts.py
Notes:
 - Adds scripts/architecture to sys.path for consumer installs.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _import_check_doc_facts(root: Path):
    arch_dir = root / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        raise FileNotFoundError(f"missing {arch_dir}")
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import check_doc_facts

    return check_doc_facts


def cmd_doc_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        check_doc_facts = _import_check_doc_facts(root)
    except FileNotFoundError as exc:
        print(f"doc validate: FAIL — {exc}", file=sys.stderr)
        return 1

    preflight = args.preflight_out
    if preflight is None and args.write_preflight:
        preflight = (
            root
            / ".local"
            / "workflow-artifacts"
            / "audit"
            / "doc-facts-preflight.json"
        )

    results = check_doc_facts.run_checks(root)
    if preflight is not None:
        check_doc_facts.write_preflight_json(results, preflight)
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
            "exit_code": check_doc_facts.exit_code_for(results),
        }
        print(json.dumps(payload, indent=2))
    else:
        print(check_doc_facts.format_report(results))
    return check_doc_facts.exit_code_for(results)


def register_doc_subparser(sub: argparse._SubParsersAction) -> None:
    doc = sub.add_parser("doc", help="Canonical documentation fact checks")
    doc_sub = doc.add_subparsers(dest="doc_command", required=True)

    validate_cmd = doc_sub.add_parser(
        "validate",
        help="Validate README/AGENTS/status docs against repo facts",
    )
    validate_cmd.add_argument("--directory", type=Path, default=".")
    validate_cmd.add_argument("--json", action="store_true", help="Emit JSON report")
    validate_cmd.add_argument(
        "--write-preflight",
        action="store_true",
        help="Write .local/workflow-artifacts/audit/doc-facts-preflight.json",
    )
    validate_cmd.add_argument(
        "--preflight-out",
        type=Path,
        default=None,
        help="Custom preflight JSON path",
    )
    validate_cmd.set_defaults(func=cmd_doc_validate)
