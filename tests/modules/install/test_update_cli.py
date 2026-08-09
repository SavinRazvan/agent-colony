"""
File: test_update_cli.py
Path: tests/modules/install/test_update_cli.py
Role: Coverage for update_cli version gate, --check, heal, upgrade, --force.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/update_cli.py
 - .ai_infra/install/agent_colony/activate_cli.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
_AI_INFRA_DIR = REPO_ROOT / ".ai_infra"

for _p in (str(_PKG_DIR), str(_AI_INFRA_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import activate_cli  # noqa: E402
import update_cli  # noqa: E402


def _write_manifest(base: Path, version: str) -> Path:
    ai = base / ".ai_infra"
    ai.mkdir(parents=True, exist_ok=True)
    (ai / "manifest.yaml").write_text(f"kit_version: {version}\n", encoding="utf-8")
    return base


def _write_installed(target: Path, version: str | None) -> Path:
    ai = target / ".ai_infra"
    ai.mkdir(parents=True, exist_ok=True)
    if version is not None:
        (ai / ".kit-version").write_text(f"{version}\n", encoding="utf-8")
    return target


def test_compare_versions_semver() -> None:
    assert update_cli.compare_versions("0.6.0", "0.6.2") == -1
    assert update_cli.compare_versions("0.6.2", "0.6.2") == 0
    assert update_cli.compare_versions("0.7.0", "0.6.2") == 1


def test_decide_action_matrix() -> None:
    assert update_cli.decide_action(installed=None, available="0.6.2", force=False) == "missing"
    assert update_cli.decide_action(installed="0.6.2", available="0.6.2", force=False) == "heal"
    assert update_cli.decide_action(installed="0.6.0", available="0.6.2", force=False) == "upgrade"
    assert update_cli.decide_action(installed="0.6.2", available="0.6.2", force=True) == "upgrade"


def test_read_installed_and_source_version(tmp_path: Path) -> None:
    target = _write_installed(tmp_path / "app", "0.6.0")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    assert update_cli.read_installed_version(target) == "0.6.0"
    assert update_cli.read_source_version(source) == "0.6.2"
    assert update_cli.read_installed_version(tmp_path / "empty") is None


def test_cmd_update_check_heal(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.2")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    monkeypatch.setattr(
        activate_cli,
        "resolve_activate_source",
        lambda *a, **k: source,
    )
    args = argparse.Namespace(
        directory=target,
        source=None,
        check=True,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 0
    out = capsys.readouterr().out
    assert "action=heal" in out
    assert "would_heal" in out


def test_cmd_update_check_upgrade(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.0")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    args = argparse.Namespace(
        directory=target,
        source=None,
        check=True,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 0
    out = capsys.readouterr().out
    assert "action=upgrade" in out
    assert "would_upgrade" in out


def test_cmd_update_missing_ai_infra(tmp_path: Path) -> None:
    target = tmp_path / "bare"
    target.mkdir()
    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 1


def test_cmd_update_missing_kit_version(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", None)
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 1


def test_cmd_update_heal_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.2")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    calls: list[str] = []

    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _fake_heal(t: Path, *, with_venv: bool) -> None:
        calls.append(f"heal:{with_venv}")

    def _fake_refresh(t: Path, s: Path | None, k: Path) -> None:
        calls.append("refresh")

    monkeypatch.setattr(activate_cli, "_heal_consumer_runtime", _fake_heal)
    monkeypatch.setattr(activate_cli, "_refresh_dashboard_templates", _fake_refresh)

    plane = SimpleNamespace(
        assess_planes=lambda *a, **k: SimpleNamespace(all_ready=True),
        format_plane_report=lambda s: "planes ok",
    )
    monkeypatch.setattr(activate_cli, "_import_plane_status", lambda: plane)

    scaffold_calls: list[list[str]] = []

    def _boom(*a, **k):
        scaffold_calls.append(["scaffold"])
        return 99

    monkeypatch.setattr(update_cli, "_run_scaffold_upgrade", _boom)

    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 0
    assert "refresh" in calls
    assert any(c.startswith("heal:") for c in calls)
    assert scaffold_calls == []


def test_cmd_update_upgrade_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.0")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _scaffold(*a, **k) -> int:
        (target / ".ai_infra" / ".kit-version").write_text("0.6.2\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(update_cli, "_run_scaffold_upgrade", _scaffold)
    monkeypatch.setattr(activate_cli, "_heal_consumer_runtime", lambda *a, **k: None)
    plane = SimpleNamespace(
        assess_planes=lambda *a, **k: SimpleNamespace(all_ready=True),
        format_plane_report=lambda s: "planes ok",
    )
    monkeypatch.setattr(activate_cli, "_import_plane_status", lambda: plane)

    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 0
    assert update_cli.read_installed_version(target) == "0.6.2"


def test_cmd_update_force_when_equal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.2")
    source = _write_manifest(tmp_path / "kit", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    ran: list[str] = []

    def _scaffold(*a, **k) -> int:
        ran.append("upgrade")
        return 0

    monkeypatch.setattr(update_cli, "_run_scaffold_upgrade", _scaffold)
    monkeypatch.setattr(activate_cli, "_heal_consumer_runtime", lambda *a, **k: None)
    plane = SimpleNamespace(
        assess_planes=lambda *a, **k: SimpleNamespace(all_ready=True),
        format_plane_report=lambda s: "planes ok",
    )
    monkeypatch.setattr(activate_cli, "_import_plane_status", lambda: plane)

    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=True,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 0
    assert ran == ["upgrade"]


def test_cmd_update_refuses_kit_dev_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "kit-dev", "0.6.2")
    marker = target / update_cli.KIT_TESTS_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    source = _write_manifest(tmp_path / "payload", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _boom(*a, **k) -> int:
        raise AssertionError("scaffold must not run on kit-dev")

    monkeypatch.setattr(update_cli, "_run_scaffold_upgrade", _boom)

    args = argparse.Namespace(
        directory=target,
        source=None,
        check=False,
        force=True,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 1
    err = capsys.readouterr().err
    assert "kit-dev product repo" in err


def test_cmd_update_check_refuses_kit_dev_upgrade(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "kit-dev", "0.6.0")
    marker = target / update_cli.KIT_TESTS_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    source = _write_manifest(tmp_path / "payload", "0.6.2")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    args = argparse.Namespace(
        directory=target,
        source=None,
        check=True,
        force=False,
        with_venv=True,
        with_mcp_json=True,
        verify=False,
        profile="with_mcp",
    )
    assert update_cli.cmd_update(args) == 1
    out = capsys.readouterr().out
    assert "would_refuse_kit_dev" in out


def test_register_update_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    update_cli.register_update_subparser(sub)
    args = parser.parse_args(["update", "--check", "--directory", "."])
    assert args.command == "update"
    assert args.check is True
    assert args.func is update_cli.cmd_update
