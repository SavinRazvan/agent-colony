"""
File: gates.py
Path: .ai_infra/mcp_servers/workflow_mcp/gates.py
Role: Load GATES from `.ai_infra/scripts/pr/prepare.py` — never duplicate gate lists in MCP.
Used By:
 - workflow_mcp/server.py
Depends On:
 - workflow_mcp/workspace.py
Notes:
 - Single source of truth remains prepare.py GATES.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

from workflow_mcp.workspace import workspace_root


def _load_prepare_module(root: Path) -> ModuleType:
    prepare_path = root / ".ai_infra" / "scripts" / "pr" / "prepare.py"
    if not prepare_path.is_file():
        prepare_path = root / "scripts" / "pr" / "prepare.py"
    if not prepare_path.is_file():
        raise FileNotFoundError(f"prepare.py not found under {root}")
    spec = importlib.util.spec_from_file_location("workflow_kit_prepare", prepare_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load prepare module from {prepare_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_gates(root: Path | None = None) -> list[list[str]]:
    """Return resolved prepare gates for the workspace (kit-dev append when applicable)."""
    repo = root or workspace_root()
    module = _load_prepare_module(repo)
    resolve = getattr(module, "resolve_gates", None)
    if callable(resolve):
        return [list(cmd) for cmd in resolve(repo)]
    gates = getattr(module, "GATES", None)
    if not isinstance(gates, list):
        raise ValueError("prepare.py GATES must be a list")
    return [list(cmd) for cmd in gates]
