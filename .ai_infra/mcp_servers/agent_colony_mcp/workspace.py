"""
File: workspace.py
Path: .ai_infra/mcp_servers/agent_colony_mcp/workspace.py
Role: Resolve target repository root for MCP tools (install workspace).
Used By:
 - agent_colony_mcp/gates.py
 - agent_colony_mcp/runner.py
 - agent_colony_mcp/server.py
Depends On:
 - os
 - pathlib
Notes:
 - Set AGENT_COLONY_ROOT to override auto-detection.
"""

from __future__ import annotations

import os
from pathlib import Path

_PREPARE_REL = Path(".ai_infra") / "scripts" / "pr" / "prepare.py"
_LEGACY_PREPARE = Path("scripts") / "pr" / "prepare.py"


def workspace_root() -> Path:
    """Return the repo root containing .ai_infra/scripts/pr/prepare.py."""
    override = os.environ.get("AGENT_COLONY_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    start = Path.cwd().resolve()
    for candidate in (start, *start.parents):
        if (candidate / _PREPARE_REL).is_file():
            return candidate
        if (candidate / _LEGACY_PREPARE).is_file():
            return candidate
    return start
