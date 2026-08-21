"""
File: doc_cli.py
Path: .ai_infra/install/agent_colony/doc_cli.py
Role: CLI handlers for doc subcommands (canonical doc fact validation + digests).
Used By:
 - .ai_infra/install/agent_colony/cli.py
Depends On:
 - .ai_infra/scripts/architecture/check_doc_facts.py
Notes:
 - Adds scripts/architecture to sys.path for consumer installs.
 - roster-digest / summarize support token-efficient agent Entry.
"""

from __future__ import annotations

import argparse
import json
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


def cmd_doc_roster_digest(args: argparse.Namespace) -> int:
    """Print agent id + one-line description (token-efficient roster)."""
    root = Path(args.directory).resolve()
    agents_dir = root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        print(f"doc roster-digest: FAIL — missing {agents_dir}", file=sys.stderr)
        return 1
    rows: list[dict[str, str]] = []
    for path in sorted(agents_dir.glob("*.md")):
        agent_id = path.stem
        desc = ""
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            if line.startswith("description:"):
                desc = line.split(":", 1)[1].strip()
                break
        rows.append({"id": agent_id, "description": desc})
    if args.json:
        print(json.dumps({"agents": rows, "count": len(rows)}, indent=2))
    else:
        print(f"agents={len(rows)}")
        for row in rows:
            short = row["description"]
            if len(short) > 72:
                short = short[:69] + "…"
            print(f"{row['id']}\t{short}")
    return 0


def cmd_doc_summarize(args: argparse.Namespace) -> int:
    """Print first N non-empty lines of a markdown/doc path (token-efficient)."""
    root = Path(args.directory).resolve()
    path = Path(args.path)
    if not path.is_absolute():
        path = (root / path).resolve()
    if not path.is_file():
        print(f"doc summarize: FAIL — missing {path}", file=sys.stderr)
        return 1
    max_lines = int(args.lines)
    lines_out: list[str] = []
    in_comment = False
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            continue
        if not stripped:
            continue
        lines_out.append(line.rstrip())
        if len(lines_out) >= max_lines:
            break
    payload = {
        "path": str(path.relative_to(root) if path.is_relative_to(root) else path),
        "lines": lines_out,
        "truncated": len(lines_out) >= max_lines,
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"path={payload['path']} · lines={len(lines_out)}"
              f"{' · truncated' if payload['truncated'] else ''}")
        for line in lines_out:
            print(line)
    return 0


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

    roster_cmd = doc_sub.add_parser(
        "roster-digest",
        help="Token-efficient agent roster (id + description)",
    )
    roster_cmd.add_argument("--directory", type=Path, default=".")
    roster_cmd.add_argument("--json", action="store_true")
    roster_cmd.set_defaults(func=cmd_doc_roster_digest)

    summarize_cmd = doc_sub.add_parser(
        "summarize",
        help="First N non-empty lines of a doc (token-efficient)",
    )
    summarize_cmd.add_argument("--directory", type=Path, default=".")
    summarize_cmd.add_argument("--path", required=True, help="Repo-relative or absolute path")
    summarize_cmd.add_argument("--lines", type=int, default=40, help="Max non-empty lines")
    summarize_cmd.add_argument("--json", action="store_true")
    summarize_cmd.set_defaults(func=cmd_doc_summarize)
