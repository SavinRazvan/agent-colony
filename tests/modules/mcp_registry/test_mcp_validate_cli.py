"""
File: test_mcp_validate_cli.py
Path: tests/modules/mcp_registry/test_mcp_validate_cli.py
Role: Tests cursor-workflow mcp validate against registry and mcp.json keys.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/cli.py
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CLI_PATH = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow" / "cli.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("cursor_workflow_cli", CLI_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["cursor_workflow_cli"] = module
    spec.loader.exec_module(module)
    return module


def _seed_mcp_layout(root: Path) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    kit = json.loads((REPO_ROOT / ".cursor" / "mcp.json.kit.example").read_text(encoding="utf-8"))
    registry = yaml.safe_load(
        (REPO_ROOT / ".cursor" / "mcp.registry.yaml.example").read_text(encoding="utf-8")
    )
    user = {
        "mcpServers": {
            "my-custom-server": {"command": "echo", "args": ["ok"]},
        }
    }
    registry["servers"]["my-custom-server"] = {
        "tier": "external",
        "description": "test",
        "agents": ["implementer"],
        "tools_hint": [],
    }
    (cursor / "mcp.json.kit.example").write_text(json.dumps(kit, indent=2), encoding="utf-8")
    (cursor / "mcp.user.json").write_text(json.dumps(user, indent=2), encoding="utf-8")
    (cursor / "mcp.registry.yaml").write_text(yaml.dump(registry), encoding="utf-8")


def test_mcp_validate_passes_with_mock_external(tmp_path: Path) -> None:
    cli = _load_cli()
    _seed_mcp_layout(tmp_path)
    code = cli.main(["mcp", "validate", "--directory", str(tmp_path)])
    assert code == 0
    merged = json.loads((tmp_path / ".cursor" / "mcp.json").read_text(encoding="utf-8"))
    assert "my-custom-server" in merged["mcpServers"]


def test_mcp_validate_fails_when_registry_key_missing_from_mcp_json(tmp_path: Path) -> None:
    cli = _load_cli()
    _seed_mcp_layout(tmp_path)
    registry_path = tmp_path / ".cursor" / "mcp.registry.yaml"
    registry = yaml.safe_load(registry_path.read_text(encoding="utf-8"))
    registry["servers"]["orphan-server"] = {
        "tier": "external",
        "description": "not in mcp.json",
        "agents": ["implementer"],
        "tools_hint": [],
    }
    registry_path.write_text(yaml.dump(registry), encoding="utf-8")
    code = cli.main(["mcp", "validate", "--directory", str(tmp_path)])
    assert code == 1
