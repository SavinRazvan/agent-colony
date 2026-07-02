"""
File: mcp_manage.py
Path: .ai_infra/install/cursor_workflow/mcp_manage.py
Role: Merge kit + user MCP JSON; validate registry against mcp.json.
Used By:
 - .ai_infra/install/cursor_workflow/cli.py
 - .ai_infra/scripts/install/scaffold.py
Depends On:
 - json, yaml (PyYAML)
Notes:
 - Never overwrites existing mcp.user.json on install.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import yaml

KIT_FRAGMENT = Path(".cursor") / "mcp.json.kit.example"
USER_FRAGMENT = Path(".cursor") / "mcp.user.json"
USER_EXAMPLE = Path(".cursor") / "mcp.user.example.json"
REGISTRY = Path(".cursor") / "mcp.registry.yaml"
REGISTRY_EXAMPLE = Path(".cursor") / "mcp.registry.yaml.example"
MCP_JSON = Path(".cursor") / "mcp.json"


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


def validate_registry(root: Path) -> list[str]:
    errors: list[str] = []
    registry_path = root / REGISTRY
    if not registry_path.is_file():
        return []
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

    return errors


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
    line = ".cursor/mcp.user.json"
    if gitignore.is_file():
        text = gitignore.read_text(encoding="utf-8")
        if line not in text:
            gitignore.write_text(text.rstrip() + f"\n{line}\n", encoding="utf-8")
    else:
        gitignore.write_text(f"# MCP secrets\n{line}\n", encoding="utf-8")
