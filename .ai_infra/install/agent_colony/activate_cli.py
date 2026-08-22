"""
File: activate_cli.py
Path: .ai_infra/install/agent_colony/activate_cli.py
Role: CLI handlers for activate — idempotent three-plane install for plugin consumers.
Used By:
 - .ai_infra/install/agent_colony/cli.py
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

import yaml


def _import_plane_status() -> object:
    install_dir = Path(__file__).resolve().parents[2] / "scripts" / "install"
    install_str = str(install_dir)
    if install_str not in sys.path:
        sys.path.insert(0, install_str)
    import plane_status

    return plane_status


def _manifest_root(path: Path) -> bool:
    return (path / ".ai_infra" / "manifest.yaml").is_file()


def _payload_complete(payload: Path) -> bool:
    """Reject bare marketplace git checkouts missing installable payload trees."""
    return (
        (payload / ".cursor" / "agents" / "implementer.md").is_file()
        and (payload / "agent_colony" / "__main__.py").is_file()
    )


def _read_payload_kit_version(payload: Path) -> tuple[int, ...]:
    manifest = payload / ".ai_infra" / "manifest.yaml"
    if not manifest.is_file():
        return (0, 0, 0)
    try:
        raw = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return (0, 0, 0)
    if not isinstance(raw, dict):
        return (0, 0, 0)
    version = str(raw.get("kit_version", "")).strip()
    parts: list[int] = []
    for piece in version.split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            break
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _payload_origin_rank(payload: Path) -> int:
    text = payload.as_posix()
    if "/cache/" in text:
        return 0
    if "/marketplaces/" in text:
        return 1
    if "/local/" in text:
        return 2
    return 3


def discover_cursor_plugin_payload(*, home: Path | None = None) -> Path | None:
    """Best Agent Colony ``payload/`` under Cursor plugin cache or marketplaces.

    After ``/add-plugin``, Cursor stores a checkout under
    ``~/.cursor/plugins/cache/agent-colony/agent-colony/<sha>/`` with a full
    ``payload/`` tree (``with_mcp`` profile). Agents on a brand-new app can
    activate from that path without a local kit clone.

    Picks highest ``kit_version`` from manifest; tie-break cache > marketplaces >
    local; then newest mtime. Skips incomplete checkouts (no agents/CLI).
    """
    home_path = home if home is not None else Path.home()
    plugins = home_path / ".cursor" / "plugins"
    if not plugins.is_dir():
        return None

    candidates: list[Path] = []
    patterns = (
        "cache/agent-colony/agent-colony/*/payload",
        "cache/agent-colony/*/payload",
        "marketplaces/**/agent-colony/*/payload",
        "marketplaces/**/agent-colony/payload",
        "local/**/agent-colony/*/payload",
        "local/**/agent-colony/payload",
    )
    for pattern in patterns:
        for match in plugins.glob(pattern):
            if match.is_dir() and _manifest_root(match) and _payload_complete(match):
                candidates.append(match.resolve())

    if not candidates:
        return None

    def sort_key(path: Path) -> tuple[tuple[int, ...], int, float]:
        return (
            _read_payload_kit_version(path),
            -_payload_origin_rank(path),
            path.stat().st_mtime,
        )

    return max(set(candidates), key=sort_key)


def resolve_activate_source(raw: Path | None, target: Path, default_kit_root: Path) -> Path:
    if raw is not None:
        resolved = raw.resolve()
        if _manifest_root(resolved):
            return resolved
        if _manifest_root(resolved / "payload"):
            return (resolved / "payload").resolve()
        raise FileNotFoundError(f"invalid activate source (no manifest): {resolved}")

    env_payload = os.environ.get("WORKFLOW_KIT_PAYLOAD", "").strip()
    if env_payload:
        candidate = Path(env_payload).resolve()
        if _manifest_root(candidate):
            return candidate
        if _manifest_root(candidate / "payload"):
            return (candidate / "payload").resolve()

    for candidate in (
        target / "payload",
        default_kit_root / "payload",
    ):
        if _manifest_root(candidate):
            return candidate.resolve()

    if _manifest_root(default_kit_root):
        if target.resolve() != default_kit_root.resolve():
            return default_kit_root.resolve()

    plugin_payload = discover_cursor_plugin_payload()
    if plugin_payload is not None:
        return plugin_payload

    raise FileNotFoundError(
        "activate source not found. Set WORKFLOW_KIT_PAYLOAD to the plugin payload/ directory, "
        "pass --source <kit-root|payload/>, or install the Agent Colony plugin "
        "(/add-plugin) so ~/.cursor/plugins/cache/agent-colony/*/payload is available."
    )


def _run_settings_validate(root: Path) -> tuple[int, str]:
    cmd = [
        sys.executable,
        "-m",
        "agent_colony",
        "contributors",
        "validate",
        "--directory",
        str(root),
    ]
    proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
    output = ((proc.stdout or "") + (proc.stderr or "")).strip()
    return proc.returncode, output


def _is_placeholder_owner_cfg(raw: object) -> bool:
    if not isinstance(raw, dict):
        return True
    pr_dir = Path(__file__).resolve().parents[2] / "scripts" / "pr"
    pr_str = str(pr_dir)
    if pr_str not in sys.path:
        sys.path.insert(0, pr_str)
    from user_settings_load import is_placeholder_owner

    return bool(is_placeholder_owner(raw))


def _print_post_activate_hints(root: Path) -> None:
    settings = root / ".local" / "user_settings"
    yaml_path = settings / "github.collaboration.yaml"
    collab_enabled = False
    raw: object = None
    try:
        raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        raw = None
    if isinstance(raw, dict):
        project_ssot = raw.get("project_ssot")
        collab_enabled = isinstance(project_ssot, dict) and bool(project_ssot.get("enabled"))

    needs_owner_edit = _is_placeholder_owner_cfg(raw)

    if collab_enabled:
        print("\nYou're almost done — board-first setup:")
        step = 1
        if needs_owner_edit:
            print(f"  {step}. Edit {yaml_path}")
            print("     Set owner.display_name and owner.github_user (replace placeholders).")
            step += 1
            print(
                f"  {step}. Run: source .venv/bin/activate && "
                "python3 -m agent_colony contributors validate"
            )
            step += 1
        else:
            print(f"  {step}. Owner configured (contributors validate: PASS).")
            step += 1
        print(f"  {step}. Run: gh auth status — refresh Project scopes only if missing")
        print("     (gh auth refresh -h github.com -s read:project,project)")
        step += 1
        print(
            f"  {step}. Agent chat: paste Project URL + this repo URL → /board wires project_ssot ids"
        )
        step += 1
        print(f"  {step}. Run: source .venv/bin/activate && python3 -m agent_colony project doctor")
        step += 1
        print(f"  {step}. Board shell overlay seeded on activate (minimal 2-view); if missing:")
        print(
            "     source .venv/bin/activate && "
            "python3 -m agent_colony project board-shell init --minimal"
        )
        step += 1
        print(f"  {step}. Agent chat: /board — CONSENT GATE then TURN PROTOCOL coach")
        step += 1
        print(
            f"  {step}. Run: source .venv/bin/activate && "
            "python3 -m agent_colony project board-bootstrap --check"
        )
        print(
            "     Until shell green (2-view overlay or six-view default; "
            "Tier-1 columns on both primary views)."
        )
        step += 1
        print(f"  {step}. Run: source .venv/bin/activate && python3 -m agent_colony project status")
        step += 1
        print(
            f"  {step}. In Agent chat: /implementer — local trackers are offline fallback under board_only."
        )
        step += 1
        print(f"  {step}. Canvas preview: python3 -m agent_colony canvas doctor")
        print("     (sync repo canvases: canvas sync --missing)")
        step += 1
        print(f"  {step}. MCP smoke: python3 -m agent_colony mcp smoke --server deepwiki")
        print("     (/mcp-connect for enable DeepWiki | link custom | doctor)")
    else:
        print("\nYou're almost done — 3 quick steps:")
        if needs_owner_edit:
            print(f"  1. Edit {yaml_path}")
            print("     Set owner.display_name and owner.github_user (replace placeholders).")
            print(
                "  2. Run: source .venv/bin/activate && "
                "python3 -m agent_colony contributors validate"
            )
            print(
                "  3. In Agent chat: /implementer — "
                "read .local/index-and-planning/current/session-pointer.md"
            )
        else:
            print("  1. Owner configured (contributors validate: PASS).")
            print(
                "  2. In Agent chat: /implementer — "
                "read .local/index-and-planning/current/session-pointer.md"
            )
            print("  3. Optional: enable project_ssot + /board when ready for board SSOT.")
        print("\nOptional:")
        print("  source .venv/bin/activate && python3 -m agent_colony integrate validate")
        print("  source .venv/bin/activate && python3 -m agent_colony health")
        print("  source .venv/bin/activate && python3 -m agent_colony canvas doctor")
        print("Add agents/skills later: /integrator (subagent, not a shell command).")

    print("\nMCP (DeepWiki seeded on consumer activate when missing):")
    print("  source .venv/bin/activate && python3 -m agent_colony mcp smoke --server deepwiki")
    print("  Agent chat: /mcp-connect — enable DeepWiki | link custom | doctor/smoke")


def _import_scaffold_refresh() -> object:
    install_dir = Path(__file__).resolve().parents[2] / "scripts" / "install"
    install_str = str(install_dir)
    if install_str not in sys.path:
        sys.path.insert(0, install_str)
    import scaffold

    return scaffold


def _heal_consumer_runtime(target: Path, *, with_venv: bool) -> None:
    """Idempotent heal: gitignore + STARTER marker + missing .venv when requested."""
    from paths import kit_root

    scaffold = _import_scaffold_refresh()
    log: list[str] = []
    mcp_manage = scaffold._load_mcp_manage(target)
    if mcp_manage is None:
        mcp_manage = scaffold._load_mcp_manage(kit_root())
    if mcp_manage is not None:
        mcp_manage.ensure_consumer_gitignore(target)
        print(f"ENSURE consumer .gitignore under {target}")
    scaffold._seed_consumer_drift_marker(target, False, log)
    for line in log:
        print(line)
    if with_venv and not (target / ".venv" / "bin" / "python").is_file():
        before = len(log)
        scaffold._create_venv(target, False, log)
        for line in log[before:]:
            print(line)


def _resolve_dashboard_refresh_source(
    raw: Path | None, target: Path, default_kit_root: Path
) -> Path | None:
    try:
        return resolve_activate_source(raw, target, default_kit_root)
    except FileNotFoundError:
        embedded = target / ".ai_infra" / "templates" / "local-workspace" / "index.html"
        if embedded.is_file():
            return target
        return None


def _refresh_dashboard_templates(target: Path, source: Path | None, default_kit_root: Path) -> None:
    refresh_source = source or _resolve_dashboard_refresh_source(None, target, default_kit_root)
    if refresh_source is None:
        return
    scaffold = _import_scaffold_refresh()
    scaffold.refresh_dashboards(refresh_source, target)


def cmd_activate(args: argparse.Namespace) -> int:
    from paths import kit_root

    target = Path(args.directory).resolve()
    plane_status = _import_plane_status()
    # Path planes only — missing .venv is healed below when --with-venv (default).
    status = plane_status.assess_planes(target, profile=args.profile, require_venv=False)

    if status.all_ready and not args.force:
        print(plane_status.format_plane_report(status))
        try:
            ext_source = resolve_activate_source(args.source, target, kit_root())
            _refresh_dashboard_templates(target, ext_source, kit_root())
        except FileNotFoundError:
            _refresh_dashboard_templates(target, None, kit_root())
        _heal_consumer_runtime(target, with_venv=bool(args.with_venv))
        status = plane_status.assess_planes(
            target, profile=args.profile, require_venv=bool(args.with_venv)
        )
        print(plane_status.format_plane_report(status))
        if not status.all_ready:
            print("activate: FAIL — runtime still incomplete after heal", file=sys.stderr)
            return 1
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
            "activate: FAIL — cannot install a workspace into itself; "
            "use kit root as --source for another target",
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
    if getattr(args, "keep_smoke_test", False):
        cmd.append("--keep-smoke-test")
    proc = subprocess.run(cmd, cwd=kit_root())
    code = int(proc.returncode)
    if code != 0:
        return code

    status = plane_status.assess_planes(
        target, profile=args.profile, require_venv=bool(args.with_venv)
    )
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
        help=(
            "Kit root or payload/ (default: auto — WORKFLOW_KIT_PAYLOAD, ./payload, "
            "kit root, then ~/.cursor/plugins/cache/agent-colony/*/payload)"
        ),
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
        "--keep-smoke-test",
        action="store_true",
        help="Opt-in: leave tests/modules/smoke/test_kit_installed.py (default: omit)",
    )
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
