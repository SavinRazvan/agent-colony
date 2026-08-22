"""
File: checks.py
Path: .ai_infra/scripts/integration/checks.py
Role: Shared integration parity checks for agents, registry, and pipelines.
Used By:
 - .ai_infra/scripts/integration/validate.py
 - tests/modules/mcp_registry/test_agent_mcp_blocks.py
Depends On:
 - pathlib, yaml
Notes:
 - Single source of truth for agent MCP block and Anchor requirements.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

PR_SKILL_ALIASES = frozenset({"review-pr", "prepare-pr", "merge-pr"})

REQUIRED_AGENT_MARKERS = (
    "## Anchor",
    "## MCP integration",
    "agent-colony-mcp",
    "mcp.registry.yaml",
    "agent_colony mcp",
)

CANVAS_AGENT_MARKERS = (
    "agent_colony canvas",
    "canvas-artifacts",
)

CANVAS_AGENT_IDS = frozenset({"implementer", "integrator"})


def agent_file_ids(agents_dir: Path) -> set[str]:
    if not agents_dir.is_dir():
        return set()
    return {path.stem for path in agents_dir.glob("*.md")}


def registry_agent_ids(registry_path: Path) -> set[str]:
    if not registry_path.is_file():
        return set()
    data = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return set()
    servers = data.get("servers") or {}
    ids: set[str] = set()
    for spec in servers.values():
        if not isinstance(spec, dict):
            continue
        for agent in spec.get("agents") or []:
            if isinstance(agent, str) and agent.strip():
                ids.add(agent.strip())
    return ids


def check_agent_file(path: Path) -> list[str]:
    """Return violation messages for a single agent markdown file."""
    text = path.read_text(encoding="utf-8")
    rel = path.name
    violations: list[str] = []
    for marker in REQUIRED_AGENT_MARKERS:
        if marker not in text:
            violations.append(f"{rel}: missing required marker '{marker}'")
    return violations


def check_all_agent_files(agents_dir: Path) -> list[str]:
    violations: list[str] = []
    agents = sorted(agents_dir.glob("*.md")) if agents_dir.is_dir() else []
    if not agents:
        violations.append(f"no agent files in {agents_dir}")
        return violations
    for path in agents:
        violations.extend(check_agent_file(path))
        if path.stem in CANVAS_AGENT_IDS:
            violations.extend(check_canvas_agent_file(path))
    return violations


def check_canvas_agent_file(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    rel = path.name
    violations: list[str] = []
    for marker in CANVAS_AGENT_MARKERS:
        if marker not in text:
            violations.append(f"{rel}: missing canvas marker '{marker}'")
    return violations


def _load_install_profile(root: Path) -> str | None:
    marker = root / ".local" / "generated-data" / "install-profile.json"
    if not marker.is_file():
        return None
    try:
        import json

        data = json.loads(marker.read_text(encoding="utf-8"))
        return str(data.get("profile") or "") or None
    except (json.JSONDecodeError, OSError):
        return None


def check_registry_parity(
    *,
    agents_dir: Path,
    registry_path: Path,
    root: Path | None = None,
) -> list[str]:
    """Registry agent ids must resolve to .cursor/agents/<id>.md files."""
    violations: list[str] = []
    file_ids = agent_file_ids(agents_dir)
    reg_ids = registry_agent_ids(registry_path)
    profile = _load_install_profile(root) if root is not None else None

    for agent_id in sorted(reg_ids):
        if agent_id in file_ids:
            continue
        if profile == "consumer_lite":
            continue
        violations.append(
            f"registry agent '{agent_id}' has no file .cursor/agents/{agent_id}.md"
        )

    return violations


def pipeline_names_from_exemplar(exemplar_path: Path) -> set[str]:
    if not exemplar_path.is_file():
        return set()
    data = yaml.safe_load(exemplar_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return set()
    pipelines = ((data.get("pr_collaboration") or {}).get("pipelines") or {})
    if not isinstance(pipelines, dict):
        return set()
    return set(pipelines.keys())


def resolve_pipeline_agent_id(
    agent_id: str,
    *,
    agents_dir: Path,
) -> bool:
    if agent_id in PR_SKILL_ALIASES:
        return True
    return (agents_dir / f"{agent_id}.md").is_file()


def check_pipeline_agent_ids(
    *,
    cfg: dict[str, Any],
    agents_dir: Path,
) -> list[str]:
    violations: list[str] = []
    pipelines = ((cfg.get("pr_collaboration") or {}).get("pipelines") or {})
    if not isinstance(pipelines, dict):
        return violations
    for pipe_name, spec in pipelines.items():
        if not isinstance(spec, dict):
            continue
        for agent_id in spec.get("agents") or []:
            if not isinstance(agent_id, str):
                continue
            aid = agent_id.strip()
            if aid and not resolve_pipeline_agent_id(aid, agents_dir=agents_dir):
                violations.append(
                    f"pipeline '{pipe_name}': unknown agent id '{aid}' "
                    "(expected agent file or review-pr|prepare-pr|merge-pr)"
                )
    return violations
