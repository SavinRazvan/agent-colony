"""
File: test_mcp_secrets.py
Path: tests/modules/mcp_client/test_mcp_secrets.py
Role: Unit tests for mcp.secrets.yaml helpers and auth CLI.
Used By:
 - pytest
Depends On:
 - mcp_secrets, cli
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
CW = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"


def _load(name: str, path: Path):
    if str(CW) not in sys.path:
        sys.path.insert(0, str(CW))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_set_and_load_secrets(tmp_path: Path) -> None:
    secrets = _load("mcp_secrets_t", CW / "mcp_secrets.py")
    secrets.set_server_secret(tmp_path, "my-api", token="sekrit", header_name="Authorization")
    entry = secrets.secrets_for_server(tmp_path, "my-api")
    assert entry["token"] == "sekrit"
    headers = secrets.http_headers_from_secrets(entry)
    assert headers["Authorization"].startswith("Bearer ")


def test_auth_cli(tmp_path: Path, monkeypatch) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    kit = json.loads((REPO_ROOT / ".cursor" / "mcp.json.kit.example").read_text(encoding="utf-8"))
    (cursor / "mcp.json.kit.example").write_text(json.dumps(kit), encoding="utf-8")
    monkeypatch.setenv("MCP_TEST_TOKEN", "abc123")
    cli = _load("cli_auth", CW / "cli.py")
    code = cli.main(
        [
            "mcp",
            "auth",
            "--directory",
            str(tmp_path),
            "--server",
            "my-api",
            "--token-env",
            "MCP_TEST_TOKEN",
        ]
    )
    assert code == 0
    text = (tmp_path / ".local" / "user_settings" / "mcp.secrets.yaml").read_text(encoding="utf-8")
    assert "abc123" in text
    assert "my-api" in text
