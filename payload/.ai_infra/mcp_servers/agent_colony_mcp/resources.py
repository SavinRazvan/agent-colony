"""
File: resources.py
Path: .ai_infra/mcp_servers/agent_colony_mcp/resources.py
Role: Resolve workflow:// MCP resource URIs to repo files (read-only).
Used By:
 - agent_colony_mcp/server.py
Depends On:
 - agent_colony_mcp/gates.py, workspace.py
Notes:
 - P1 resources per IMPLEMENTATION-STATUS.md. No second GATES list in inventory.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from agent_colony_mcp.gates import load_gates

_PR_PHASES = {
    "review": "review.md",
    "prep": "prep.md",
    "prepare": "prep.md",
    "merge": "merge.md",
}

_TRACKER_NAMES = frozenset(
    {
        "session-pointer",
        "plan",
        "work-tracker",
        "change-index",
        "test-plan",
        "test-index",
        "coverage-index",
        "architecture",
    }
)


def _read_text(path: Path) -> str:
    if not path.is_file():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def read_agent(root: Path, agent_id: str) -> str:
    return _read_text(root / ".cursor" / "agents" / f"{agent_id}.md")


def _find_skill_path(root: Path, skill_id: str) -> Path:
    candidates = [
        root / ".cursor" / "skills" / skill_id / "SKILL.md",
        root / ".agents" / "skills" / skill_id / "SKILL.md",
        root / ".agents" / "skills" / f"{skill_id}.md",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError(f"skill not found: {skill_id}")


def read_skill(root: Path, skill_id: str) -> str:
    return _read_text(_find_skill_path(root, skill_id))


def read_pr_artifact(root: Path, phase: str) -> str:
    filename = _PR_PHASES.get(phase.lower())
    if filename is None:
        allowed = ", ".join(sorted(_PR_PHASES))
        raise ValueError(f"Unknown PR phase '{phase}'. Allowed: {allowed}")
    path = root / ".local" / "workflow-artifacts" / "pr" / filename
    return _read_text(path)


def read_tracker(root: Path, name: str) -> str:
    if name not in _TRACKER_NAMES:
        allowed = ", ".join(sorted(_TRACKER_NAMES))
        raise ValueError(f"Unknown tracker '{name}'. Allowed: {allowed}")
    path = root / ".local" / "index-and-planning" / "current" / f"{name}.md"
    return _read_text(path)


def _list_agent_ids(root: Path) -> list[str]:
    agents_dir = root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return []
    return sorted(p.stem for p in agents_dir.glob("*.md"))


def _list_skill_ids(root: Path) -> list[str]:
    ids: set[str] = set()
    for base in (root / ".cursor" / "skills", root / ".agents" / "skills"):
        if not base.is_dir():
            continue
        for skill_md in base.rglob("SKILL.md"):
            if skill_md.parent != base:
                ids.add(skill_md.parent.name)
        for md in base.glob("*.md"):
            ids.add(md.stem)
    return sorted(ids)


def build_inventory(root: Path) -> str:
    """Minimal live inventory JSON — not a duplicate of prepare.py GATES commands."""
    payload = {
        "schema": "agent-colony-mcp-inventory/v1",
        "agents": _list_agent_ids(root),
        "skills": _list_skill_ids(root),
        "gate_count": len(load_gates(root)),
        "workspace_root": str(root),
    }
    return json.dumps(payload, indent=2)


def read_project_config(root: Path) -> str:
    for candidate in (root / "project.config.yaml", root / ".ai_infra" / "project.config.yaml.example"):
        if candidate.is_file():
            return candidate.read_text(encoding="utf-8")
    return "project.config.yaml not found; copy .ai_infra/project.config.yaml.example"


def _load_registry_yaml(root: Path) -> dict:
    for candidate in (
        root / ".cursor" / "mcp.registry.yaml",
        root / ".cursor" / "mcp.registry.yaml.example",
    ):
        if candidate.is_file():
            data = yaml.safe_load(candidate.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    raise FileNotFoundError("mcp.registry.yaml not found")


def read_mcp_registry(root: Path) -> str:
    return json.dumps(_load_registry_yaml(root), indent=2)


def read_mcp_connection_guide(root: Path) -> str:
    doc = root / ".ai_infra" / "docs" / "operations" / "connect-external-mcp.md"
    if not doc.is_file():
        raise FileNotFoundError(str(doc))
    return doc.read_text(encoding="utf-8")
