"""
File: plan_cli.py
Path: .ai_infra/install/agent_colony/plan_cli.py
Role: Pattern A plan snapshot CLI (ADR-010).
Used By:
 - .ai_infra/install/agent_colony/cli.py
Depends On:
 - plan_manage
Notes:
 - History snapshots only; live SSOT remains board/plan.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import plan_manage


def cmd_plan_snapshot(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        dst, meta = plan_manage.snapshot_plan(
            root,
            slug=args.slug,
            from_spec=args.from_spec,
            agent=args.agent,
            board_item=args.board_item,
            parent_chat=args.parent_chat,
        )
    except FileNotFoundError as exc:
        print(f"plan snapshot: FAIL — {exc}", file=sys.stderr)
        return plan_manage.EXIT_NOT_FOUND
    except ValueError as exc:
        print(f"plan snapshot: FAIL — {exc}", file=sys.stderr)
        return plan_manage.EXIT_VALIDATION
    print(f"plan snapshot: {dst}")
    if meta:
        print(f"meta: {meta}")
    return plan_manage.EXIT_OK


def cmd_plan_list(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    rows = plan_manage.list_snapshots(root)
    if not rows:
        print("plan list: (none)")
        return plan_manage.EXIT_OK
    print("snapshot\tslug\tagent\tboard_item\tsource")
    seen_slugs: set[str] = set()
    for row in rows:
        slug = row.get("slug") or "—"
        if slug != "—":
            seen_slugs.add(slug)
        print(
            f"{row['file']}\t{slug}\t"
            f"{row.get('agent') or '—'}\t{row.get('board_item') or '—'}\t"
            f"{row.get('source') or '—'}"
        )
        if args.verbose and slug != "—":
            local_path = root / ".local" / "plans" / row["file"]
            print(f"# local: {local_path}")
            print(f"# build_bridge: plan open --slug {slug}")
    if seen_slugs and not args.verbose:
        for slug in sorted(seen_slugs):
            print(f"build_bridge: plan open --slug {slug}")
    return plan_manage.EXIT_OK


def cmd_plan_open(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        dest = plan_manage.open_plan(root, slug=args.slug, force=args.force)
    except FileNotFoundError as exc:
        print(f"plan open: FAIL — {exc}", file=sys.stderr)
        return plan_manage.EXIT_NOT_FOUND
    except ValueError as exc:
        print(f"plan open: FAIL — {exc}", file=sys.stderr)
        return plan_manage.EXIT_VALIDATION
    print(f"plan open: {dest}")
    print("hint: Open in Plans UI for Build; agents build from .local/plans")
    return plan_manage.EXIT_OK


def register_plan_subcommands(sub: Any) -> None:
    """Attach plan subcommands to the root parser group."""
    snapshot = sub.add_parser("snapshot", help="Save dated plan snapshot under .local/plans/")
    snapshot.add_argument("--directory", type=Path, default=".")
    snapshot.add_argument("--slug", required=True, help="Kebab-case slug for this plan")
    snapshot.add_argument(
        "--from",
        dest="from_spec",
        default="plan.md",
        help="Source: plan.md, path, or cursor-plan:<basename>",
    )
    snapshot.add_argument("--agent", default=None)
    snapshot.add_argument("--board-item", default=None)
    snapshot.add_argument("--parent-chat", default=None)
    snapshot.set_defaults(func=cmd_plan_snapshot)

    list_p = sub.add_parser("list", help="List plan snapshots")
    list_p.add_argument("--directory", type=Path, default=".")
    list_p.add_argument(
        "--verbose",
        action="store_true",
        help="Print local path and build_bridge hint per row",
    )
    list_p.set_defaults(func=cmd_plan_list)

    open_p = sub.add_parser(
        "open",
        help="Copy latest local snapshot to ~/.cursor/plans/ for IDE Build",
    )
    open_p.add_argument("--directory", type=Path, default=".")
    open_p.add_argument("--slug", required=True, help="Kebab-case slug for this plan")
    open_p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing Cursor plan twin",
    )
    open_p.set_defaults(func=cmd_plan_open)
