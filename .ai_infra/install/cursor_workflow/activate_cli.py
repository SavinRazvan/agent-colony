"""
File: activate_cli.py
Path: .ai_infra/install/cursor_workflow/activate_cli.py
Role: CLI handlers for activate — idempotent three-plane install for plugin consumers.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - .ai_infra/scripts/install/plane_status.py
 - .ai_infra/scripts/install/scaffold.py (via install subcommand)
Notes:
 - Agents invoke one command after plugin enable; user personalizes .local/user_settings/ next.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _import_plane_status() -> object:
    install_dir = Path(__file__).resolve().parents[2] / "scripts" / "install"
    install_str = str(install_dir)
    if install_str not in sys.path:
        sys.path.insert(0, install_str)
    import plane_status

    return plane_status


def resolve_activate_source(raw: Path | None, target: Path, default_kit_root: Path) -> Path:
    if raw is not None:
        resolved = raw.resolve()
        if (resolved / ".ai_infra" / "manifest.yaml").is_file():
            return resolved
        if (resolved / "payload" / ".ai_infra" / "manifest.yaml").is_file():
            return (resolved / "payload").resolve()
        raise FileNotFoundError(f"invalid activate source (no manifest): {resolved}")

    env_payload = os.environ.get("WORKFLOW_KIT_PAYLOAD", "").strip()
    if env_payload:
        candidate = Path(env_payload).resolve()
        if (candidate / ".ai_infra" / "manifest.yaml").is_file():
            return candidate

    for candidate in (
        target / "payload",
        default_kit_root / "payload",
    ):
        if (candidate / ".ai_infra" / "manifest.yaml").is_file():
            return candidate.resolve()

    if (default_kit_root / ".ai_infra" / "manifest.yaml").is_file():
        if target.resolve() != default_kit_root.resolve():
            return default_kit_root.resolve()

    raise FileNotFoundError(
        "activate source not found. Set WORKFLOW_KIT_PAYLOAD to the plugin payload/ directory, "
        "or pass --source <kit-root|payload/>."
    )


def _run_settings_validate(root: Path) -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "cursor_workflow",
        "contributors",
        "validate",
        "--directory",
        str(root),
    ]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _print_post_activate_hints(root: Path) -> None:
    settings = root / ".local" / "user_settings"
    yaml_path = settings / "github.collaboration.yaml"
    print("\nYou're almost done — 3 quick steps:")
    print(f"  1. Edit {yaml_path}")
    print('     Set owner.display_name and owner.github_user (replace placeholders).')
    print("  2. Run: python3 -m cursor_workflow contributors validate")
    print("  3. In Cursor chat: @ implementer — read .local/index-and-planning/current/session-pointer.md")
    print("\nOptional:")
    print("  python3 -m cursor_workflow integrate validate")
    print("  python3 -m cursor_workflow health")
    print("Add agents/skills later: @ integrator-mas-agent (chat agent, not a shell command).")


def cmd_activate(args: argparse.Namespace) -> int:
    from paths import kit_root

    target = Path(args.directory).resolve()
    plane_status = _import_plane_status()
    status = plane_status.assess_planes(target, profile=args.profile)

    if status.all_ready and not args.force:
        print(plane_status.format_plane_report(status))
        print("\nAll three planes ready — skipping install.")
        code, out = _run_settings_validate(target)
        if out:
            print(out)
        if code != 0:
            print("\nSettings not yet valid — edit .local/user_settings/ then re-run activate.")
            _print_post_activate_hints(target)
            return 0 if args.allow_settings_pending else 1
        _print_post_activate_hints(target)
        return 0

    if not status.all_ready:
        print("Pre-activate: planes not installed yet — proceeding with scaffold.")
    else:
        print(plane_status.format_plane_report(status))

    try:
        source = resolve_activate_source(args.source, target, kit_root())
    except FileNotFoundError as exc:
        print(f"activate: FAIL — {exc}", file=sys.stderr)
        return 1

    if source.resolve() == target.resolve():
        print(
            "activate: FAIL — cannot install a workspace into itself; use kit root as --source for another target",
            file=sys.stderr,
        )
        return 1

    print(f"\nInstalling three planes from {source} → {target}")
    from paths import kit_root, scripts_dir

    script = scripts_dir("install", kit_root()) / "scaffold.py"
    cmd = [
        sys.executable,
        str(script),
        "--target",
        str(target),
        "--source",
        str(source),
        "--profile",
        args.profile,
    ]
    if args.with_venv:
        cmd.append("--with-venv")
    if args.with_mcp_json:
        cmd.append("--with-mcp-json")
    if args.verify:
        cmd.append("--verify")
    proc = subprocess.run(cmd, cwd=kit_root())
    code = int(proc.returncode)
    if code != 0:
        return code

    status = plane_status.assess_planes(target, profile=args.profile)
    print("\nPost-install plane status:")
    print(plane_status.format_plane_report(status))
    if not status.all_ready:
        print("activate: FAIL — planes still incomplete after install", file=sys.stderr)
        return 1

    code, out = _run_settings_validate(target)
    if out:
        print(out)
    _print_post_activate_hints(target)
    return 0 if code == 0 or args.allow_settings_pending else 1


def register_activate_subparser(sub: argparse._SubParsersAction) -> None:
    activate = sub.add_parser(
        "activate",
        help="Idempotent three-plane install (plugin / first-run automation)",
    )
    activate.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Target workspace (default: current directory)",
    )
    activate.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Kit root or payload/ (default: auto — WORKFLOW_KIT_PAYLOAD, ./payload, kit root)",
    )
    activate.add_argument(
        "--profile",
        default="with_mcp",
        choices=("default", "with_mcp"),
        help="Install profile (default: with_mcp for plugin flow)",
    )
    activate.add_argument("--with-venv", action="store_true", default=True)
    activate.add_argument("--no-venv", action="store_false", dest="with_venv")
    activate.add_argument("--with-mcp-json", action="store_true", default=True)
    activate.add_argument("--no-mcp-json", action="store_false", dest="with_mcp_json")
    activate.add_argument("--verify", action="store_true", default=True)
    activate.add_argument("--no-verify", action="store_false", dest="verify")
    activate.add_argument(
        "--force",
        action="store_true",
        help="Re-run install even when all planes report ready",
    )
    activate.add_argument(
        "--allow-settings-pending",
        action="store_true",
        default=True,
        help="Exit 0 when planes ready but user_settings still have placeholders (default)",
    )
    activate.set_defaults(func=cmd_activate)
