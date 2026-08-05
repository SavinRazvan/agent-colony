"""
File: test_mcp_secrets_edges.py
Path: tests/modules/mcp_client/test_mcp_secrets_edges.py
Role: Edge coverage for mcp_secrets miss lines.
Used By:
 - pytest
Depends On:
 - mcp_secrets
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import mcp_secrets  # noqa: E402


def test_load_secrets_invalid_root(tmp_path: Path) -> None:
    path = mcp_secrets.secrets_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("- list\n", encoding="utf-8")
    with pytest.raises(ValueError, match="invalid secrets file"):
        mcp_secrets.load_secrets(tmp_path)


def test_load_secrets_missing_servers_key(tmp_path: Path) -> None:
    path = mcp_secrets.secrets_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("version: 1\n", encoding="utf-8")
    data = mcp_secrets.load_secrets(tmp_path)
    assert data["servers"] == {}


def test_load_secrets_servers_not_dict(tmp_path: Path) -> None:
    path = mcp_secrets.secrets_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("servers: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a mapping"):
        mcp_secrets.load_secrets(tmp_path)


def test_set_server_secret_servers_not_dict(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mcp_secrets, "load_secrets", lambda _r: {"servers": []})
    with pytest.raises(ValueError, match="must be a mapping"):
        mcp_secrets.set_server_secret(tmp_path, "s", token="t")


def test_set_server_secret_with_env_and_merge(tmp_path: Path) -> None:
    mcp_secrets.set_server_secret(tmp_path, "api", token="t1")
    mcp_secrets.set_server_secret(
        tmp_path, "api", header_name="X-Api-Key", env={"K": "V"}
    )
    entry = mcp_secrets.secrets_for_server(tmp_path, "api")
    assert entry["token"] == "t1"
    assert entry["header"] == "X-Api-Key"
    assert entry["env"]["K"] == "V"


def test_secrets_for_server_invalid_servers(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(mcp_secrets, "load_secrets", lambda _r: {"servers": "bad"})
    assert mcp_secrets.secrets_for_server(tmp_path, "x") == {}


def test_http_headers_custom_and_bearer_and_extra() -> None:
    h1 = mcp_secrets.http_headers_from_secrets(
        {"token": "Bearer xyz", "header": "Authorization"}
    )
    assert h1["Authorization"] == "Bearer xyz"
    h2 = mcp_secrets.http_headers_from_secrets({"token": "raw", "header": "X-Auth"})
    assert h2["X-Auth"] == "raw"
    h3 = mcp_secrets.http_headers_from_secrets(
        {"token": "t", "headers": {"X-Custom": "v", 1: "skip", "bad": 2}}
    )
    assert h3["Authorization"].startswith("Bearer ")
    assert h3["X-Custom"] == "v"
    assert "bad" not in h3


def test_env_from_secrets() -> None:
    assert mcp_secrets.env_from_secrets({}) == {}
    assert mcp_secrets.env_from_secrets({"env": "nope"}) == {}
    assert mcp_secrets.env_from_secrets({"env": {"A": 1}}) == {"A": "1"}
