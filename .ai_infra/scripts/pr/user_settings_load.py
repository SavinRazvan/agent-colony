"""
File: user_settings_load.py
Path: .ai_infra/scripts/pr/user_settings_load.py
Role: Load and schema-validate `.local/user_settings/` YAML worksheets.
Used By:
 - user_settings.py
 - user_settings_resolve.py
 - user_settings_render.py
Depends On:
 - pathlib
 - yaml (PyYAML)
Notes:
 - `.local/user_settings/` is gitignored; exemplars ship under .ai_infra/templates/user-settings/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml

from local_workflow_paths import DEFAULT_GITHUB_USER

GITHUB_COLLAB_REL = Path(".local") / "user_settings" / "github.collaboration.yaml"
MCP_AGENTS_REL = Path(".local") / "user_settings" / "mcp.agents.yaml"

SCHEMAS_DIR = Path(__file__).resolve().parents[2] / "schemas"
GITHUB_COLLAB_SCHEMA = SCHEMAS_DIR / "github-collaboration.schema.json"
MCP_AGENTS_SCHEMA = SCHEMAS_DIR / "mcp-agents.schema.json"

PLACEHOLDER_DISPLAY_NAMES = frozenset({"Your Full Name", "Your Name"})
PLACEHOLDER_GITHUB_USERS = frozenset({"@yourhandle", "@YourGitHubHandle", "yourhandle"})

PIPELINE_NAMES = (
    "default",
    "architecture_impacting",
    "multi_agent_feature",
    "infrastructure_integration",
)


def project_root(root: Path | None) -> Path:
    return (root or Path.cwd()).resolve()


def load_yaml(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML syntax error in {path}: {exc}") from exc
    if not isinstance(data, dict):
        return None
    return data


def validate_against_schema(data: dict[str, Any], schema_path: Path) -> list[str]:
    if not schema_path.is_file():
        return [f"missing schema {schema_path.name}"]
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        errors.append(f"{path}: {err.message}")
    return errors


def github_collaboration_path(root: Path | None = None) -> Path:
    return project_root(root) / GITHUB_COLLAB_REL


def mcp_agents_path(root: Path | None = None) -> Path:
    return project_root(root) / MCP_AGENTS_REL


def load_github_collaboration(root: Path | None = None) -> dict[str, Any] | None:
    return load_yaml(github_collaboration_path(root))


def load_mcp_agents(root: Path | None = None) -> dict[str, Any] | None:
    return load_yaml(mcp_agents_path(root))


def normalize_github_user(raw: str) -> str:
    text = raw.strip()
    if not text:
        return DEFAULT_GITHUB_USER
    return text if text.startswith("@") else f"@{text}"


def is_placeholder_owner(cfg: dict[str, Any]) -> bool:
    owner = cfg.get("owner") or {}
    name = str(owner.get("display_name", "")).strip()
    handle = normalize_github_user(str(owner.get("github_user", "")))
    if not name or name in PLACEHOLDER_DISPLAY_NAMES:
        return True
    if handle in PLACEHOLDER_GITHUB_USERS:
        return True
    return False


def validate_github_collaboration_schema(root: Path | None = None) -> list[str]:
    cfg = load_github_collaboration(root)
    if cfg is None:
        return [f"invalid YAML in {GITHUB_COLLAB_REL}"]
    return validate_against_schema(cfg, GITHUB_COLLAB_SCHEMA)


def validate_mcp_agents_schema(root: Path | None = None) -> list[str]:
    cfg = load_mcp_agents(root)
    if cfg is None:
        return [f"invalid YAML in {MCP_AGENTS_REL}"]
    return validate_against_schema(cfg, MCP_AGENTS_SCHEMA)
