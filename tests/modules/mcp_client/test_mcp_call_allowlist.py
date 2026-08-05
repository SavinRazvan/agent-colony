"""
File: test_mcp_call_allowlist.py
Path: tests/modules/mcp_client/test_mcp_call_allowlist.py
Role: Registry allowlist + live stdio smoke against workflow-kit when available.
Used By:
 - pytest
Depends On:
 - mcp_client, mcp_manage, cli
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CW = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"


def _load(name: str, path: Path):
    if str(CW) not in sys.path:
        sys.path.insert(0, str(CW))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _seed(root: Path) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    kit = json.loads((REPO_ROOT / ".cursor" / "mcp.json.kit.example").read_text(encoding="utf-8"))
    # Point command at repo venv + servers for live smoke when root==REPO
    (cursor / "mcp.json.kit.example").write_text(json.dumps(kit, indent=2), encoding="utf-8")
    registry = {
        "version": 1,
        "servers": {
            "workflow-kit": {
                "tier": "kit",
                "description": "kit",
                "agents": ["implementer"],
                "tools_hint": [],
            }
        },
    }
    (cursor / "mcp.registry.yaml").write_text(yaml.dump(registry), encoding="utf-8")


def test_assert_server_rejects_unknown(tmp_path: Path) -> None:
    _seed(tmp_path)
    manage = _load("mcp_manage_al", CW / "mcp_manage.py")
    manage.write_merged_mcp(tmp_path)
    err = manage.assert_server_allowed(tmp_path, "nope")
    assert err is not None
    err2 = manage.assert_server_allowed(tmp_path, "workflow-kit", agent="researcher")
    assert err2 is not None
    err3 = manage.assert_server_allowed(tmp_path, "workflow-kit", agent="implementer")
    assert err3 is None


def test_parse_args_json() -> None:
    client = _load("mcp_client_al", CW / "mcp_client.py")
    assert client.parse_args_json('{"a":1}') == {"a": 1}
    with pytest.raises(client.McpClientError):
        client.parse_args_json("[1]")


@pytest.mark.skipif(
    not (REPO_ROOT / ".venv" / "bin" / "python").is_file(),
    reason="venv required for live stdio smoke",
)
def test_list_tools_workflow_kit_live() -> None:
    """Live stdio against this kit's workflow-kit server."""
    manage = _load("mcp_manage_live", CW / "mcp_manage.py")
    client = _load("mcp_client_live", CW / "mcp_client.py")
    # Ensure registry exists for allowlist — use example-only path: no live registry
    # means allowlist skips registry check and only requires merged mcp.json
    tools = client.list_tools(REPO_ROOT, "workflow-kit")
    names = {t["name"] for t in tools}
    assert "workflow_gate_count" in names
    assert len(tools) >= 5


@pytest.mark.skipif(
    not (REPO_ROOT / ".venv" / "bin" / "python").is_file(),
    reason="venv required",
)
def test_smoke_cli_workflow_kit() -> None:
    cli = _load("cli_smoke", CW / "cli.py")
    code = cli.main(["mcp", "smoke", "--directory", str(REPO_ROOT), "--server", "workflow-kit"])
    assert code == 0
    arts = list((REPO_ROOT / ".local" / "workflow-artifacts" / "mcp").glob("smoke-*.md"))
    assert arts
