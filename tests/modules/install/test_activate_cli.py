"""
File: test_activate_cli.py
Path: tests/modules/install/test_activate_cli.py
Role: Full-branch coverage for activate_cli.py (source resolution, hints, cmd_activate, parser).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/activate_cli.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
_AI_INFRA_DIR = REPO_ROOT / ".ai_infra"

for _p in (str(_PKG_DIR), str(_AI_INFRA_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import activate_cli  # noqa: E402
import paths  # noqa: E402


def _manifest_dir(base: Path) -> Path:
    (base / ".ai_infra").mkdir(parents=True, exist_ok=True)
    (base / ".ai_infra" / "manifest.yaml").write_text("kit_version: 0.0.0\n", encoding="utf-8")
    return base


# ---------------------------------------------------------------------------
# resolve_activate_source
# ---------------------------------------------------------------------------


def test_resolve_source_explicit_manifest_root(tmp_path: Path) -> None:
    source = _manifest_dir(tmp_path / "kit")
    result = activate_cli.resolve_activate_source(source, tmp_path / "target", tmp_path / "default")
    assert result == source.resolve()


def test_resolve_source_explicit_payload_subdir(tmp_path: Path) -> None:
    raw = tmp_path / "plugin"
    _manifest_dir(raw / "payload")
    result = activate_cli.resolve_activate_source(raw, tmp_path / "target", tmp_path / "default")
    assert result == (raw / "payload").resolve()


def test_resolve_source_explicit_invalid_raises(tmp_path: Path) -> None:
    raw = tmp_path / "nothing-here"
    raw.mkdir()
    with pytest.raises(FileNotFoundError, match="invalid activate source"):
        activate_cli.resolve_activate_source(raw, tmp_path / "target", tmp_path / "default")


def test_resolve_source_env_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_dir = _manifest_dir(tmp_path / "env-payload")
    monkeypatch.setenv("WORKFLOW_KIT_PAYLOAD", str(env_dir))
    result = activate_cli.resolve_activate_source(None, tmp_path / "target", tmp_path / "default")
    assert result == env_dir.resolve()


def test_resolve_source_env_payload_invalid_falls_through(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKFLOW_KIT_PAYLOAD", str(tmp_path / "does-not-exist"))
    target = tmp_path / "target"
    _manifest_dir(target / "payload")
    result = activate_cli.resolve_activate_source(None, target, tmp_path / "default")
    assert result == (target / "payload").resolve()


def test_resolve_source_target_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    target = tmp_path / "target"
    _manifest_dir(target / "payload")
    result = activate_cli.resolve_activate_source(None, target, tmp_path / "default")
    assert result == (target / "payload").resolve()


def test_resolve_source_default_kit_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    default_root = tmp_path / "default"
    _manifest_dir(default_root / "payload")
    result = activate_cli.resolve_activate_source(None, tmp_path / "target", default_root)
    assert result == (default_root / "payload").resolve()


def test_resolve_source_default_kit_root_itself(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    default_root = _manifest_dir(tmp_path / "default")
    target = tmp_path / "target"
    target.mkdir()
    result = activate_cli.resolve_activate_source(None, target, default_root)
    assert result == default_root.resolve()


def test_resolve_source_default_kit_root_equals_target_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    default_root = _manifest_dir(tmp_path / "same")
    with pytest.raises(FileNotFoundError, match="activate source not found"):
        activate_cli.resolve_activate_source(None, default_root, default_root)


def test_resolve_source_nothing_found_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    with pytest.raises(FileNotFoundError, match="activate source not found"):
        activate_cli.resolve_activate_source(None, tmp_path / "target", tmp_path / "default")


# ---------------------------------------------------------------------------
# _run_settings_validate
# ---------------------------------------------------------------------------


def test_run_settings_validate_returns_output(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run(cmd, cwd, capture_output, text):  # noqa: ANN001
        assert "contributors" in cmd
        return SimpleNamespace(returncode=0, stdout="PASS\n", stderr="")

    monkeypatch.setattr(activate_cli.subprocess, "run", _fake_run)
    code, out = activate_cli._run_settings_validate(tmp_path)
    assert code == 0
    assert out == "PASS"


# ---------------------------------------------------------------------------
# _print_post_activate_hints
# ---------------------------------------------------------------------------


def test_print_post_activate_hints(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    activate_cli._print_post_activate_hints(tmp_path)
    out = capsys.readouterr().out
    assert "github.collaboration.yaml" in out
    assert "/implementer" in out
    assert "/integrator-mas-agent" in out


# ---------------------------------------------------------------------------
# cmd_activate — branch coverage
# ---------------------------------------------------------------------------

_READY_PATHS = (
    ".cursor/agents/implementer.md",
    ".ai_infra/scripts/pr/prepare.py",
    ".local/index-and-planning/current/session-pointer.md",
    "AGENTS.md",
)


def _make_ready(root: Path) -> None:
    for rel in _READY_PATHS:
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("ok\n", encoding="utf-8")


def _args(**overrides) -> argparse.Namespace:
    base = dict(
        directory=None,
        source=None,
        profile="with_mcp",
        with_venv=False,
        with_mcp_json=False,
        verify=False,
        force=False,
        allow_settings_pending=True,
    )
    base.update(overrides)
    return argparse.Namespace(**base)


def test_cmd_activate_all_ready_settings_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    _make_ready(target)

    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="PASS", stderr=""),
    )
    code = activate_cli.cmd_activate(_args(directory=target))
    assert code == 0


def test_cmd_activate_idempotent_refreshes_dashboards_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    _make_ready(target)
    ui = target / ".ai_infra" / "templates" / "local-workspace"
    ui.mkdir(parents=True)
    (ui / "index.html").write_text("<html><title>Local control center</title></html>", encoding="utf-8")

    calls: list[tuple[Path, Path | None, Path]] = []

    def _fake_refresh(t: Path, source: Path | None, default_root: Path) -> None:
        calls.append((t, source, default_root))

    monkeypatch.setattr(activate_cli, "_refresh_dashboard_templates", _fake_refresh)
    monkeypatch.setattr(
        activate_cli,
        "resolve_activate_source",
        lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError("no payload")),
    )
    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="PASS", stderr=""),
    )
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)

    code = activate_cli.cmd_activate(_args(directory=target))
    assert code == 0
    assert len(calls) == 1
    assert calls[0][0] == target.resolve()
    assert calls[0][1] is None


def test_cmd_activate_all_ready_settings_fail_pending_allowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    _make_ready(target)

    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="FAIL", stderr=""),
    )
    code = activate_cli.cmd_activate(_args(directory=target, allow_settings_pending=True))
    assert code == 0


def test_cmd_activate_all_ready_settings_fail_pending_disallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    _make_ready(target)

    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=1, stdout="FAIL", stderr=""),
    )
    code = activate_cli.cmd_activate(_args(directory=target, allow_settings_pending=False))
    assert code == 1


def test_cmd_activate_force_reinstall_when_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    _make_ready(target)
    source = _manifest_dir(tmp_path / "src")

    def _fake_run(cmd, *a, **k):  # noqa: ANN001
        if "--target" in cmd:
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="PASS", stderr="")

    monkeypatch.setattr(activate_cli.subprocess, "run", _fake_run)
    monkeypatch.setattr(paths, "kit_root", lambda: REPO_ROOT)
    code = activate_cli.cmd_activate(_args(directory=target, source=source, force=True))
    assert code == 0


def test_cmd_activate_source_not_found(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    monkeypatch.delenv("WORKFLOW_KIT_PAYLOAD", raising=False)
    monkeypatch.setattr(paths, "kit_root", lambda: tmp_path / "no-manifest-here")
    code = activate_cli.cmd_activate(_args(directory=target, source=None))
    assert code == 1


def test_cmd_activate_source_equals_target(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _manifest_dir(tmp_path / "target")
    code = activate_cli.cmd_activate(_args(directory=target, source=target))
    assert code == 1


def test_cmd_activate_install_subprocess_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    source = _manifest_dir(tmp_path / "src")

    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=7, stdout="", stderr="boom"),
    )
    monkeypatch.setattr(paths, "kit_root", lambda: REPO_ROOT)
    code = activate_cli.cmd_activate(_args(directory=target, source=source))
    assert code == 7


def test_cmd_activate_install_succeeds_but_planes_incomplete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    source = _manifest_dir(tmp_path / "src")

    monkeypatch.setattr(
        activate_cli.subprocess,
        "run",
        lambda *a, **k: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    monkeypatch.setattr(paths, "kit_root", lambda: REPO_ROOT)
    code = activate_cli.cmd_activate(_args(directory=target, source=source))
    assert code == 1


def test_cmd_activate_install_succeeds_settings_pass(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    source = _manifest_dir(tmp_path / "src")

    def _fake_run(cmd, *a, **k):  # noqa: ANN001
        if "--target" in cmd:
            _make_ready(target)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=0, stdout="PASS", stderr="")

    monkeypatch.setattr(activate_cli.subprocess, "run", _fake_run)
    monkeypatch.setattr(paths, "kit_root", lambda: REPO_ROOT)
    code = activate_cli.cmd_activate(
        _args(directory=target, source=source, with_venv=True, with_mcp_json=True, verify=True)
    )
    assert code == 0


def test_cmd_activate_install_succeeds_settings_fail_pending_disallowed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    target.mkdir()
    source = _manifest_dir(tmp_path / "src")

    def _fake_run(cmd, *a, **k):  # noqa: ANN001
        if "--target" in cmd:
            _make_ready(target)
            return SimpleNamespace(returncode=0, stdout="", stderr="")
        return SimpleNamespace(returncode=1, stdout="FAIL", stderr="")

    monkeypatch.setattr(activate_cli.subprocess, "run", _fake_run)
    monkeypatch.setattr(paths, "kit_root", lambda: REPO_ROOT)
    code = activate_cli.cmd_activate(_args(directory=target, source=source, allow_settings_pending=False))
    assert code == 1


# ---------------------------------------------------------------------------
# register_activate_subparser
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Dashboard refresh helpers
# ---------------------------------------------------------------------------


def test_import_scaffold_refresh_returns_scaffold_module() -> None:
    scaffold = activate_cli._import_scaffold_refresh()
    assert hasattr(scaffold, "refresh_dashboards")


def test_import_scaffold_refresh_inserts_install_dir_on_sys_path() -> None:
    install_dir = Path(activate_cli.__file__).resolve().parents[2] / "scripts" / "install"
    install_str = str(install_dir)
    original = sys.path.copy()
    try:
        sys.path[:] = [p for p in sys.path if p != install_str]
        activate_cli._import_scaffold_refresh()
        assert install_str in sys.path
    finally:
        sys.path[:] = original


def test_resolve_dashboard_refresh_source_embedded_fallback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    ui = target / ".ai_infra" / "templates" / "local-workspace"
    ui.mkdir(parents=True)
    (ui / "index.html").write_text("<html></html>", encoding="utf-8")

    def _raise(*_a, **_k):  # noqa: ANN001
        raise FileNotFoundError("no payload")

    monkeypatch.setattr(activate_cli, "resolve_activate_source", _raise)
    result = activate_cli._resolve_dashboard_refresh_source(None, target, tmp_path / "default")
    assert result == target


def test_resolve_dashboard_refresh_source_no_embedded_returns_none(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "target"
    target.mkdir()

    def _raise(*_a, **_k):  # noqa: ANN001
        raise FileNotFoundError("no payload")

    monkeypatch.setattr(activate_cli, "resolve_activate_source", _raise)
    result = activate_cli._resolve_dashboard_refresh_source(None, target, tmp_path / "default")
    assert result is None


def test_refresh_dashboard_templates_skips_when_no_source(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    target.mkdir()
    calls: list[tuple[Path, Path]] = []

    class _FakeScaffold:
        @staticmethod
        def refresh_dashboards(source: Path, t: Path, dry_run: bool = False) -> list[str]:  # noqa: ARG004
            calls.append((source, t))
            return []

    monkeypatch.setattr(activate_cli, "_resolve_dashboard_refresh_source", lambda *a, **k: None)
    monkeypatch.setattr(activate_cli, "_import_scaffold_refresh", lambda: _FakeScaffold())
    activate_cli._refresh_dashboard_templates(target, None, tmp_path / "default")
    assert calls == []


def test_refresh_dashboard_templates_calls_scaffold(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "target"
    source = tmp_path / "source"
    source.mkdir()
    calls: list[tuple[Path, Path]] = []

    class _FakeScaffold:
        @staticmethod
        def refresh_dashboards(s: Path, t: Path, dry_run: bool = False) -> list[str]:  # noqa: ARG004
            calls.append((s, t))
            return ["ok"]

    monkeypatch.setattr(activate_cli, "_import_scaffold_refresh", lambda: _FakeScaffold())
    activate_cli._refresh_dashboard_templates(target, source, tmp_path / "default")
    assert calls == [(source, target)]


def test_register_activate_subparser_defaults_and_flags() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    activate_cli.register_activate_subparser(sub)

    args = parser.parse_args(["activate"])
    assert args.func is activate_cli.cmd_activate
    assert args.profile == "with_mcp"
    assert args.with_venv is True
    assert args.with_mcp_json is True
    assert args.verify is True
    assert args.force is False
    assert args.allow_settings_pending is True

    args2 = parser.parse_args(
        ["activate", "--no-venv", "--no-mcp-json", "--no-verify", "--force", "--directory", "/tmp/x"]
    )
    assert args2.with_venv is False
    assert args2.with_mcp_json is False
    assert args2.verify is False
    assert args2.force is True
    assert args2.directory == Path("/tmp/x")
