"""
File: test_mcp_cli_handlers.py
Path: tests/modules/mcp_client/test_mcp_cli_handlers.py
Role: Handler coverage for mcp_cli Pattern A commands (ADR-009).
Used By:
 - pytest
Depends On:
 - mcp_cli, mcp_client, mcp_manage, mcp_secrets
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(PKG) not in sys.path:
    sys.path.insert(0, str(PKG))

import mcp_cli  # noqa: E402
import mcp_client  # noqa: E402
import mcp_manage  # noqa: E402
import mcp_secrets  # noqa: E402


def _seed_kit(root: Path, *, with_registry: bool = True) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True)
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"kit-server": {"command": "echo"}}}),
        encoding="utf-8",
    )
    if with_registry:
        (cursor / "mcp.registry.yaml").write_text(
            yaml.safe_dump(
                {
                    "servers": {
                        "kit-server": {"agents": ["implementer"], "tier": "kit"},
                        "bad": "not-a-dict",
                    }
                }
            ),
            encoding="utf-8",
        )


def test_build_doctor_report_merge_error(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    (tmp_path / ".cursor" / "mcp.json").write_text("{not-json", encoding="utf-8")
    report = mcp_cli.build_doctor_report(tmp_path)
    assert report["merge_error"]
    assert report["merged_servers"] == []


def test_build_doctor_report_skips_non_dict_spec(tmp_path: Path) -> None:
    _seed_kit(tmp_path)
    mcp_manage.write_merged_mcp(tmp_path)
    report = mcp_cli.build_doctor_report(tmp_path)
    assert "implementer" in report["agent_mappings"]
    assert "kit-server" in report["agent_mappings"]["implementer"]
    assert "bad" not in report["registry_servers"] or "bad" in report["registry_servers"]


def test_format_doctor_markdown_merge_error_and_empty_mappings() -> None:
    report = {
        "root": "/tmp/x",
        "user_fragment_present": False,
        "registry_path": None,
        "registry_live": False,
        "merged_servers": [],
        "registry_servers": [],
        "cursor_mcps_dir": None,
        "cursor_host_loaded": [],
        "configured_not_host_loaded": [],
        "host_loaded_not_configured": [],
        "workflow_mcp": {"venv_python": None, "import_ok": False, "error": "missing"},
        "merge_error": "boom",
        "agent_mappings": {},
    }
    body = mcp_cli.format_doctor_markdown(report)
    assert "**merge error:** boom" in body
    assert "(none)" in body
    assert "error: missing" in body


def test_format_doctor_markdown_with_mappings() -> None:
    report = {
        "root": "/tmp/x",
        "user_fragment_present": True,
        "registry_path": "/r.yaml",
        "registry_live": True,
        "merged_servers": ["a"],
        "registry_servers": ["a"],
        "cursor_mcps_dir": "/mcps",
        "cursor_host_loaded": ["a"],
        "configured_not_host_loaded": [],
        "host_loaded_not_configured": [],
        "workflow_mcp": {"venv_python": "/py", "import_ok": True},
        "agent_mappings": {"implementer": ["a"]},
    }
    body = mcp_cli.format_doctor_markdown(report)
    assert "`implementer`: a" in body


def test_cmd_mcp_doctor_warns_on_merge_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_manage, "write_merged_mcp", lambda _r: (_ for _ in ()).throw(FileNotFoundError("no kit"))
    )
    args = argparse.Namespace(directory=tmp_path)
    assert mcp_cli.cmd_mcp_doctor(args) == 0
    err = capsys.readouterr().err
    assert "WARN" in err
    assert "merge failed" in err


def test_cmd_mcp_list_tools_success(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_client,
        "list_tools",
        lambda root, server, agent=None: [{"name": "t1", "description": "line1\nline2"}],
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_list_tools(args) == 0
    assert "t1\tline1 line2" in capsys.readouterr().out


def test_cmd_mcp_list_tools_client_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_client,
        "list_tools",
        lambda *a, **k: (_ for _ in ()).throw(mcp_client.McpClientError("nope", code=3)),
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_list_tools(args) == 3


def test_cmd_mcp_list_tools_validation_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_manage, "write_merged_mcp", lambda _r: (_ for _ in ()).throw(ValueError("bad"))
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_list_tools(args) == mcp_manage.EXIT_VALIDATION


def test_cmd_mcp_call_json_and_string(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(mcp_client, "call_tool", lambda *a, **k: {"ok": True})
    args = argparse.Namespace(
        directory=tmp_path, server="kit-server", tool="t", args_json='{"a":1}', agent=None
    )
    assert mcp_cli.cmd_mcp_call(args) == 0
    assert '"ok"' in capsys.readouterr().out

    monkeypatch.setattr(mcp_client, "call_tool", lambda *a, **k: "plain")
    assert mcp_cli.cmd_mcp_call(args) == 0
    assert "plain" in capsys.readouterr().out


def test_cmd_mcp_call_errors(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_client,
        "call_tool",
        lambda *a, **k: (_ for _ in ()).throw(mcp_client.McpClientError("x", code=4)),
    )
    args = argparse.Namespace(
        directory=tmp_path, server="kit-server", tool="t", args_json=None, agent=None
    )
    assert mcp_cli.cmd_mcp_call(args) == 4

    monkeypatch.setattr(
        mcp_manage, "write_merged_mcp", lambda _r: (_ for _ in ()).throw(FileNotFoundError("x"))
    )
    assert mcp_cli.cmd_mcp_call(args) == mcp_manage.EXIT_VALIDATION


def test_cmd_mcp_auth_empty_token_env(tmp_path: Path, monkeypatch, capsys) -> None:
    args = argparse.Namespace(
        directory=tmp_path,
        server="s",
        token=None,
        token_env="EMPTY_TOKEN_XYZ",
        header=None,
        env_pair=[],
    )
    monkeypatch.delenv("EMPTY_TOKEN_XYZ", raising=False)
    assert mcp_cli.cmd_mcp_auth(args) == mcp_manage.EXIT_USAGE
    assert "empty" in capsys.readouterr().err


def test_cmd_mcp_auth_no_credentials(tmp_path: Path, capsys) -> None:
    args = argparse.Namespace(
        directory=tmp_path, server="s", token=None, token_env=None, header=None, env_pair=[]
    )
    assert mcp_cli.cmd_mcp_auth(args) == mcp_manage.EXIT_USAGE


def test_cmd_mcp_auth_bad_env_pair(tmp_path: Path, capsys) -> None:
    args = argparse.Namespace(
        directory=tmp_path,
        server="s",
        token="tok",
        token_env=None,
        header=None,
        env_pair=["NOEQUALS"],
    )
    assert mcp_cli.cmd_mcp_auth(args) == mcp_manage.EXIT_USAGE
    assert "bad --env" in capsys.readouterr().err


def test_cmd_mcp_auth_write_failure(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        mcp_secrets,
        "set_server_secret",
        lambda *a, **k: (_ for _ in ()).throw(OSError("disk")),
    )
    args = argparse.Namespace(
        directory=tmp_path,
        server="s",
        token="tok",
        token_env=None,
        header=None,
        env_pair=["A=B"],
    )
    assert mcp_cli.cmd_mcp_auth(args) == mcp_manage.EXIT_VALIDATION


def test_cmd_mcp_auth_success_with_env(tmp_path: Path, capsys) -> None:
    args = argparse.Namespace(
        directory=tmp_path,
        server="s",
        token="tok",
        token_env=None,
        header="X-Api-Key",
        env_pair=["FOO=bar"],
    )
    assert mcp_cli.cmd_mcp_auth(args) == 0
    entry = mcp_secrets.secrets_for_server(tmp_path, "s")
    assert entry["token"] == "tok"
    assert entry["env"]["FOO"] == "bar"


def test_cmd_mcp_smoke_client_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_client,
        "smoke_server",
        lambda *a, **k: (_ for _ in ()).throw(mcp_client.McpClientError("fail", code=3)),
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_smoke(args) == 3
    err = capsys.readouterr().err
    assert "artifact:" in err
    arts = list((tmp_path / ".local" / "workflow-artifacts" / "mcp").glob("smoke-*.md"))
    assert arts


def test_cmd_mcp_smoke_validation_error(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_manage, "write_merged_mcp", lambda _r: (_ for _ in ()).throw(ValueError("bad"))
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_smoke(args) == mcp_manage.EXIT_VALIDATION


def test_cmd_mcp_smoke_success(tmp_path: Path, monkeypatch, capsys) -> None:
    _seed_kit(tmp_path)
    monkeypatch.setattr(
        mcp_client,
        "smoke_server",
        lambda *a, **k: {"server": "kit-server", "ok": True, "tool_count": 1, "tools": ["t"]},
    )
    args = argparse.Namespace(directory=tmp_path, server="kit-server", agent=None)
    assert mcp_cli.cmd_mcp_smoke(args) == 0
    out = capsys.readouterr().out
    assert "MCP smoke OK" in out
    assert "artifact:" in out


def test_cmd_mcp_validate_merge_fail(tmp_path: Path, capsys) -> None:
    (tmp_path / ".cursor").mkdir()
    args = argparse.Namespace(directory=tmp_path, strict=False)
    assert mcp_cli.cmd_mcp_validate(args) == 1
    assert "FAIL" in capsys.readouterr().err


def test_cmd_mcp_link_success_and_fail(tmp_path: Path, capsys) -> None:
    _seed_kit(tmp_path)
    fragment = tmp_path / "frag.json"
    fragment.write_text(
        json.dumps({"mcpServers": {"new-server": {"command": "bar"}}}), encoding="utf-8"
    )
    args = argparse.Namespace(directory=tmp_path, name="new-server", file=fragment)
    assert mcp_cli.cmd_mcp_link(args) == 0
    assert "linked" in capsys.readouterr().out
    assert (tmp_path / ".gitignore").is_file()

    bad = argparse.Namespace(directory=tmp_path, name="x", file=fragment)
    # fragment has new-server only; linking name x with multi? empty rename path —
    # use empty fragment for failure
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    bad.file = empty
    assert mcp_cli.cmd_mcp_link(bad) == 1
    assert "FAIL" in capsys.readouterr().err
