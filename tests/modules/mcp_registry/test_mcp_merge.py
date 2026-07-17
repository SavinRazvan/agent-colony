"""
File: test_mcp_merge.py
Path: tests/modules/mcp_registry/test_mcp_merge.py
Role: Tests kit + user MCP JSON merge preserves user keys.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/mcp_manage.py
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MCP_MANAGE = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow" / "mcp_manage.py"


def _load_mcp_manage():
    spec = importlib.util.spec_from_file_location("mcp_manage", MCP_MANAGE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["mcp_manage"] = module
    spec.loader.exec_module(module)
    return module


def test_merge_preserves_user_servers() -> None:
    mod = _load_mcp_manage()
    kit = {"mcpServers": {"workflow-kit": {"command": "python"}}}
    user = {"mcpServers": {"slack": {"command": "npx"}}}
    merged = mod.merge_mcp_configs(kit, user)
    assert "workflow-kit" in merged["mcpServers"]
    assert "slack" in merged["mcpServers"]


def test_write_merged_mcp_from_examples(tmp_path: Path) -> None:
    mod = _load_mcp_manage()
    cursor = tmp_path / ".cursor"
    cursor.mkdir(parents=True)
    shutil_copy = __import__("shutil").copy2
    shutil_copy(REPO_ROOT / ".cursor" / "mcp.json.kit.example", cursor / "mcp.json.kit.example")
    dest = mod.write_merged_mcp(tmp_path)
    assert dest.is_file()
    text = dest.read_text(encoding="utf-8")
    assert "workflow-kit" in text
