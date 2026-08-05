"""
File: canvas_cli.py
Path: .ai_infra/install/cursor_workflow/canvas_cli.py
Role: Pattern A canvas CLI — doctor, list, sync, save (ADR-010).
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - canvas_manage, cursor_host_paths
Notes:
 - Exit codes align with project CLI.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import canvas_manage


def _artifact_dir(root: Path) -> Path:
    path = root / ".local" / "workflow-artifacts" / "canvas"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_artifact(root: Path, prefix: str, body: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _artifact_dir(root) / f"{prefix}-{stamp}.md"
    path.write_text(body, encoding="utf-8")
    return path


def cmd_canvas_doctor(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    report = canvas_manage.build_doctor_report(root)
    body = canvas_manage.format_doctor_markdown(report)
    print(body)
    art = _write_artifact(root, "doctor", body)
    print(f"artifact: {art}")
    return canvas_manage.EXIT_OK


def cmd_canvas_list(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    tier = args.tier
    by_tier = canvas_manage.list_by_tier(root, tier)  # type: ignore[arg-type]
    for name, files in by_tier.items():
        print(f"[{name}]")
        for filename in files:
            print(f"  {filename}")
        if not files:
            print("  (none)")
    return canvas_manage.EXIT_OK


def cmd_canvas_sync(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        copied = canvas_manage.sync_canvas(
            root,
            name=args.name,
            missing=bool(args.missing),
            sync_all=bool(args.all),
            force=bool(args.force),
            source=args.from_tier,  # type: ignore[arg-type]
        )
    except FileNotFoundError as exc:
        print(f"canvas sync: FAIL — {exc}", file=sys.stderr)
        return canvas_manage.EXIT_NOT_FOUND
    except ValueError as exc:
        print(f"canvas sync: FAIL — {exc}", file=sys.stderr)
        return canvas_manage.EXIT_USAGE
    if not copied:
        print("canvas sync: nothing to copy")
    else:
        print(f"canvas sync: copied {len(copied)} file(s)")
        for name in copied:
            print(f" - {name}")
    return canvas_manage.EXIT_OK


def cmd_canvas_save(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        dst = canvas_manage.save_canvas(
            root,
            slug=args.slug,
            source=args.from_tier,  # type: ignore[arg-type]
            agent=args.agent,
        )
    except FileNotFoundError as exc:
        print(f"canvas save: FAIL — {exc}", file=sys.stderr)
        return canvas_manage.EXIT_NOT_FOUND
    except ValueError as exc:
        print(f"canvas save: FAIL — {exc}", file=sys.stderr)
        return canvas_manage.EXIT_VALIDATION
    text = dst.read_text(encoding="utf-8")
    for warning in canvas_manage.validate_canvas_source(text):
        print(f"canvas save: WARN — {warning}", file=sys.stderr)
    print(f"canvas save: {dst}")
    return canvas_manage.EXIT_OK


def register_canvas_subcommands(sub: Any) -> None:
    """Attach canvas subcommands to the root parser group."""
    doctor = sub.add_parser("doctor", help="Report repo vs managed vs local canvas drift")
    doctor.add_argument("--directory", type=Path, default=".")
    doctor.set_defaults(func=cmd_canvas_doctor)

    list_p = sub.add_parser("list", help="List canvases by tier")
    list_p.add_argument("--directory", type=Path, default=".")
    list_p.add_argument(
        "--tier",
        choices=("repo", "managed", "local", "all"),
        default="all",
    )
    list_p.set_defaults(func=cmd_canvas_list)

    sync = sub.add_parser("sync", help="Copy canvases to Cursor managed render path")
    sync.add_argument("--directory", type=Path, default=".")
    sync.add_argument("--name", default=None, help="Canvas base name (no .canvas.tsx)")
    sync.add_argument("--missing", action="store_true", help="Copy only absent managed files")
    sync.add_argument("--all", action="store_true", help="Copy all from source (requires --force)")
    sync.add_argument("--force", action="store_true", help="Allow --all overwrite")
    sync.add_argument(
        "--from",
        dest="from_tier",
        choices=("repo", "local"),
        default="repo",
    )
    sync.set_defaults(func=cmd_canvas_sync)

    save = sub.add_parser("save", help="Save canvas to .local/canvases/")
    save.add_argument("--directory", type=Path, default=".")
    save.add_argument("--slug", required=True, help="Canvas base name (kebab-case)")
    save.add_argument("--agent", default=None)
    save.add_argument(
        "--from",
        dest="from_tier",
        choices=("managed", "repo", "local"),
        default="managed",
    )
    save.set_defaults(func=cmd_canvas_save)
