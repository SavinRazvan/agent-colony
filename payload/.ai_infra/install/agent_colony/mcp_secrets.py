"""
File: mcp_secrets.py
Path: .ai_infra/install/agent_colony/mcp_secrets.py
Role: Read/write MCP secrets under .local/user_settings (gitignored).
Used By:
 - .ai_infra/install/agent_colony/mcp_cli.py
 - .ai_infra/install/agent_colony/mcp_client.py
Depends On:
 - yaml
Notes:
 - Never print secret values. ADR-009.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SECRETS_REL = Path(".local") / "user_settings" / "mcp.secrets.yaml"
SECRETS_EXEMPLAR_REL = (
    Path(".ai_infra") / "templates" / "user-settings" / "exemplars" / "mcp.secrets.yaml"
)


def secrets_path(root: Path) -> Path:
    return root / SECRETS_REL


def load_secrets(root: Path) -> dict[str, Any]:
    path = secrets_path(root)
    if not path.is_file():
        return {"version": 1, "servers": {}}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"invalid secrets file: {path}")
    servers = data.get("servers")
    if servers is None:
        data["servers"] = {}
    elif not isinstance(servers, dict):
        raise ValueError("secrets servers must be a mapping")
    return data


def save_secrets(root: Path, data: dict[str, Any]) -> Path:
    path = secrets_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def set_server_secret(
    root: Path,
    server: str,
    *,
    token: str | None = None,
    header_name: str | None = None,
    env: dict[str, str] | None = None,
) -> Path:
    data = load_secrets(root)
    servers = data.setdefault("servers", {})
    if not isinstance(servers, dict):
        raise ValueError("secrets servers must be a mapping")
    entry: dict[str, Any] = {}
    if token is not None:
        entry["token"] = token
    if header_name:
        entry["header"] = header_name
    if env:
        entry["env"] = dict(env)
    existing = servers.get(server)
    if isinstance(existing, dict):
        existing.update(entry)
        servers[server] = existing
    else:
        servers[server] = entry
    data["version"] = int(data.get("version") or 1)
    return save_secrets(root, data)


def secrets_for_server(root: Path, server: str) -> dict[str, Any]:
    data = load_secrets(root)
    servers = data.get("servers") or {}
    if not isinstance(servers, dict):
        return {}
    entry = servers.get(server)
    return dict(entry) if isinstance(entry, dict) else {}


def http_headers_from_secrets(entry: dict[str, Any]) -> dict[str, str]:
    headers: dict[str, str] = {}
    token = entry.get("token")
    if isinstance(token, str) and token:
        header = entry.get("header")
        name = header if isinstance(header, str) and header else "Authorization"
        if name.lower() == "authorization" and not token.lower().startswith("bearer "):
            headers[name] = f"Bearer {token}"
        else:
            headers[name] = token
    extra = entry.get("headers")
    if isinstance(extra, dict):
        for k, v in extra.items():
            if isinstance(k, str) and isinstance(v, str):
                headers[k] = v
    return headers


def env_from_secrets(entry: dict[str, Any]) -> dict[str, str]:
    env = entry.get("env")
    if not isinstance(env, dict):
        return {}
    return {str(k): str(v) for k, v in env.items()}
