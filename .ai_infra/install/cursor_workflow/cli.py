"""
File: cli.py
Path: .ai_infra/install/cursor_workflow/cli.py
Role: Branded cursor-workflow CLI — install, gates, health, and MCP helpers.
Used By:
 - cursor_workflow/__main__.py (root shim)
Depends On:
 - .ai_infra/bootstrap.py
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/install/cursor_workflow/mcp_manage.py
Notes:
 - install forwards to scaffold.py; gates runs prepare-aligned checks.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

for _candidate in (Path(__file__).resolve(), *Path(__file__).resolve().parents):
    # Walk up to kit root whether invoked via editable install or payload copy.
    bootstrap = _candidate / ".ai_infra" / "bootstrap.py"
    if bootstrap.is_file():
        if str(_candidate / ".ai_infra") not in sys.path:
            sys.path.insert(0, str(_candidate / ".ai_infra"))
        from bootstrap import ensure_paths_import

        KIT_ROOT = ensure_paths_import(__file__)
        break
else:
    raise RuntimeError("kit root not found above cursor_workflow")

import paths
from paths import ai_infra_dir, kit_root, scripts_dir

_MCP_PKG = Path(__file__).resolve().parent
if str(_MCP_PKG) not in sys.path:
    sys.path.insert(0, str(_MCP_PKG))
import mcp_manage  # noqa: E402
import contributors_cli  # noqa: E402
import integrate_cli  # noqa: E402
import drift_cli  # noqa: E402
import doc_cli  # noqa: E402
import verify_cli  # noqa: E402
import activate_cli  # noqa: E402
import project_cli  # noqa: E402


def _scaffold_script() -> Path:
    return scripts_dir("install") / "scaffold.py"


def _run(cmd: list[str], cwd: Path, *, timeout_s: float = 300.0) -> int:
    try:
        proc = subprocess.run(cmd, cwd=cwd, timeout=timeout_s)
    except subprocess.TimeoutExpired:
        print(f"timeout after {timeout_s}s: {' '.join(cmd)}", file=sys.stderr)
        return 124
    return int(proc.returncode)


def _resolve_install_source(raw: Path | None) -> Path:
    if raw is None:
        return kit_root()
    if raw.is_absolute():
        return raw.resolve()
    root = kit_root()
    for base in (root.parent, root, Path.cwd()):
        candidate = (base / raw).resolve()
        if candidate.is_dir():
            return candidate
    return raw.resolve()


def cmd_install(args: argparse.Namespace) -> int:
    script = _scaffold_script()
    cmd = [
        sys.executable,
        str(script),
        "--target",
        str(args.target),
        "--source",
        str(args.source),
        "--profile",
        args.profile,
    ]
    if args.dry_run:
        cmd.append("--dry-run")
    if args.with_readme:
        cmd.append("--with-readme")
    if args.with_tests:
        cmd.append("--with-tests")
    if args.with_venv:
        cmd.append("--with-venv")
    if args.with_mcp_json:
        cmd.append("--with-mcp-json")
    if args.verify:
        cmd.append("--verify")
    return _run(cmd, kit_root())


def cmd_gates(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    py = paths.resolve_project_python(root)
    pr = root / ".ai_infra" / "scripts" / "pr"
    arch = root / ".ai_infra" / "scripts" / "architecture"
    if not pr.is_dir():
        pr = scripts_dir("pr", root)
        arch = scripts_dir("architecture", root)
    steps = [
        [py, str(pr / "check_testing_artifacts.py")],
        [py, "-m", "pytest", "-q"],
        [py, str(arch / "check_governance_consistency.py")],
        [py, str(arch / "check_debrand.py")],
        [py, str(arch / "check_doc_facts.py")],
    ]
    for cmd in steps:
        code = _run(cmd, root)
        if code != 0:
            return code
    return 0


def cmd_health(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    issues: list[str] = []
    required = [
        root / ".ai_infra" / "scripts" / "pr" / "prepare.py",
        root / ".ai_infra" / ".kit-version",
        root / ".cursor" / "agents" / "implementer.md",
        root / ".local" / "index-and-planning" / "current" / "session-pointer.md",
    ]
    for path in required:
        if not path.is_file():
            issues.append(f"missing {path.relative_to(root)}")

    kit_version = root / ".ai_infra" / ".kit-version"
    if kit_version.is_file():
        print(f"kit_version: {kit_version.read_text(encoding='utf-8').strip()}")

    if (root / ".cursor" / "mcp.json.kit.example").is_file() and (
        root / ".cursor" / "mcp.registry.yaml"
    ).is_file():
        try:
            mcp_manage.write_merged_mcp(root)
            registry_errors = mcp_manage.validate_registry(root)
            issues.extend(registry_errors)
        except (FileNotFoundError, ValueError) as exc:
            issues.append(str(exc))

    try:
        us = contributors_cli._import_user_settings(root)
        settings_errors = us.validate_github_collaboration(root)
        for err in settings_errors:
            issues.append(f"user_settings: {err}")
        try:
            validate = integrate_cli._import_validate(root)
            p0_failures = [
                r for r in validate.run_checks(root)
                if not r.passed and r.severity.value == "P0"
            ]
            for result in p0_failures:
                issues.append(f"integrate {result.check_id}: {result.detail}")
        except FileNotFoundError:
            issues.append("integrate validate: missing .ai_infra/scripts/integration")
        try:
            check_drift = drift_cli._import_check_drift(root)
            p0_drift = [
                r for r in check_drift.run_checks(root)
                if not r.passed and r.severity.value == "P0"
            ]
            for result in p0_drift:
                issues.append(f"drift {result.check_id}: {result.detail}")
        except FileNotFoundError:
            issues.append("drift validate: missing .ai_infra/scripts/workflow")
    except FileNotFoundError:
        issues.append("user_settings: missing .ai_infra/scripts/pr (kit incomplete)")

    if issues:
        print("health: FAIL")
        for issue in issues:
            print(f" - {issue}")
        return 1

    print("health: PASS")
    return 0


def cmd_mcp_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        mcp_manage.write_merged_mcp(root)
        errors = mcp_manage.validate_registry(root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp validate: FAIL — {exc}", file=sys.stderr)
        return 1
    if errors:
        print("mcp validate: FAIL")
        for err in errors:
            print(f" - {err}")
        return 1
    print("mcp validate: PASS")
    return 0


def cmd_mcp_link(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        mcp_manage.link_user_server(root, args.name, args.file.resolve())
        mcp_manage.ensure_mcp_gitignore(root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp link: FAIL — {exc}", file=sys.stderr)
        return 1
    print(f"mcp link: linked '{args.name}' from {args.file}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cursor-workflow",
        description="Cursor Agent Infrastructure Plugin — install and gate helpers.",
    )
    parser.add_argument("--version", action="version", version="cursor-workflow 0.4.0")
    sub = parser.add_subparsers(dest="command", required=True)

    install = sub.add_parser("install", help="Install infrastructure into a target project")
    install.add_argument("--target", required=True, type=Path, help="Destination directory")
    install.add_argument(
        "--source",
        type=Path,
        default=None,
        help="Kit root (default: this repository)",
    )
    install.add_argument(
        "--profile",
        default="default",
        choices=("default", "with_mcp"),
        help="Install profile from .ai_infra/manifest.yaml",
    )
    install.add_argument("--dry-run", action="store_true")
    install.add_argument("--with-readme", action="store_true")
    install.add_argument("--with-tests", action="store_true")
    install.add_argument("--with-venv", action="store_true")
    install.add_argument("--with-mcp-json", action="store_true")
    install.add_argument("--verify", action="store_true")
    install.set_defaults(func=cmd_install)

    gates = sub.add_parser("gates", help="Run prepare-aligned gate checks")
    gates.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Project root (default: current directory)",
    )
    gates.set_defaults(func=cmd_gates)

    health = sub.add_parser("health", help="Diagnostic check for installed kit layout")
    health.add_argument(
        "--directory",
        type=Path,
        default=".",
        help="Project root (default: current directory)",
    )
    health.set_defaults(func=cmd_health)

    mcp = sub.add_parser("mcp", help="MCP config merge and registry validation")
    mcp_sub = mcp.add_subparsers(dest="mcp_command", required=True)

    mcp_validate = mcp_sub.add_parser("validate", help="Merge kit+user MCP and validate registry")
    mcp_validate.add_argument("--directory", type=Path, default=".")
    mcp_validate.set_defaults(func=cmd_mcp_validate)

    mcp_link = mcp_sub.add_parser("link", help="Link external MCP server fragment into mcp.user.json")
    mcp_link.add_argument("--name", required=True, help="Server name in mcp.user.json")
    mcp_link.add_argument("--file", required=True, type=Path, help="JSON fragment with mcpServers")
    mcp_link.add_argument("--directory", type=Path, default=".")
    mcp_link.set_defaults(func=cmd_mcp_link)

    contributors_cli.register_contributors_subparser(sub)
    integrate_cli.register_integrate_subparser(sub)
    drift_cli.register_drift_subparser(sub)
    doc_cli.register_doc_subparser(sub)
    verify_cli.register_verify_subparser(sub)
    activate_cli.register_activate_subparser(sub)
    project_cli.register_project_subparser(sub)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "install":
        args.source = _resolve_install_source(args.source)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
