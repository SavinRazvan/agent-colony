"""
File: mcp_manage.py
Path: .ai_infra/install/cursor_workflow/mcp_manage.py
Role: Merge kit + user MCP JSON; validate registry against mcp.json; doctor helpers.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .ai_infra/install/cursor_workflow/mcp_cli.py
 - .ai_infra/scripts/install/scaffold.py
Depends On:
 - json, yaml (PyYAML)
Notes:
 - Never overwrites existing mcp.user.json on install.
 - Pattern A CLI: ADR-009.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import yaml

import cursor_host_paths

KIT_FRAGMENT = Path(".cursor") / "mcp.json.kit.example"
USER_FRAGMENT = Path(".cursor") / "mcp.user.json"
USER_EXAMPLE = Path(".cursor") / "mcp.user.example.json"
REGISTRY = Path(".cursor") / "mcp.registry.yaml"
REGISTRY_EXAMPLE = Path(".cursor") / "mcp.registry.yaml.example"
MCP_JSON = Path(".cursor") / "mcp.json"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GH = 3
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5
EXIT_QUEUED = 6


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def _strip_private_keys(obj: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in obj.items():
        if str(key).startswith("_"):
            continue
        if isinstance(value, dict):
            cleaned[key] = _strip_private_keys(value)
        else:
            cleaned[key] = value
    return cleaned


def merge_mcp_configs(kit: dict[str, Any], user: dict[str, Any] | None = None) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    kit_servers = kit.get("mcpServers", {})
    if not isinstance(kit_servers, dict):
        raise ValueError("kit mcpServers must be an object")
    merged_servers = {k: v for k, v in kit_servers.items()}
    if user:
        user_servers = user.get("mcpServers", {})
        if not isinstance(user_servers, dict):
            raise ValueError("user mcpServers must be an object")
        for name, spec in user_servers.items():
            if str(name).startswith("_"):
                continue
            merged_servers[name] = spec
    merged["mcpServers"] = merged_servers
    return merged


def write_merged_mcp(root: Path, *, dry_run: bool = False) -> Path:
    kit_path = root / KIT_FRAGMENT
    if not kit_path.is_file():
        raise FileNotFoundError(f"missing kit MCP fragment: {kit_path}")
    kit = _strip_private_keys(_read_json(kit_path))
    user_path = root / USER_FRAGMENT
    user = _strip_private_keys(_read_json(user_path)) if user_path.is_file() else None
    merged = merge_mcp_configs(kit, user)
    dest = root / MCP_JSON
    if dry_run:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(merged, indent=2) + "\n", encoding="utf-8")
    return dest


def load_registry(root: Path) -> dict[str, Any]:
    path = root / REGISTRY
    if not path.is_file():
        example = root / REGISTRY_EXAMPLE
        if not example.is_file():
            raise FileNotFoundError(f"missing registry: {path} or {example}")
        path = example
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid registry YAML: {path}")
    return data


def validate_registry(root: Path, *, strict: bool = False) -> list[str]:
    errors: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.is_file():
        if strict:
            errors.append(
                f"strict: missing live registry {registry_path} "
                f"(copy from {REGISTRY_EXAMPLE})"
            )
        return errors
    try:
        registry = load_registry(root)
    except (FileNotFoundError, ValueError) as exc:
        return [str(exc)]

    servers = registry.get("servers", {})
    if not isinstance(servers, dict):
        return ["registry servers must be a mapping"]

    mcp_path = root / MCP_JSON
    if not mcp_path.is_file():
        return [f"missing merged MCP config: {mcp_path}"]

    mcp = _read_json(mcp_path)
    mcp_servers = mcp.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        return ["mcp.json mcpServers must be an object"]

    for name, spec in servers.items():
        if not isinstance(spec, dict):
            errors.append(f"registry server '{name}' must be a mapping")
            continue
        if name not in mcp_servers:
            errors.append(f"registry server '{name}' not in .cursor/mcp.json mcpServers")
        agents = spec.get("agents", [])
        if agents is not None and not isinstance(agents, list):
            errors.append(f"registry server '{name}' agents must be a list")
        if strict and isinstance(spec, dict):
            tier = str(spec.get("tier") or "")
            if tier == "external" and name not in mcp_servers:
                # already covered above; keep for clarity
                pass

    if strict and not (root / USER_FRAGMENT).is_file():
        # Kit-only is OK unless registry lists external servers missing from merge
        for name, spec in servers.items():
            if not isinstance(spec, dict):
                continue
            if str(spec.get("tier") or "") == "external" and name not in mcp_servers:
                errors.append(
                    f"strict: external registry server '{name}' missing from mcp.json "
                    f"(add to {USER_FRAGMENT} and re-validate)"
                )

    return errors


def load_merged_servers(root: Path, *, write: bool = False) -> dict[str, Any]:
    """Return mcpServers from merged kit+user (optionally rewrite mcp.json)."""
    if write:
        write_merged_mcp(root)
    mcp_path = root / MCP_JSON
    if not mcp_path.is_file():
        write_merged_mcp(root)
    mcp = _read_json(root / MCP_JSON)
    servers = mcp.get("mcpServers", {})
    if not isinstance(servers, dict):
        raise ValueError("mcp.json mcpServers must be an object")
    return {k: v for k, v in servers.items() if isinstance(v, dict)}


def registry_path_used(root: Path) -> Path | None:
    live = root / REGISTRY
    if live.is_file():
        return live
    example = root / REGISTRY_EXAMPLE
    if example.is_file():
        return example
    return None


def registry_servers(root: Path) -> dict[str, Any]:
    try:
        data = load_registry(root)
    except FileNotFoundError:
        return {}
    servers = data.get("servers") or {}
    return servers if isinstance(servers, dict) else {}


def servers_for_agent(root: Path, agent: str | None) -> set[str] | None:
    """
    If agent is None, return None (no filter).
    If agent set, return allowlisted server names for that agent from registry.
    """
    if not agent:
        return None
    servers = registry_servers(root)
    allowed: set[str] = set()
    for name, spec in servers.items():
        if not isinstance(spec, dict):
            continue
        agents = spec.get("agents") or []
        if isinstance(agents, list) and agent in agents:
            allowed.add(name)
    return allowed


def assert_server_allowed(
    root: Path,
    server: str,
    *,
    agent: str | None = None,
) -> str | None:
    """Return error message if server not allowlisted; None if OK."""
    reg_live = root / REGISTRY
    if reg_live.is_file():
        servers = registry_servers(root)
        if server not in servers:
            return f"server '{server}' not in registry {reg_live}"
        if agent:
            allowed = servers_for_agent(root, agent)
            if allowed is not None and server not in allowed:
                return f"server '{server}' not mapped to agent '{agent}' in registry"
    merged = load_merged_servers(root)
    if server not in merged:
        return f"server '{server}' not in merged mcp.json mcpServers"
    return None


def expand_server_env(spec: dict[str, Any], root: Path) -> dict[str, Any]:
    """Expand ${workspaceFolder} in command/args/env for local spawn."""
    root_s = str(root)
    out = dict(spec)

    def _expand(val: Any) -> Any:
        if isinstance(val, str):
            return val.replace("${workspaceFolder}", root_s)
        if isinstance(val, list):
            return [_expand(v) for v in val]
        if isinstance(val, dict):
            return {k: _expand(v) for k, v in val.items()}
        return val

    return _expand(out)  # type: ignore[return-value]


def cursor_project_mcps_dir(root: Path) -> Path | None:
    """Best-effort path to Cursor's per-project mcps cache for this workspace."""
    return cursor_host_paths.cursor_project_mcps_dir(root)


def list_cursor_host_servers(mcps_dir: Path | None) -> list[str]:
    if mcps_dir is None or not mcps_dir.is_dir():
        return []
    return sorted(p.name for p in mcps_dir.iterdir() if p.is_dir() and not p.name.startswith("."))


def check_workflow_mcp_import(root: Path) -> dict[str, Any]:
    """Report venv python + whether workflow_mcp is importable with kit PYTHONPATH."""
    venv_py = root / ".venv" / "bin" / "python"
    servers_path = root / ".ai_infra" / "mcp_servers"
    result: dict[str, Any] = {
        "venv_python": str(venv_py) if venv_py.is_file() else None,
        "mcp_servers_path": str(servers_path) if servers_path.is_dir() else None,
        "import_ok": False,
        "error": None,
    }
    if not venv_py.is_file() or not servers_path.is_dir():
        result["error"] = "missing .venv/bin/python or .ai_infra/mcp_servers"
        return result
    import subprocess

    env = {**os.environ, "PYTHONPATH": str(servers_path)}
    proc = subprocess.run(
        [str(venv_py), "-c", "import workflow_mcp; print(workflow_mcp.__file__)"],
        cwd=root,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    if proc.returncode == 0:
        result["import_ok"] = True
        result["module_file"] = proc.stdout.strip()
    else:
        result["error"] = (proc.stderr or proc.stdout or "import failed").strip()
    return result


def link_user_server(root: Path, name: str, fragment_file: Path) -> None:
    fragment = _strip_private_keys(_read_json(fragment_file))
    fragment_servers = fragment.get("mcpServers", {})
    if not isinstance(fragment_servers, dict) or not fragment_servers:
        raise ValueError("fragment must contain mcpServers with at least one entry")

    user_path = root / USER_FRAGMENT
    if user_path.is_file():
        user = _read_json(user_path)
    else:
        example = root / USER_EXAMPLE
        user = _read_json(example) if example.is_file() else {"mcpServers": {}}

    user_servers = user.setdefault("mcpServers", {})
    if not isinstance(user_servers, dict):
        raise ValueError("existing mcp.user.json mcpServers must be an object")

    if name in fragment_servers:
        user_servers[name] = fragment_servers[name]
    else:
        if len(fragment_servers) == 1:
            only_key = next(iter(fragment_servers))
            user_servers[name] = fragment_servers[only_key]
        else:
            raise ValueError(
                f"fragment has multiple servers; pass --name matching a key in {fragment_file}"
            )

    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_text(json.dumps(user, indent=2) + "\n", encoding="utf-8")
    write_merged_mcp(root)


def ensure_mcp_gitignore(root: Path) -> None:
    gitignore = root / ".gitignore"
    lines = [
        ".cursor/mcp.user.json",
        ".local/user_settings/mcp.secrets.yaml",
    ]
    if gitignore.is_file():
        text = gitignore.read_text(encoding="utf-8")
        additions = [ln for ln in lines if ln not in text]
        if additions:
            gitignore.write_text(text.rstrip() + "\n" + "\n".join(additions) + "\n", encoding="utf-8")
    else:
        gitignore.write_text("# MCP secrets\n" + "\n".join(lines) + "\n", encoding="utf-8")
