"""
File: mcp_client.py
Path: .ai_infra/install/cursor_workflow/mcp_client.py
Role: Pattern A MCP client — stdio + URL transports for list-tools/call/smoke.
Used By:
 - .ai_infra/install/cursor_workflow/mcp_cli.py
Depends On:
 - mcp (SDK), mcp_manage, mcp_secrets
Notes:
 - ADR-009. Does not print secrets.
"""

from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import mcp_manage
import mcp_secrets

EXIT_OK = mcp_manage.EXIT_OK
EXIT_USAGE = mcp_manage.EXIT_USAGE
EXIT_GH = mcp_manage.EXIT_GH
EXIT_NOT_FOUND = mcp_manage.EXIT_NOT_FOUND
EXIT_VALIDATION = mcp_manage.EXIT_VALIDATION


class McpClientError(Exception):
    def __init__(self, message: str, *, code: int = EXIT_GH) -> None:
        super().__init__(message)
        self.code = code


def _resolve_spec(root: Path, server: str) -> dict[str, Any]:
    err = mcp_manage.assert_server_allowed(root, server)
    if err:
        raise McpClientError(err, code=EXIT_VALIDATION)
    merged = mcp_manage.load_merged_servers(root)
    raw = merged[server]
    return mcp_manage.expand_server_env(raw, root)


@asynccontextmanager
async def _open_session(
    root: Path,
    server: str,
    *,
    agent: str | None = None,
) -> AsyncIterator[Any]:
    err = mcp_manage.assert_server_allowed(root, server, agent=agent)
    if err:
        raise McpClientError(err, code=EXIT_VALIDATION)

    from mcp import ClientSession

    spec = _resolve_spec(root, server)
    secret = mcp_secrets.secrets_for_server(root, server)

    if "url" in spec and isinstance(spec["url"], str):
        url = spec["url"]
        headers = mcp_secrets.http_headers_from_secrets(secret)
        try:
            from mcp.client.streamable_http import streamable_http_client
            from mcp.client.streamable_http import create_mcp_http_client
        except ImportError as exc:  # pragma: no cover
            raise McpClientError(f"streamable HTTP transport unavailable: {exc}") from exc

        if headers:
            async with create_mcp_http_client(headers=headers) as http_client:
                async with streamable_http_client(url, http_client=http_client) as streams:
                    read, write = streams[0], streams[1]
                    async with ClientSession(read, write) as session:
                        await session.initialize()
                        yield session
        else:
            async with streamable_http_client(url) as streams:
                read, write = streams[0], streams[1]
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session
        return

    command = spec.get("command")
    if not isinstance(command, str) or not command:
        raise McpClientError(
            f"server '{server}' needs 'command' (stdio) or 'url' (HTTP)",
            code=EXIT_VALIDATION,
        )

    from mcp.client.stdio import StdioServerParameters, stdio_client

    args = spec.get("args") or []
    if not isinstance(args, list):
        raise McpClientError(f"server '{server}' args must be a list", code=EXIT_VALIDATION)
    env_spec = spec.get("env") if isinstance(spec.get("env"), dict) else {}
    env = {**os.environ, **{str(k): str(v) for k, v in env_spec.items()}}
    env.update(mcp_secrets.env_from_secrets(secret))
    params = StdioServerParameters(
        command=command,
        args=[str(a) for a in args],
        env=env,
        cwd=str(root),
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def _list_tools_async(root: Path, server: str, *, agent: str | None) -> list[dict[str, Any]]:
    async with _open_session(root, server, agent=agent) as session:
        result = await session.list_tools()
        out: list[dict[str, Any]] = []
        for tool in result.tools:
            out.append(
                {
                    "name": tool.name,
                    "description": getattr(tool, "description", None) or "",
                }
            )
        return out


async def _call_tool_async(
    root: Path,
    server: str,
    tool: str,
    arguments: dict[str, Any],
    *,
    agent: str | None,
) -> Any:
    async with _open_session(root, server, agent=agent) as session:
        result = await session.call_tool(tool, arguments=arguments)
        # Prefer structured content when present
        if getattr(result, "structuredContent", None) is not None:
            return result.structuredContent
        texts: list[str] = []
        for block in getattr(result, "content", None) or []:
            text = getattr(block, "text", None)
            if text is not None:
                texts.append(str(text))
            else:
                texts.append(str(block))
        if len(texts) == 1:
            return texts[0]
        return texts


def list_tools(root: Path, server: str, *, agent: str | None = None) -> list[dict[str, Any]]:
    try:
        return asyncio.run(_list_tools_async(root, server, agent=agent))
    except McpClientError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise McpClientError(str(exc), code=EXIT_GH) from exc


def call_tool(
    root: Path,
    server: str,
    tool: str,
    arguments: dict[str, Any] | None = None,
    *,
    agent: str | None = None,
) -> Any:
    try:
        return asyncio.run(
            _call_tool_async(root, server, tool, arguments or {}, agent=agent)
        )
    except McpClientError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise McpClientError(str(exc), code=EXIT_GH) from exc


def smoke_server(root: Path, server: str, *, agent: str | None = None) -> dict[str, Any]:
    tools = list_tools(root, server, agent=agent)
    return {
        "server": server,
        "ok": True,
        "tool_count": len(tools),
        "tools": [t["name"] for t in tools],
    }


def parse_args_json(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise McpClientError(f"invalid --args-json: {exc}", code=EXIT_USAGE) from exc
    if not isinstance(data, dict):
        raise McpClientError("--args-json must be a JSON object", code=EXIT_USAGE)
    return data
