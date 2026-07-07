"""
File: test_cursor_workflow_cli_full.py
Path: tests/modules/install/test_cursor_workflow_cli_full.py
Role: Full-branch in-process coverage for .ai_infra/install/cursor_workflow/cli.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/cli.py
 - .ai_infra/install/cursor_workflow/mcp_manage.py
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import cli  # noqa: E402
import paths  # noqa: E402
import contributors_cli  # noqa: E402
import drift_cli  # noqa: E402
import integrate_cli  # noqa: E402
import mcp_manage  # noqa: E402


# ---------------------------------------------------------------------------
# _run
# ---------------------------------------------------------------------------


def test_run_returns_code(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        cli.subprocess, "run", lambda cmd, cwd, timeout: SimpleNamespace(returncode=3)
    )
    assert cli._run(["true"], tmp_path) == 3


def test_run_timeout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    def _raise(cmd, cwd, timeout):  # noqa: ANN001
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(cli.subprocess, "run", _raise)
    code = cli._run(["sleep", "999"], tmp_path, timeout_s=0.01)
    assert code == 124
    assert "timeout after" in capsys.readouterr().err


# ---------------------------------------------------------------------------
# _resolve_install_source
# ---------------------------------------------------------------------------


def test_resolve_install_source_none() -> None:
    assert cli._resolve_install_source(None) == cli.kit_root()


def test_resolve_install_source_absolute(tmp_path: Path) -> None:
    assert cli._resolve_install_source(tmp_path) == tmp_path.resolve()


def test_resolve_install_source_relative_found_under_root() -> None:
    result = cli._resolve_install_source(Path("."))
    assert result.is_dir()


def test_resolve_install_source_relative_not_found() -> None:
    raw = Path("definitely-nowhere-xyz")
    result = cli._resolve_install_source(raw)
    assert result == raw.resolve()


# ---------------------------------------------------------------------------
# cmd_install
# ---------------------------------------------------------------------------


def test_cmd_install_all_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, list[str]] = {}

    def _fake_run(cmd: list[str], cwd: Path) -> int:
        captured["cmd"] = cmd
        return 0

    monkeypatch.setattr(cli, "_run", _fake_run)
    args = argparse.Namespace(
        target=tmp_path / "out",
        source=tmp_path / "src",
        profile="with_mcp",
        dry_run=True,
        with_readme=True,
        with_tests=True,
        with_venv=True,
        with_mcp_json=True,
        verify=True,
    )
    assert cli.cmd_install(args) == 0
    cmd = captured["cmd"]
    for flag in ("--dry-run", "--with-readme", "--with-tests", "--with-venv", "--with-mcp-json", "--verify"):
        assert flag in cmd


def test_cmd_install_no_flags(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    captured: dict[str, list[str]] = {}

    def _fake_run(cmd: list[str], cwd: Path) -> int:
        captured["cmd"] = cmd
        return 0

    monkeypatch.setattr(cli, "_run", _fake_run)
    args = argparse.Namespace(
        target=tmp_path / "out",
        source=tmp_path / "src",
        profile="default",
        dry_run=False,
        with_readme=False,
        with_tests=False,
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    assert cli.cmd_install(args) == 0
    for flag in ("--dry-run", "--with-readme", "--with-tests", "--with-venv", "--with-mcp-json", "--verify"):
        assert flag not in captured["cmd"]


# ---------------------------------------------------------------------------
# cmd_gates
# ---------------------------------------------------------------------------


def test_cmd_gates_all_pass(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "_run", lambda cmd, cwd: 0)
    args = argparse.Namespace(directory=REPO_ROOT)
    assert cli.cmd_gates(args) == 0


def test_cmd_gates_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str], cwd: Path) -> int:
        calls.append(cmd)
        return 5

    monkeypatch.setattr(cli, "_run", _fake_run)
    args = argparse.Namespace(directory=REPO_ROOT)
    assert cli.cmd_gates(args) == 5
    assert len(calls) == 1


def test_cmd_gates_uses_resolve_project_python(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".ai_infra" / "scripts" / "pr").mkdir(parents=True)
    (tmp_path / ".ai_infra" / "scripts" / "architecture").mkdir(parents=True)
    (tmp_path / ".ai_infra" / "scripts" / "pr" / "check_testing_artifacts.py").write_text(
        "# stub\n", encoding="utf-8"
    )
    resolved_roots: list[Path | None] = []
    seen_interpreters: list[str] = []

    def _fake_resolve(root: Path | None = None) -> str:
        resolved_roots.append(root)
        return "/tmp/fake-project-python"

    def _fake_run(cmd: list[str], cwd: Path) -> int:
        seen_interpreters.append(cmd[0])
        return 0

    monkeypatch.setattr(paths, "resolve_project_python", _fake_resolve)
    monkeypatch.setattr(cli, "_run", _fake_run)
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_gates(args) == 0
    assert resolved_roots == [tmp_path.resolve()]
    assert seen_interpreters == ["/tmp/fake-project-python"] * 5


def test_cmd_gates_fallback_scripts_dir_raises_when_absent(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Local .ai_infra/scripts/pr is absent on both root and fallback lookup — the
    # fallback re-resolves the identical path via scripts_dir(), which also raises.
    (tmp_path / ".ai_infra").mkdir()
    monkeypatch.setattr(cli, "_run", lambda cmd, cwd: 0)
    args = argparse.Namespace(directory=tmp_path)
    with pytest.raises(FileNotFoundError):
        cli.cmd_gates(args)


def test_cmd_gates_fallback_arch_dir_line_reached(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Drive the fallback branch's second assignment (arch = scripts_dir(...)) by making
    # the "pr" fallback succeed via a stubbed scripts_dir, independent of paths.py's own
    # (identical-path) re-check — isolates cmd_gates' own control flow.
    real_scripts_dir = cli.scripts_dir

    def _fake_scripts_dir(name: str, root: Path | None = None) -> Path:
        if name == "pr":
            return tmp_path / "stub-pr"
        return real_scripts_dir(name, root)

    monkeypatch.setattr(cli, "scripts_dir", _fake_scripts_dir)
    monkeypatch.setattr(cli, "_run", lambda cmd, cwd: 0)
    args = argparse.Namespace(directory=tmp_path)
    with pytest.raises(FileNotFoundError):
        cli.cmd_gates(args)


# ---------------------------------------------------------------------------
# cmd_health
# ---------------------------------------------------------------------------


def test_cmd_health_pass_on_kit_repo() -> None:
    args = argparse.Namespace(directory=REPO_ROOT)
    assert cli.cmd_health(args) == 0


def test_cmd_health_missing_required_file(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def test_cmd_health_mcp_validate_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json.kit.example").write_text("{}\n", encoding="utf-8")
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text("servers: {}\n", encoding="utf-8")
    monkeypatch.setattr(mcp_manage, "write_merged_mcp", lambda root: None)
    monkeypatch.setattr(mcp_manage, "validate_registry", lambda root: ["bad registry"])
    monkeypatch.setattr(
        contributors_cli, "_import_user_settings", lambda root: (_ for _ in ()).throw(FileNotFoundError("no pr"))
    )
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def test_cmd_health_mcp_validate_raises(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json.kit.example").write_text("{}\n", encoding="utf-8")
    (tmp_path / ".cursor" / "mcp.registry.yaml").write_text("servers: {}\n", encoding="utf-8")

    def _raise(root):  # noqa: ANN001
        raise ValueError("bad json")

    monkeypatch.setattr(mcp_manage, "write_merged_mcp", _raise)
    monkeypatch.setattr(
        contributors_cli, "_import_user_settings", lambda root: (_ for _ in ()).throw(FileNotFoundError("no pr"))
    )
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def test_cmd_health_user_settings_missing_pr(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        contributors_cli, "_import_user_settings", lambda root: (_ for _ in ()).throw(FileNotFoundError("no pr"))
    )
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def test_cmd_health_user_settings_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_us = SimpleNamespace(validate_github_collaboration=lambda root: ["bad owner"])
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake_us)
    monkeypatch.setattr(
        integrate_cli, "_import_validate", lambda root: (_ for _ in ()).throw(FileNotFoundError("no integ"))
    )
    monkeypatch.setattr(
        drift_cli, "_import_check_drift", lambda root: (_ for _ in ()).throw(FileNotFoundError("no drift"))
    )
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def _severity(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


def test_cmd_health_integrate_and_drift_p0_failures(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_us = SimpleNamespace(validate_github_collaboration=lambda root: [])
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake_us)

    fake_validate = SimpleNamespace(
        run_checks=lambda root: [
            SimpleNamespace(passed=False, severity=_severity("P0"), check_id="INT-001", detail="bad"),
            SimpleNamespace(passed=True, severity=_severity("P0"), check_id="INT-002", detail="ok"),
            SimpleNamespace(passed=False, severity=_severity("P1"), check_id="INT-003", detail="minor"),
        ]
    )
    monkeypatch.setattr(integrate_cli, "_import_validate", lambda root: fake_validate)

    fake_drift = SimpleNamespace(
        run_checks=lambda root: [
            SimpleNamespace(passed=False, severity=_severity("P0"), check_id="DRIFT-001", detail="stale"),
        ]
    )
    monkeypatch.setattr(drift_cli, "_import_check_drift", lambda root: fake_drift)

    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 1


def test_cmd_health_integrate_and_drift_all_pass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake_us = SimpleNamespace(validate_github_collaboration=lambda root: [])
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake_us)
    monkeypatch.setattr(integrate_cli, "_import_validate", lambda root: SimpleNamespace(run_checks=lambda root: []))
    monkeypatch.setattr(drift_cli, "_import_check_drift", lambda root: SimpleNamespace(run_checks=lambda root: []))

    for rel in (
        ".ai_infra/scripts/pr/prepare.py",
        ".ai_infra/.kit-version",
        ".cursor/agents/implementer.md",
        ".local/index-and-planning/current/session-pointer.md",
    ):
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("ok\n", encoding="utf-8")

    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_health(args) == 0


# ---------------------------------------------------------------------------
# cmd_mcp_validate / cmd_mcp_link
# ---------------------------------------------------------------------------


def _write_mcp_fixture(root: Path) -> None:
    cursor = root / ".cursor"
    cursor.mkdir(parents=True, exist_ok=True)
    (cursor / "mcp.json.kit.example").write_text(
        json.dumps({"mcpServers": {"kit-server": {"command": "foo"}}}), encoding="utf-8"
    )
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"kit-server": {"agents": []}}}), encoding="utf-8"
    )


def test_cmd_mcp_validate_pass(tmp_path: Path) -> None:
    _write_mcp_fixture(tmp_path)
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_mcp_validate(args) == 0


def test_cmd_mcp_validate_fail_missing_fragment(tmp_path: Path) -> None:
    (tmp_path / ".cursor").mkdir()
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_mcp_validate(args) == 1


def test_cmd_mcp_validate_fail_registry_mismatch(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    (cursor / "mcp.json.kit.example").write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    (cursor / "mcp.registry.yaml").write_text(
        yaml.safe_dump({"servers": {"missing-server": {"agents": []}}}), encoding="utf-8"
    )
    args = argparse.Namespace(directory=tmp_path)
    assert cli.cmd_mcp_validate(args) == 1


def test_cmd_mcp_link_success(tmp_path: Path) -> None:
    _write_mcp_fixture(tmp_path)
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {"new-server": {"command": "bar"}}}), encoding="utf-8")
    args = argparse.Namespace(directory=tmp_path, name="new-server", file=fragment)
    assert cli.cmd_mcp_link(args) == 0
    assert (tmp_path / ".gitignore").is_file()


def test_cmd_mcp_link_failure(tmp_path: Path) -> None:
    cursor = tmp_path / ".cursor"
    cursor.mkdir()
    fragment = tmp_path / "fragment.json"
    fragment.write_text(json.dumps({"mcpServers": {}}), encoding="utf-8")
    args = argparse.Namespace(directory=tmp_path, name="whatever", file=fragment)
    assert cli.cmd_mcp_link(args) == 1


# ---------------------------------------------------------------------------
# build_parser / main
# ---------------------------------------------------------------------------


def test_build_parser_version_exits(capsys: pytest.CaptureFixture[str]) -> None:
    parser = cli.build_parser()
    with pytest.raises(SystemExit) as exc:
        parser.parse_args(["--version"])
    assert exc.value.code == 0
    assert "cursor-workflow 0.4.0" in capsys.readouterr().out


def test_main_install_dispatch(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr(cli, "_run", lambda cmd, cwd: 0)
    code = cli.main(["install", "--target", str(tmp_path / "out")])
    assert code == 0


def test_cli_module_raises_when_no_kit_root_found(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    # Run the *real* cli.py file (so coverage attributes the hit line to the tracked
    # source path) but make every bootstrap.py candidate report as missing, forcing the
    # walk-up for/else loop to exhaust and hit its RuntimeError branch.
    monkeypatch.setattr(Path, "is_file", lambda self: False)
    with pytest.raises(RuntimeError, match="kit root not found"):
        runpy.run_path(str(_PKG_DIR / "cli.py"), run_name="cli_no_bootstrap_found")


def test_main_health_dispatch() -> None:
    code = cli.main(["health", "--directory", str(REPO_ROOT)])
    assert code == 0


def test_cli_module_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    import runpy

    monkeypatch.setattr(sys, "argv", ["cli.py", "health", "--directory", str(REPO_ROOT)])
    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(_PKG_DIR / "cli.py"), run_name="__main__")
    assert exc.value.code == 0


def test_cli_module_fresh_import_inserts_ai_infra_and_mcp_pkg_paths(monkeypatch: pytest.MonkeyPatch) -> None:
    # cli.py's own bootstrap walk-up loop (lines ~22-39) only inserts each directory into
    # sys.path the first time it is imported in this process; subsequent imports reuse the
    # cached sys.modules entry and skip the body. Force a genuinely fresh exec via runpy
    # with both directories removed from sys.path first, to cover the True branches.
    import runpy

    # Duplicate entries can accumulate across the suite (multiple scripts share the same
    # bootstrap-insert target), so strip every occurrence rather than just the first, or the
    # "not in sys.path" guard in cli.py stays false and the insert's True branch is skipped.
    # Dedupe back to at most one copy afterwards (rather than the original duplicate count)
    # so duplicates don't keep re-accumulating for later tests.
    ai_infra_entry = str(REPO_ROOT / ".ai_infra")
    mcp_pkg_entry = str(_PKG_DIR)

    ai_infra_was_present = ai_infra_entry in sys.path
    while ai_infra_entry in sys.path:
        sys.path.remove(ai_infra_entry)
    mcp_pkg_was_present = mcp_pkg_entry in sys.path
    while mcp_pkg_entry in sys.path:
        sys.path.remove(mcp_pkg_entry)
    monkeypatch.setattr(sys, "argv", ["cli.py", "--version"])
    try:
        with pytest.raises(SystemExit):
            runpy.run_path(str(_PKG_DIR / "cli.py"), run_name="__main__")
    finally:
        ai_infra_added = ai_infra_entry in sys.path
        while ai_infra_entry in sys.path:
            sys.path.remove(ai_infra_entry)
        if ai_infra_was_present or ai_infra_added:
            sys.path.insert(0, ai_infra_entry)
        mcp_pkg_added = mcp_pkg_entry in sys.path
        while mcp_pkg_entry in sys.path:
            sys.path.remove(mcp_pkg_entry)
        if mcp_pkg_was_present or mcp_pkg_added:
            sys.path.insert(0, mcp_pkg_entry)
    assert ai_infra_entry in sys.path
    assert mcp_pkg_entry in sys.path
