"""
File: mcp_manage.py
Path: .ai_infra/install/agent_colony/mcp_manage.py
Role: Merge kit + user MCP JSON; validate registry against mcp.json; doctor helpers.
Used By:
 - .ai_infra/install/agent_colony/cli.py
 - .ai_infra/install/agent_colony/mcp_cli.py
 - .ai_infra/scripts/install/scaffold.py
Depends On:
 - json, yaml (PyYAML)
Notes:
 - Never overwrites existing mcp.user.json wholesale on install.
 - Consumer activate may seed DeepWiki (user-tier) when fragment/registry keys are missing.
 - Kit-dev: live registry/mcp.json stay kit-tier; smoke/call allowlist uses example overlay
   via effective_registry_servers for servers present in merged mcpServers.
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
# Same marker as scaffold.py — kit-dev must not commit user-tier into live mcp.json.
KIT_DEV_MARKER = Path("tests") / "modules" / "install" / "test_scaffold.py"

DEEPWIKI_SERVER_ID = "deepwiki"
DEEPWIKI_URL = "https://mcp.deepwiki.com/mcp"
DEEPWIKI_AGENTS: tuple[str, ...] = (
    "implementer",
    "test-runner",
    "verifier",
    "auditor",
    "researcher",
    "integrator",
    "drift-guard",
)
DEEPWIKI_TOOLS_HINT: tuple[str, ...] = (
    "read_wiki_structure",
    "read_wiki_contents",
    "ask_question",
)

KIT_REGISTRY_SERVER: dict[str, Any] = {
    "tier": "kit",
    "description": "PR workflow, trackers, gates",
    "agents": [
        "implementer",
        "test-runner",
        "verifier",
        "auditor",
        "researcher",
        "integrator",
        "drift-guard",
    ],
    "tools_hint": [
        "workflow_run_prepare",
        "workflow_get_tracker",
        "workflow_list_mcp_registry",
        "workflow_integrate_validate",
        "workflow_drift_validate",
    ],
}

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GH = 3
EXIT_NOT_FOUND = 4
EXIT_VALIDATION = 5
EXIT_QUEUED = 6


def is_kit_dev_repo(root: Path) -> bool:
    """True when target tree includes kit install tests (maintainer checkout)."""
    return (root / KIT_DEV_MARKER).is_file()


def deepwiki_user_server_spec() -> dict[str, Any]:
    return {"url": DEEPWIKI_URL}


def deepwiki_registry_entry() -> dict[str, Any]:
    return {
        "tier": "external",
        "description": "Public GitHub repo docs/Q&A (no auth) — Cognition DeepWiki",
        "agents": list(DEEPWIKI_AGENTS),
        "tools_hint": list(DEEPWIKI_TOOLS_HINT),
    }


def ensure_deepwiki_user_fragment(root: Path, *, only_if_missing: bool = True) -> bool:
    """
    Ensure mcp.user.json contains DeepWiki URL transport.

    Returns True when a write occurred. Never replaces an existing deepwiki entry
    when only_if_missing is True. Never copies my-custom-server from the example.
    """
    user_path = root / USER_FRAGMENT
    if user_path.is_file():
        user = _read_json(user_path)
        servers = user.setdefault("mcpServers", {})
        if not isinstance(servers, dict):
            raise ValueError("existing mcp.user.json mcpServers must be an object")
        if only_if_missing and DEEPWIKI_SERVER_ID in servers:
            return False
        servers[DEEPWIKI_SERVER_ID] = deepwiki_user_server_spec()
        user_path.write_text(json.dumps(user, indent=2) + "\n", encoding="utf-8")
        return True

    payload = {"mcpServers": {DEEPWIKI_SERVER_ID: deepwiki_user_server_spec()}}
    user_path.parent.mkdir(parents=True, exist_ok=True)
    user_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return True


def ensure_deepwiki_registry(
    root: Path,
    *,
    only_if_missing_server: bool = True,
    force_registry_agents: bool = False,
) -> bool:
    """
    Ensure live mcp.registry.yaml includes kit server + deepwiki.

    Returns True when a write occurred. Does not replace an existing deepwiki
    agents list unless force_registry_agents is True. Never bulk-copies the example.
    """
    reg_path = root / REGISTRY
    wrote = False

    if reg_path.is_file():
        data = yaml.safe_load(reg_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"invalid registry YAML: {reg_path}")
        servers = data.setdefault("servers", {})
        if not isinstance(servers, dict):
            raise ValueError("registry servers must be a mapping")
    else:
        data = {"version": 1, "servers": {}}
        servers = data["servers"]
        wrote = True

    if "agent-colony-mcp" not in servers:
        example_path = root / REGISTRY_EXAMPLE
        kit_entry = dict(KIT_REGISTRY_SERVER)
        if example_path.is_file():
            example = yaml.safe_load(example_path.read_text(encoding="utf-8"))
            if isinstance(example, dict):
                ex_servers = example.get("servers") or {}
                if isinstance(ex_servers, dict):
                    kit = ex_servers.get("agent-colony-mcp")
                    if isinstance(kit, dict):
                        kit_entry = kit
        servers["agent-colony-mcp"] = kit_entry
        wrote = True

    if DEEPWIKI_SERVER_ID in servers:
        if force_registry_agents:
            existing = servers[DEEPWIKI_SERVER_ID]
            if not isinstance(existing, dict):
                existing = {}
            existing["agents"] = list(DEEPWIKI_AGENTS)
            if "tools_hint" not in existing:
                existing["tools_hint"] = list(DEEPWIKI_TOOLS_HINT)
            if "tier" not in existing:
                existing["tier"] = "external"
            if "description" not in existing:
                existing["description"] = deepwiki_registry_entry()["description"]
            servers[DEEPWIKI_SERVER_ID] = existing
            wrote = True
        elif only_if_missing_server:
            pass
        else:
            servers[DEEPWIKI_SERVER_ID] = deepwiki_registry_entry()
            wrote = True
    else:
        servers[DEEPWIKI_SERVER_ID] = deepwiki_registry_entry()
        wrote = True

    if not wrote:
        return False

    data["version"] = int(data.get("version") or 1)
    data["servers"] = servers
    reg_path.parent.mkdir(parents=True, exist_ok=True)
    reg_path.write_text(
        yaml.safe_dump(data, sort_keys=False, default_flow_style=False),
        encoding="utf-8",
    )
    return True


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


def compute_merged_mcp(root: Path) -> dict[str, Any]:
    """In-memory kit + user merge (CLI allowlist / validate). Does not write disk."""
    kit_path = root / KIT_FRAGMENT
    if not kit_path.is_file():
        raise FileNotFoundError(f"missing kit MCP fragment: {kit_path}")
    kit = _strip_private_keys(_read_json(kit_path))
    user_path = root / USER_FRAGMENT
    user = _strip_private_keys(_read_json(user_path)) if user_path.is_file() else None
    return merge_mcp_configs(kit, user)


def write_merged_mcp(root: Path, *, dry_run: bool = False) -> Path:
    """
    Write `.cursor/mcp.json` for the Cursor host.

    Consumers: full kit+user merge.
    Kit-dev: kit fragment only — user-tier stays in gitignored mcp.user.json so
    validate/doctor/health cannot pollute the tracked mcp.json.
    """
    kit_path = root / KIT_FRAGMENT
    if not kit_path.is_file():
        raise FileNotFoundError(f"missing kit MCP fragment: {kit_path}")
    kit = _strip_private_keys(_read_json(kit_path))
    user_path = root / USER_FRAGMENT
    user = _strip_private_keys(_read_json(user_path)) if user_path.is_file() else None
    merged = merge_mcp_configs(kit, user)
    kit_dev = is_kit_dev_repo(root)
    payload = kit if kit_dev else merged
    dest = root / MCP_JSON
    if dry_run:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
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

    try:
        merged = compute_merged_mcp(root)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        return [str(exc)]
    mcp_servers = merged.get("mcpServers", {})
    if not isinstance(mcp_servers, dict):
        return ["merged mcpServers must be an object"]

    # Kit-dev hygiene: live registry must stay kit-tier (user servers live in examples / seed).
    if is_kit_dev_repo(root):
        for name, spec in servers.items():
            if not isinstance(spec, dict):
                continue
            if str(spec.get("tier") or "") == "external":
                errors.append(
                    f"kit-dev: live registry must not list external server '{name}' "
                    f"(keep kit-tier only; use mcp.user.json + *.example / consumer seed)"
                )

    for name, spec in servers.items():
        if not isinstance(spec, dict):
            errors.append(f"registry server '{name}' must be a mapping")
            continue
        if name not in mcp_servers:
            errors.append(
                f"registry server '{name}' not in merged kit+user mcpServers "
                f"(add to {USER_FRAGMENT} or kit example)"
            )
        agents = spec.get("agents", [])
        if agents is not None and not isinstance(agents, list):
            errors.append(f"registry server '{name}' agents must be a list")

    return errors


def load_merged_servers(root: Path, *, write: bool = False) -> dict[str, Any]:
    """Return mcpServers from kit+user merge (optionally refresh on-disk mcp.json)."""
    if write:
        write_merged_mcp(root)
    merged = compute_merged_mcp(root)
    servers = merged.get("mcpServers", {})
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
    """Servers from live registry if present, else example (load_registry fallback)."""
    try:
        data = load_registry(root)
    except FileNotFoundError:
        return {}
    servers = data.get("servers") or {}
    return servers if isinstance(servers, dict) else {}


def _load_example_registry_servers(root: Path) -> dict[str, Any]:
    example = root / REGISTRY_EXAMPLE
    if not example.is_file():
        return {}
    try:
        data = yaml.safe_load(example.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(data, dict):
        return {}
    servers = data.get("servers") or {}
    return servers if isinstance(servers, dict) else {}


def effective_registry_servers(root: Path) -> dict[str, Any]:
    """
    Allowlist map for smoke/call/list-tools.

    Live registry entries win. On kit-dev, also overlay example-registry servers that
    appear in merged mcpServers but are intentionally absent from the live kit-tier
    registry (e.g. DeepWiki in mcp.user.json).
    """
    live_path = root / REGISTRY
    if live_path.is_file():
        try:
            data = yaml.safe_load(live_path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            data = None
        live: dict[str, Any] = {}
        if isinstance(data, dict):
            raw = data.get("servers") or {}
            if isinstance(raw, dict):
                live = dict(raw)
    else:
        live = dict(registry_servers(root))

    if not is_kit_dev_repo(root):
        return live

    try:
        merged = compute_merged_mcp(root)
    except (FileNotFoundError, ValueError, json.JSONDecodeError, OSError):
        return live
    mcp_servers = merged.get("mcpServers") or {}
    if not isinstance(mcp_servers, dict):
        return live

    example = _load_example_registry_servers(root)
    out = dict(live)
    for name, spec in example.items():
        if name in out:
            continue
        if name not in mcp_servers:
            continue
        if isinstance(spec, dict):
            out[name] = spec
    return out


def servers_for_agent(root: Path, agent: str | None) -> set[str] | None:
    """
    If agent is None, return None (no filter).
    If agent set, return allowlisted server names for that agent from effective registry.
    """
    if not agent:
        return None
    servers = effective_registry_servers(root)
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
    example = root / REGISTRY_EXAMPLE
    has_registry_source = reg_live.is_file() or example.is_file()
    if has_registry_source:
        servers = effective_registry_servers(root)
        if server not in servers:
            return (
                f"server '{server}' not in effective registry "
                f"(live {reg_live}"
                + (
                    f"; kit-dev also checks {example} for merged user servers"
                    if is_kit_dev_repo(root)
                    else ""
                )
                + ")"
            )
        if agent:
            allowed = servers_for_agent(root, agent)
            if allowed is not None and server not in allowed:
                return f"server '{server}' not mapped to agent '{agent}' in registry"
    merged = load_merged_servers(root)
    if server not in merged:
        return (
            f"server '{server}' not in merged mcpServers "
            f"(add to {USER_FRAGMENT} or kit example)"
        )
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


def check_agent_colony_mcp_import(root: Path) -> dict[str, Any]:
    """Report venv python + whether agent_colony_mcp is importable with kit PYTHONPATH."""
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
        [str(venv_py), "-c", "import agent_colony_mcp; print(agent_colony_mcp.__file__)"],
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


RUNTIME_GITIGNORE_LINES: tuple[str, ...] = (
    ".local/",
    ".venv/",
    ".env",
    ".env.*",
    "!.env.example",
    "__pycache__/",
    "*.py[cod]",
    ".pytest_cache/",
    ".coverage",
    "htmlcov/",
    "*.egg-info/",
)

MCP_GITIGNORE_LINES: tuple[str, ...] = (
    ".cursor/mcp.user.json",
    ".local/user_settings/mcp.secrets.yaml",
)


def _append_gitignore_lines(root: Path, lines: tuple[str, ...], *, header: str) -> None:
    gitignore = root / ".gitignore"
    if gitignore.is_file():
        text = gitignore.read_text(encoding="utf-8")
        # Exact line match — substring checks wrongly skip ".local/" when
        # ".local/user_settings/mcp.secrets.yaml" is already present.
        existing = set(text.splitlines())
        additions = [ln for ln in lines if ln not in existing]
        if additions:
            gitignore.write_text(text.rstrip() + "\n" + "\n".join(additions) + "\n", encoding="utf-8")
        return
    gitignore.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")


def ensure_runtime_gitignore(root: Path) -> None:
    """Ensure consumer .gitignore covers .local/, .venv/, and common Python runtime junk."""
    _append_gitignore_lines(
        root,
        RUNTIME_GITIGNORE_LINES,
        header="# Agent Colony runtime (activate)\n",
    )


def ensure_mcp_gitignore(root: Path) -> None:
    _append_gitignore_lines(
        root,
        MCP_GITIGNORE_LINES,
        header="# MCP secrets\n",
    )


def ensure_consumer_gitignore(root: Path) -> None:
    """Write runtime + MCP ignore lines (idempotent append)."""
    ensure_runtime_gitignore(root)
    ensure_mcp_gitignore(root)
