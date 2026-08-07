"""
File: test_mcp_manage_edges.py
Path: tests/modules/mcp_registry/test_mcp_manage_edges.py
Role: Edge coverage for mcp_manage doctor/load helpers (ADR-009).
Used By:
 - pytest
Depends On:
 - mcp_manage
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import mcp_manage  # noqa: E402


def _seed_kit(root: Path) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"kit-server": {"command": "echo"}}}),
        encoding="utf-8",
    )


def test_validate_registry_strict_external_and_bad_spec(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    mcp_manage.write_merged_mcp(tmp_path)
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "kit-server": {"agents": [], "tier": "kit"},
                    "bad": [],
                    "ext-svc": {"agents": [], "tier": "external"},
                }
            }
        ),
        encoding="utf-8",
    )
    errors = mcp_manage.validate_registry(tmp_path, strict=True)
    assert any("ext-svc" in e for e in errors)


def test_load_merged_servers_write_and_auto(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    servers = mcp_manage.load_merged_servers(tmp_path, write=True)
    assert "kit-server" in servers
    mcp_path = tmp_path / ".cursor" / "mcp.json"
    assert mcp_path.is_file()
    mcp_path.unlink()
    servers2 = mcp_manage.load_merged_servers(tmp_path)
    assert "kit-server" in servers2


def test_load_merged_servers_invalid_kit_servers(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    (tmp_path / ".cursor" / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": []}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="mcpServers must be an object"):
        mcp_manage.load_merged_servers(tmp_path)


def test_registry_path_used_live_and_none(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    assert mcp_manage.registry_path_used(tmp_path) is None
    (cursor / "mcp.registry.yaml").write_text("servers: {}\n", encoding="utf-8")
    assert mcp_manage.registry_path_used(tmp_path) == cursor / "mcp.registry.yaml"


def test_registry_servers_missing(tmp_path: Path) -> None:
    assert mcp_manage.registry_servers(tmp_path) == {}


def test_servers_for_agent_none_and_skips_bad(tmp_path: Path) -> None:
    assert mcp_manage.servers_for_agent(tmp_path, None) is None
    _seed_kit(tmp_path)
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {
                "servers": {
                    "good": {"agents": ["implementer"]},
                    "bad": "x",
                }
            }
        ),
        encoding="utf-8",
    )
    allowed = mcp_manage.servers_for_agent(tmp_path, "implementer")
    assert allowed == {"good"}


def test_assert_server_in_registry_not_in_merged(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    mcp_manage.write_merged_mcp(tmp_path)
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"ghost": {"agents": []}, "kit-server": {"agents": []}}}),
        encoding="utf-8",
    )
    # ghost in registry but not mcp.json
    err = mcp_manage.assert_server_allowed(tmp_path, "ghost")
    assert err is not None
    assert "not in merged" in err or "not in registry" in err or "ghost" in err


def test_expand_server_env_passthrough(tmp_path: Path) -> None:
    out = mcp_manage.expand_server_env(
        {"command": "${workspaceFolder}/bin", "timeout": 30, "args": ["${workspaceFolder}"]},
        tmp_path,
    )
    assert str(tmp_path) in out["command"]
    assert out["timeout"] == 30
    assert out["args"][0] == str(tmp_path)


def test_list_cursor_host_servers(tmp_path: Path) -> None:
    assert mcp_manage.list_cursor_host_servers(None) == []
    mcps = tmp_path / "mcps"
    mcps.mkdir()
    (mcps / "alpha").mkdir()
    (mcps / ".hidden").mkdir()
    (mcps / "file.txt").write_text("x", encoding="utf-8")
    assert mcp_manage.list_cursor_host_servers(mcps) == ["alpha"]


def test_check_workflow_mcp_import_missing(tmp_path: Path) -> None:
    result = mcp_manage.check_workflow_mcp_import(tmp_path)
    assert result["import_ok"] is False
    assert result["error"]


def test_check_workflow_mcp_import_success_and_fail(tmp_path: Path, monkeypatch) -> None:
    venv_py = tmp_path / ".venv" / "bin" / "python"
    venv_py.parent.mkdir(parents=True)
    venv_py.write_text("#!/bin/sh\n", encoding="utf-8")
    venv_py.chmod(0o755)
    (tmp_path / ".ai_infra" / "mcp_servers").mkdir(parents=True)

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="/mod.py\n", stderr=""),
    )
    ok = mcp_manage.check_workflow_mcp_import(tmp_path)
    assert ok["import_ok"] is True
    assert ok["module_file"] == "/mod.py"

    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="", stderr="No module"),
    )
    fail = mcp_manage.check_workflow_mcp_import(tmp_path)
    assert fail["import_ok"] is False
    assert "No module" in fail["error"]
