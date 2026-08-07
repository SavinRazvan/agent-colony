"""
File: cursor_host_paths.py
Path: .ai_infra/install/agent_colony/cursor_host_paths.py
Role: Resolve Cursor IDE managed paths for workspace (canvases, mcps, global plans).
Used By:
 - .ai_infra/install/agent_colony/mcp_manage.py
 - .ai_infra/install/agent_colony/canvas_manage.py
Depends On:
 - pathlib, re
Notes:
 - Best-effort fuzzy match for WSL/Linux workspace slugs. ADR-010.
"""

from __future__ import annotations

import re
from pathlib import Path


def cursor_projects_home() -> Path:
    return Path.home() / ".cursor" / "projects"


def cursor_plans_dir() -> Path:
    """Global Cursor plan-mode store (not project-scoped)."""
    return Path.home() / ".cursor" / "plans"


def cursor_project_dir(root: Path) -> Path | None:
    """Best-effort path to Cursor's per-project cache for this workspace."""
    home = cursor_projects_home()
    if not home.is_dir():
        return None
    slug = re.sub(r"[^A-Za-z0-9]+", "-", str(root).strip("/")).strip("-")
    candidates = [
        home / f"home-{slug}" if not str(root).startswith("/home/") else None,
        home / ("home-" + str(root).lstrip("/").replace("/", "-")),
    ]
    rel = str(root)
    if rel.startswith("/"):
        candidates.append(home / ("home-" + rel[1:].replace("/", "-")))
    for candidate in candidates:
        if candidate is not None and candidate.is_dir():
            return candidate
    name = root.name
    for path in sorted(home.iterdir()):
        if path.is_dir() and path.name.endswith(name):
            return path
    return None


def cursor_canvases_dir(root: Path) -> Path | None:
    project = cursor_project_dir(root)
    if project is None:
        return None
    canvases = project / "canvases"
    return canvases if canvases.is_dir() else None


def cursor_project_mcps_dir(root: Path) -> Path | None:
    project = cursor_project_dir(root)
    if project is None:
        return None
    mcps = project / "mcps"
    return mcps if mcps.is_dir() else None
