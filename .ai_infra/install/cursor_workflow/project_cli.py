"""
File: project_cli.py
Path: .ai_infra/install/cursor_workflow/project_cli.py
Role: CLI for GitHub Project SSOT — load project_ssot from collab YAML; drive gh project.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .cursor/skills/project-board-ssot/SKILL.md
 - .cursor/agents/project-board.md
Depends On:
 - .ai_infra/scripts/pr/user_settings.py (load_github_collaboration)
Notes:
 - Pattern A: one gh invocation per action; no dual-write of local trackers.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _import_user_settings(root: Path):
    pr_dir = root / ".ai_infra" / "scripts" / "pr"
    if not pr_dir.is_dir():
        raise FileNotFoundError(f"missing {pr_dir}")
    pr_str = str(pr_dir)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    import user_settings

    return user_settings


def load_project_ssot(root: Path) -> tuple[dict[str, Any] | None, list[str]]:
    """Return (project_ssot dict or None, error messages)."""
    errors: list[str] = []
    try:
        us = _import_user_settings(root)
    except FileNotFoundError as exc:
        return None, [str(exc)]
    cfg = us.load_github_collaboration(root)
    if cfg is None:
        return None, [f"missing or empty {us.GITHUB_COLLAB_REL}"]
    ssot = cfg.get("project_ssot")
    if not isinstance(ssot, dict):
        return None, ["project_ssot: missing block in github.collaboration.yaml"]
    return ssot, errors


def require_enabled(ssot: dict[str, Any]) -> list[str]:
    if not ssot.get("enabled"):
        fallback = ssot.get("fallback", "local_trackers")
        msg = "project_ssot.enabled is false — board SSOT inactive"
        if fallback == "local_trackers":
            msg += "; fallback: local_trackers (.local/index-and-planning/current/)"
        return [msg]
    for key in ("owner", "number", "project_id"):
        if ssot.get(key) in (None, ""):
            return [f"project_ssot.{key} is required when enabled"]
    return []


def resolve_status_option_id(ssot: dict[str, Any], logical: str) -> str:
    fields = ssot.get("fields") or {}
    status = fields.get("status") or {}
    options = status.get("options") or {}
    key = logical.strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "inprogress": "in_progress",
        "in_review": "in_review",
        "review": "in_review",
    }
    key = aliases.get(key, key)
    if key not in options:
        known = ", ".join(sorted(options)) or "(none)"
        raise KeyError(f"unknown status '{logical}' — known: {known}")
    return str(options[key])


def resolve_field_option_id(ssot: dict[str, Any], field: str, logical: str) -> tuple[str, str]:
    """Return (field_id, option_id) for priority or size."""
    fields = ssot.get("fields") or {}
    block = fields.get(field)
    if not isinstance(block, dict):
        raise KeyError(f"project_ssot.fields.{field} missing")
    field_id = block.get("field_id")
    if not field_id:
        raise KeyError(f"project_ssot.fields.{field}.field_id missing")
    options = block.get("options") or {}
    key = logical.strip().lower().replace("-", "_")
    if key not in options:
        known = ", ".join(sorted(options)) or "(none)"
        raise KeyError(f"unknown {field} '{logical}' — known: {known}")
    return str(field_id), str(options[key])


def status_field_id(ssot: dict[str, Any]) -> str:
    fields = ssot.get("fields") or {}
    status = fields.get("status") or {}
    fid = status.get("field_id")
    if not fid:
        raise KeyError("project_ssot.fields.status.field_id missing")
    return str(fid)


def run_gh(args: list[str], *, timeout_s: float = 60.0) -> subprocess.CompletedProcess[str]:
    cmd = ["gh", *args]
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )


def cmd_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project status: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    enabled = not enabled_errs
    payload = {
        "enabled": bool(ssot.get("enabled")),
        "operational": enabled,
        "name": ssot.get("name"),
        "owner": ssot.get("owner"),
        "number": ssot.get("number"),
        "url": ssot.get("url"),
        "project_id": ssot.get("project_id"),
        "default_repo": ssot.get("default_repo"),
        "tool": ssot.get("tool", "gh"),
        "sync_policy": ssot.get("sync_policy"),
        "fallback": ssot.get("fallback"),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"enabled: {payload['enabled']}")
        print(f"operational: {payload['operational']}")
        print(f"name: {payload['name']}")
        print(f"owner: {payload['owner']}")
        print(f"number: {payload['number']}")
        print(f"url: {payload['url']}")
        print(f"project_id: {payload['project_id']}")
        print(f"sync_policy: {payload['sync_policy']}")
        print(f"fallback: {payload['fallback']}")
        if enabled_errs:
            for e in enabled_errs:
                print(f"note: {e}", file=sys.stderr)
    return 0 if enabled else 2


def cmd_list(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project list: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project list: FAIL — {e}", file=sys.stderr)
        return 2
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    proc = run_gh(
        [
            "project",
            "item-list",
            str(number),
            "--owner",
            owner,
            "--format",
            "json",
            "--limit",
            str(args.limit),
        ]
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-list failed", file=sys.stderr)
        return proc.returncode or 1
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        print(f"project list: FAIL — invalid JSON from gh: {exc}", file=sys.stderr)
        return 1
    items = data.get("items") if isinstance(data, dict) else data
    if not isinstance(items, list):
        items = []
    filter_status = (args.status or "").strip().lower().replace("-", "_")
    if filter_status in ("inprogress",):
        filter_status = "in_progress"
    if filter_status in ("review",):
        filter_status = "in_review"
    out_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "").strip().lower().replace(" ", "_")
        if filter_status and status != filter_status:
            continue
        out_items.append(
            {
                "id": item.get("id"),
                "title": item.get("title"),
                "status": item.get("status"),
                "priority": item.get("priority"),
                "size": item.get("size"),
            }
        )
    if args.json:
        print(json.dumps({"items": out_items, "totalCount": len(out_items)}, indent=2))
    else:
        if not out_items:
            print("(no items)")
        for it in out_items:
            print(f"{it.get('id')}\t{it.get('status')}\t{it.get('title')}")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project create: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project create: FAIL — {e}", file=sys.stderr)
        return 2
    owner = str(ssot["owner"])
    number = int(ssot["number"])
    body = args.body or ""
    sections = (ssot.get("conventions") or {}).get("body_sections") or []
    if not body and sections:
        body = "\n\n".join(f"## {s}\n\n(TBD)" for s in sections)
    gh_args = [
        "project",
        "item-create",
        str(number),
        "--owner",
        owner,
        "--title",
        args.title,
        "--format",
        "json",
    ]
    if body:
        gh_args.extend(["--body", body])
    proc = run_gh(gh_args)
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-create failed", file=sys.stderr)
        return proc.returncode or 1
    print(proc.stdout.strip())
    return 0


def cmd_set_status(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project set-status: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project set-status: FAIL — {e}", file=sys.stderr)
        return 2
    try:
        option_id = resolve_status_option_id(ssot, args.to)
        field_id = status_field_id(ssot)
    except KeyError as exc:
        print(f"project set-status: FAIL — {exc}", file=sys.stderr)
        return 1
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            args.id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-edit failed", file=sys.stderr)
        return proc.returncode or 1
    print(f"set-status: {args.id} → {args.to} ({option_id})")
    return 0


def cmd_set_field(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    ssot, errs = load_project_ssot(root)
    if errs or ssot is None:
        for e in errs:
            print(f"project set-field: FAIL — {e}", file=sys.stderr)
        return 1
    enabled_errs = require_enabled(ssot)
    if enabled_errs:
        for e in enabled_errs:
            print(f"project set-field: FAIL — {e}", file=sys.stderr)
        return 2
    field = args.field.strip().lower()
    if field not in ("priority", "size"):
        print("project set-field: FAIL — --field must be priority or size", file=sys.stderr)
        return 1
    try:
        field_id, option_id = resolve_field_option_id(ssot, field, args.to)
    except KeyError as exc:
        print(f"project set-field: FAIL — {exc}", file=sys.stderr)
        return 1
    project_id = str(ssot["project_id"])
    proc = run_gh(
        [
            "project",
            "item-edit",
            "--project-id",
            project_id,
            "--id",
            args.id,
            "--field-id",
            field_id,
            "--single-select-option-id",
            option_id,
        ]
    )
    if proc.returncode != 0:
        print(proc.stderr or proc.stdout or "gh project item-edit failed", file=sys.stderr)
        return proc.returncode or 1
    print(f"set-field: {args.id} {field} → {args.to} ({option_id})")
    return 0


def register_project_subparser(sub: argparse._SubParsersAction) -> None:
    project = sub.add_parser(
        "project",
        help="GitHub Project SSOT (project_ssot in github.collaboration.yaml)",
    )
    project_sub = project.add_subparsers(dest="project_command", required=True)

    status_cmd = project_sub.add_parser("status", help="Show project_ssot config from user_settings")
    status_cmd.add_argument("--directory", type=Path, default=".")
    status_cmd.add_argument("--json", action="store_true")
    status_cmd.set_defaults(func=cmd_status)

    list_cmd = project_sub.add_parser("list", help="List project items (optional status filter)")
    list_cmd.add_argument("--directory", type=Path, default=".")
    list_cmd.add_argument(
        "--status",
        default="",
        help="Filter: backlog|ready|in_progress|in_review|done",
    )
    list_cmd.add_argument("--limit", type=int, default=100)
    list_cmd.add_argument("--json", action="store_true")
    list_cmd.set_defaults(func=cmd_list)

    create_cmd = project_sub.add_parser("create", help="Create a DraftIssue on the project")
    create_cmd.add_argument("--directory", type=Path, default=".")
    create_cmd.add_argument("--title", required=True)
    create_cmd.add_argument("--body", default="")
    create_cmd.set_defaults(func=cmd_create)

    set_status = project_sub.add_parser("set-status", help="Set item Status from YAML option ids")
    set_status.add_argument("--directory", type=Path, default=".")
    set_status.add_argument("--id", required=True, help="Project item id (PVTI_…)")
    set_status.add_argument(
        "--to",
        required=True,
        help="Logical status: backlog|ready|in_progress|in_review|done",
    )
    set_status.set_defaults(func=cmd_set_status)

    set_field = project_sub.add_parser("set-field", help="Set Priority or Size from YAML option ids")
    set_field.add_argument("--directory", type=Path, default=".")
    set_field.add_argument("--id", required=True)
    set_field.add_argument("--field", required=True, choices=("priority", "size"))
    set_field.add_argument("--to", required=True, help="e.g. p1 or s")
    set_field.set_defaults(func=cmd_set_field)
