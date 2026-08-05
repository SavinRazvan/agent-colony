"""
File: test_mcp_client_http.py
Path: tests/modules/mcp_client/test_mcp_client_http.py
Role: HTTP transport + call_tool result shaping + error wrapping for mcp_client.
Used By:
 - pytest
Depends On:
 - mcp_client, mcp_manage, mcp_secrets
"""

from __future__ import annotations

import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import mcp_client  # noqa: E402
import mcp_manage  # noqa: E402
import mcp_secrets  # noqa: E402


def _seed(root: Path, server_spec: dict[str, Any], *, agents: list[str] | None = None) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"svc": server_spec}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump(
            {"servers": {"svc": {"agents": agents or ["implementer"], "tier": "kit"}}}
        ),
        encoding="utf-8",
    )
    mcp_manage.write_merged_mcp(root)


def test_parse_args_json_none_and_invalid() -> None:
    assert mcp_client.parse_args_json(None) == {}
    assert mcp_client.parse_args_json("") == {}
    with pytest.raises(mcp_client.McpClientError) as exc:
        mcp_client.parse_args_json("{bad")
    assert exc.value.code == mcp_client.EXIT_USAGE


def test_resolve_spec_rejects_unknown(tmp_path: Path) -> None:
    _seed(tmp_path, {"command": "echo"})
    with pytest.raises(mcp_client.McpClientError) as exc:
        mcp_client._resolve_spec(tmp_path, "ghost")
    assert exc.value.code == mcp_client.EXIT_VALIDATION


def test_open_session_agent_not_allowed(tmp_path: Path) -> None:
    _seed(tmp_path, {"command": "echo"}, agents=["implementer"])
    with pytest.raises(mcp_client.McpClientError, match="not mapped"):
        mcp_client.list_tools(tmp_path, "svc", agent="researcher")


def test_open_session_needs_command_or_url(tmp_path: Path) -> None:
    _seed(tmp_path, {})
    with pytest.raises(mcp_client.McpClientError, match="needs 'command'"):
        mcp_client.list_tools(tmp_path, "svc")


def test_open_session_args_must_be_list(tmp_path: Path) -> None:
    _seed(tmp_path, {"command": "echo", "args": "nope"})
    with pytest.raises(mcp_client.McpClientError, match="args must be a list"):
        mcp_client.list_tools(tmp_path, "svc")


def test_list_tools_wraps_unexpected(tmp_path: Path, monkeypatch) -> None:
    async def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(mcp_client, "_list_tools_async", boom)
    with pytest.raises(mcp_client.McpClientError) as exc:
        mcp_client.list_tools(tmp_path, "svc")
    assert exc.value.code == mcp_client.EXIT_GH


def test_call_tool_wraps_unexpected(tmp_path: Path, monkeypatch) -> None:
    async def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(mcp_client, "_call_tool_async", boom)
    with pytest.raises(mcp_client.McpClientError) as exc:
        mcp_client.call_tool(tmp_path, "svc", "t", {})
    assert exc.value.code == mcp_client.EXIT_GH


def test_call_tool_reraises_mcp_client_error(tmp_path: Path, monkeypatch) -> None:
    async def boom(*a, **k):
        raise mcp_client.McpClientError("nope", code=5)

    monkeypatch.setattr(mcp_client, "_call_tool_async", boom)
    with pytest.raises(mcp_client.McpClientError) as exc:
        mcp_client.call_tool(tmp_path, "svc", "t", {})
    assert exc.value.code == 5
    assert str(exc.value) == "nope"


def test_call_tool_result_shaping(tmp_path: Path, monkeypatch) -> None:
    class Session:
        def __init__(self, result):
            self._result = result

        async def call_tool(self, tool, arguments=None):
            return self._result

    @asynccontextmanager
    async def fake_open(root, server, *, agent=None):
        yield Session(SimpleNamespace(structuredContent={"a": 1}, content=None))

    monkeypatch.setattr(mcp_client, "_open_session", fake_open)
    assert mcp_client.call_tool(tmp_path, "svc", "t") == {"a": 1}

    @asynccontextmanager
    async def fake_open_text(root, server, *, agent=None):
        yield Session(
            SimpleNamespace(
                structuredContent=None,
                content=[SimpleNamespace(text="only")],
            )
        )

    monkeypatch.setattr(mcp_client, "_open_session", fake_open_text)
    assert mcp_client.call_tool(tmp_path, "svc", "t") == "only"

    @asynccontextmanager
    async def fake_open_multi(root, server, *, agent=None):
        yield Session(
            SimpleNamespace(
                structuredContent=None,
                content=[SimpleNamespace(text="a"), SimpleNamespace(text="b"), object()],
            )
        )

    monkeypatch.setattr(mcp_client, "_open_session", fake_open_multi)
    result = mcp_client.call_tool(tmp_path, "svc", "t")
    assert result[0] == "a" and result[1] == "b"
    assert len(result) == 3


def test_http_transport_with_and_without_headers(tmp_path: Path, monkeypatch) -> None:
    _seed(tmp_path, {"url": "https://example.test/mcp"})
    mcp_secrets.set_server_secret(tmp_path, "svc", token="tok")

    calls: list[str] = []

    class FakeSession:
        async def initialize(self):
            return None

        async def list_tools(self):
            return SimpleNamespace(tools=[SimpleNamespace(name="ht", description="d")])

    @asynccontextmanager
    async def fake_http_client(*, headers=None):
        calls.append(f"http_client:{bool(headers)}")
        yield object()

    @asynccontextmanager
    async def fake_streamable(url, http_client=None):
        calls.append(f"streamable:{url}:{http_client is not None}")
        yield (object(), object())

    @asynccontextmanager
    async def fake_client_session(read, write):
        yield FakeSession()

    monkeypatch.setitem(
        sys.modules,
        "mcp.client.streamable_http",
        SimpleNamespace(
            streamable_http_client=fake_streamable,
            create_mcp_http_client=fake_http_client,
        ),
    )
    # Also patch imports used inside _open_session
    import mcp.client.streamable_http as sh  # noqa: F401

    monkeypatch.setattr(
        "mcp.client.streamable_http.streamable_http_client", fake_streamable, raising=False
    )
    monkeypatch.setattr(
        "mcp.client.streamable_http.create_mcp_http_client", fake_http_client, raising=False
    )
    monkeypatch.setattr("mcp.ClientSession", fake_client_session)

    tools = mcp_client.list_tools(tmp_path, "svc")
    assert tools[0]["name"] == "ht"
    assert any(c.startswith("http_client:True") for c in calls)

    # without headers
    secrets_path = tmp_path / ".local" / "user_settings" / "mcp.secrets.yaml"
    if secrets_path.is_file():
        secrets_path.unlink()
    calls.clear()
    tools = mcp_client.list_tools(tmp_path, "svc")
    assert tools[0]["name"] == "ht"
    assert any("streamable:" in c and ":False" in c for c in calls)


def test_smoke_server(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        mcp_client,
        "list_tools",
        lambda *a, **k: [{"name": "a", "description": ""}],
    )
    out = mcp_client.smoke_server(tmp_path, "svc")
    assert out["tool_count"] == 1
    assert out["tools"] == ["a"]
