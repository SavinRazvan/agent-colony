"""
File: mcp_cli.py
Path: .ai_infra/install/cursor_workflow/mcp_cli.py
Role: Pattern A MCP CLI handlers — doctor, list-tools, call, auth, smoke.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
Depends On:
 - mcp_manage, mcp_client, mcp_secrets
Notes:
 - ADR-009. Exit codes align with project CLI.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import mcp_client
import mcp_manage
import mcp_secrets


def _artifact_dir(root: Path) -> Path:
    path = root / ".local" / "workflow-artifacts" / "mcp"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_artifact(root: Path, prefix: str, body: str) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = _artifact_dir(root) / f"{prefix}-{stamp}.md"
    path.write_text(body, encoding="utf-8")
    return path


def build_doctor_report(root: Path) -> dict[str, Any]:
    try:
        merged = mcp_manage.load_merged_servers(root, write=False)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        merged = {}
        merge_error = str(exc)
    else:
        merge_error = None

    reg_path = mcp_manage.registry_path_used(root)
    reg_live = (root / mcp_manage.REGISTRY).is_file()
    user_live = (root / mcp_manage.USER_FRAGMENT).is_file()
    servers_reg = mcp_manage.registry_servers(root)

    agent_map: dict[str, list[str]] = {}
    for name, spec in servers_reg.items():
        if not isinstance(spec, dict):
            continue
        agents = spec.get("agents") or []
        if isinstance(agents, list):
            for agent in agents:
                if isinstance(agent, str) and agent:
                    agent_map.setdefault(agent, []).append(name)

    mcps_dir = mcp_manage.cursor_project_mcps_dir(root)
    host_loaded = mcp_manage.list_cursor_host_servers(mcps_dir)
    configured = sorted(merged.keys())
    host_set = set(host_loaded)
    cfg_set = set(configured)

    import_info = mcp_manage.check_workflow_mcp_import(root)

    return {
        "root": str(root),
        "merged_servers": configured,
        "merge_error": merge_error,
        "user_fragment_present": user_live,
        "registry_path": str(reg_path) if reg_path else None,
        "registry_live": reg_live,
        "registry_servers": sorted(servers_reg.keys()),
        "agent_mappings": {k: sorted(v) for k, v in sorted(agent_map.items())},
        "workflow_mcp": import_info,
        "cursor_mcps_dir": str(mcps_dir) if mcps_dir else None,
        "cursor_host_loaded": host_loaded,
        "configured_not_host_loaded": sorted(cfg_set - host_set),
        "host_loaded_not_configured": sorted(host_set - cfg_set),
    }


def format_doctor_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# MCP doctor",
        "",
        f"- root: `{report['root']}`",
        f"- user fragment (mcp.user.json): {'yes' if report['user_fragment_present'] else 'no'}",
        f"- registry: `{report['registry_path']}` "
        f"({'live' if report['registry_live'] else 'example/fallback'})",
        f"- merged servers: {', '.join(report['merged_servers']) or '(none)'}",
        f"- registry servers: {', '.join(report['registry_servers']) or '(none)'}",
        "",
        "## Configured vs Cursor host",
        "",
        f"- cursor mcps dir: `{report['cursor_mcps_dir'] or '(not found)'}`",
        f"- host-loaded: {', '.join(report['cursor_host_loaded']) or '(none)'}",
        f"- configured but NOT host-loaded: "
        f"{', '.join(report['configured_not_host_loaded']) or '(none)'}",
        f"- host-loaded but not in mcp.json: "
        f"{', '.join(report['host_loaded_not_configured']) or '(none)'}",
        "",
        "## workflow_mcp import",
        "",
        f"- venv: `{report['workflow_mcp'].get('venv_python')}`",
        f"- import_ok: {report['workflow_mcp'].get('import_ok')}",
    ]
    if report["workflow_mcp"].get("error"):
        lines.append(f"- error: {report['workflow_mcp']['error']}")
    if report.get("merge_error"):
        lines.extend(["", f"**merge error:** {report['merge_error']}"])
    lines.extend(["", "## Agent mappings", ""])
    mappings = report.get("agent_mappings") or {}
    if not mappings:
        lines.append("(none)")
    else:
        for agent, servers in mappings.items():
            lines.append(f"- `{agent}`: {', '.join(servers)}")
    lines.append("")
    return "\n".join(lines)


def cmd_mcp_doctor(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        mcp_manage.write_merged_mcp(root)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp doctor: WARN — merge failed: {exc}", file=sys.stderr)
    report = build_doctor_report(root)
    body = format_doctor_markdown(report)
    print(body)
    art = _write_artifact(root, "doctor", body)
    print(f"artifact: {art}")
    return mcp_manage.EXIT_OK


def cmd_mcp_validate(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    strict = bool(getattr(args, "strict", False))
    try:
        mcp_manage.write_merged_mcp(root)
        errors = mcp_manage.validate_registry(root, strict=strict)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp validate: FAIL — {exc}", file=sys.stderr)
        return 1
    if errors:
        print("mcp validate: FAIL")
        for err in errors:
            print(f" - {err}")
        return 1
    print("mcp validate: PASS" + (" (strict)" if strict else ""))
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


def cmd_mcp_list_tools(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        mcp_manage.write_merged_mcp(root)
        tools = mcp_client.list_tools(root, args.server, agent=args.agent)
    except mcp_client.McpClientError as exc:
        print(f"mcp list-tools: FAIL — {exc}", file=sys.stderr)
        return int(exc.code)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp list-tools: FAIL — {exc}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    for tool in tools:
        desc = (tool.get("description") or "").replace("\n", " ")
        print(f"{tool['name']}\t{desc}")
    return mcp_manage.EXIT_OK


def cmd_mcp_call(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    try:
        mcp_manage.write_merged_mcp(root)
        arguments = mcp_client.parse_args_json(args.args_json)
        result = mcp_client.call_tool(
            root,
            args.server,
            args.tool,
            arguments,
            agent=args.agent,
        )
    except mcp_client.McpClientError as exc:
        print(f"mcp call: FAIL — {exc}", file=sys.stderr)
        return int(exc.code)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp call: FAIL — {exc}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    if isinstance(result, (dict, list)):
        print(json.dumps(result, indent=2, default=str))
    else:
        print(result)
    return mcp_manage.EXIT_OK


def cmd_mcp_auth(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    token = args.token
    if not token and args.token_env:
        import os

        token = os.environ.get(args.token_env)
        if not token:
            print(
                f"mcp auth: FAIL — env {args.token_env} empty",
                file=sys.stderr,
            )
            return mcp_manage.EXIT_USAGE
    if not token and not args.env_pair:
        print(
            "mcp auth: FAIL — pass --token, --token-env, or --env KEY=VALUE",
            file=sys.stderr,
        )
        return mcp_manage.EXIT_USAGE
    env_map: dict[str, str] = {}
    for pair in args.env_pair or []:
        if "=" not in pair:
            print(f"mcp auth: FAIL — bad --env {pair}", file=sys.stderr)
            return mcp_manage.EXIT_USAGE
        k, v = pair.split("=", 1)
        env_map[k] = v
    try:
        path = mcp_secrets.set_server_secret(
            root,
            args.server,
            token=token,
            header_name=args.header,
            env=env_map or None,
        )
        mcp_manage.ensure_mcp_gitignore(root)
    except (OSError, ValueError) as exc:
        print(f"mcp auth: FAIL — {exc}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    print(f"mcp auth: stored secrets for '{args.server}' at {path} (values not printed)")
    return mcp_manage.EXIT_OK


def cmd_mcp_smoke(args: argparse.Namespace) -> int:
    root = Path(args.directory).resolve()
    server = args.server
    try:
        mcp_manage.write_merged_mcp(root)
        result = mcp_client.smoke_server(root, server, agent=args.agent)
    except mcp_client.McpClientError as exc:
        print(f"mcp smoke: FAIL — {exc}", file=sys.stderr)
        body = f"# MCP smoke FAIL\n\n- server: `{server}`\n- error: {exc}\n"
        art = _write_artifact(root, "smoke", body)
        print(f"artifact: {art}", file=sys.stderr)
        return int(exc.code)
    except (FileNotFoundError, ValueError) as exc:
        print(f"mcp smoke: FAIL — {exc}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    body = (
        f"# MCP smoke OK\n\n"
        f"- server: `{server}`\n"
        f"- tool_count: {result['tool_count']}\n"
        f"- tools: {', '.join(result['tools'])}\n"
    )
    print(body)
    art = _write_artifact(root, "smoke", body)
    print(f"artifact: {art}")
    return mcp_manage.EXIT_OK


def cmd_mcp_seed(args: argparse.Namespace) -> int:
    """Seed DeepWiki user fragment + registry (re-run without full activate)."""
    root = Path(args.directory).resolve()
    seed_deepwiki = bool(getattr(args, "deepwiki", True))
    force_agents = bool(getattr(args, "force_registry_agents", False))
    if not seed_deepwiki:
        print("mcp seed: FAIL — pass --deepwiki (only seed target today)", file=sys.stderr)
        return mcp_manage.EXIT_USAGE
    try:
        user_wrote = mcp_manage.ensure_deepwiki_user_fragment(root)
        reg_wrote = False
        if mcp_manage.is_kit_dev_repo(root):
            print(
                "mcp seed: WARN — kit-dev: seeded user fragment only; "
                "live registry stays kit-tier (use consumer activate for full seed)",
                file=sys.stderr,
            )
        else:
            reg_wrote = mcp_manage.ensure_deepwiki_registry(
                root,
                force_registry_agents=force_agents,
            )
        mcp_manage.write_merged_mcp(root)
        mcp_manage.ensure_mcp_gitignore(root)
        errors = mcp_manage.validate_registry(root)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"mcp seed: FAIL — {exc}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    body = (
        "# MCP seed\n\n"
        f"- root: `{root}`\n"
        f"- deepwiki: yes\n"
        f"- user_fragment_wrote: {user_wrote}\n"
        f"- registry_wrote: {reg_wrote}\n"
        f"- force_registry_agents: {force_agents}\n"
        f"- validate: {'PASS' if not errors else 'FAIL'}\n"
    )
    if errors:
        body += "\n## Errors\n\n" + "\n".join(f"- {e}" for e in errors) + "\n"
        print("mcp seed: FAIL — validate after seed")
        for err in errors:
            print(f" - {err}")
        art = _write_artifact(root, "seed", body)
        print(f"artifact: {art}", file=sys.stderr)
        return mcp_manage.EXIT_VALIDATION
    print(
        f"mcp seed: OK — deepwiki "
        f"(user_wrote={user_wrote}, registry_wrote={reg_wrote}); validate PASS"
    )
    art = _write_artifact(root, "seed", body)
    print(f"artifact: {art}")
    return mcp_manage.EXIT_OK


def register_mcp_subcommands(mcp_sub: Any) -> None:
    """Attach Pattern A MCP subparsers to an existing `mcp` subparser group."""
    mcp_validate = mcp_sub.add_parser("validate", help="Merge kit+user MCP and validate registry")
    mcp_validate.add_argument("--directory", type=Path, default=".")
    mcp_validate.add_argument(
        "--strict",
        action="store_true",
        help="Fail when live registry is missing or external entries absent from mcp.json",
    )
    mcp_validate.set_defaults(func=cmd_mcp_validate)

    mcp_link = mcp_sub.add_parser("link", help="Link external MCP server fragment into mcp.user.json")
    mcp_link.add_argument("--name", required=True, help="Server name in mcp.user.json")
    mcp_link.add_argument("--file", required=True, type=Path, help="JSON fragment with mcpServers")
    mcp_link.add_argument("--directory", type=Path, default=".")
    mcp_link.set_defaults(func=cmd_mcp_link)

    doctor = mcp_sub.add_parser("doctor", help="Report MCP config vs Cursor host load status")
    doctor.add_argument("--directory", type=Path, default=".")
    doctor.set_defaults(func=cmd_mcp_doctor)

    list_tools = mcp_sub.add_parser("list-tools", help="List tools for an allowlisted MCP server")
    list_tools.add_argument("--directory", type=Path, default=".")
    list_tools.add_argument("--server", required=True)
    list_tools.add_argument("--agent", default=None, help="Filter by registry agent mapping")
    list_tools.set_defaults(func=cmd_mcp_list_tools)

    call = mcp_sub.add_parser("call", help="Call a tool on an allowlisted MCP server")
    call.add_argument("--directory", type=Path, default=".")
    call.add_argument("--server", required=True)
    call.add_argument("--tool", required=True)
    call.add_argument("--args-json", default=None, help='JSON object, e.g. \'{"repo":"org/name"}\'')
    call.add_argument("--agent", default=None)
    call.set_defaults(func=cmd_mcp_call)

    auth = mcp_sub.add_parser("auth", help="Store MCP secrets under .local/user_settings")
    auth.add_argument("--directory", type=Path, default=".")
    auth.add_argument("--server", required=True)
    auth.add_argument("--token", default=None, help="Bearer/token value (not echoed later)")
    auth.add_argument("--token-env", default=None, help="Read token from environment variable")
    auth.add_argument("--header", default=None, help="HTTP header name (default Authorization)")
    auth.add_argument(
        "--env",
        dest="env_pair",
        action="append",
        default=[],
        help="KEY=VALUE env injected for stdio servers (repeatable)",
    )
    auth.set_defaults(func=cmd_mcp_auth)

    smoke = mcp_sub.add_parser("smoke", help="Initialize server and list tools; write evidence")
    smoke.add_argument("--directory", type=Path, default=".")
    smoke.add_argument("--server", required=True)
    smoke.add_argument("--agent", default=None)
    smoke.set_defaults(func=cmd_mcp_smoke)

    seed = mcp_sub.add_parser(
        "seed",
        help="Seed DeepWiki into mcp.user.json + registry (consumer default / re-run)",
    )
    seed.add_argument("--directory", type=Path, default=".")
    seed.add_argument(
        "--deepwiki",
        action="store_true",
        default=True,
        help="Seed DeepWiki user transport + registry (default)",
    )
    seed.add_argument(
        "--no-deepwiki",
        action="store_false",
        dest="deepwiki",
        help="Disable DeepWiki seed (no other seed targets yet)",
    )
    seed.add_argument(
        "--force-registry-agents",
        action="store_true",
        help="Overwrite deepwiki.agents in live registry with kit default seven",
    )
    seed.set_defaults(func=cmd_mcp_seed)
