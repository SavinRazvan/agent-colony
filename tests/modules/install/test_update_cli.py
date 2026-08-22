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
import json
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
import kit_cleanup  # noqa: E402
import update_cli  # noqa: E402


def _write_manifest(base: Path, version: str) -> Path:
    ai = base / ".ai_infra"
    ai.mkdir(parents=True, exist_ok=True)
    (ai / "manifest.yaml").write_text(f"kit_version: {version}\n", encoding="utf-8")
    return base


def _write_payload_scaffold(source: Path) -> Path:
    script = source / ".ai_infra" / "scripts" / "install" / "scaffold.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("# payload scaffold marker\n", encoding="utf-8")
    return script


def _write_installed(target: Path, version: str | None) -> Path:
    ai = target / ".ai_infra"
    ai.mkdir(parents=True, exist_ok=True)
    if version is not None:
        (ai / ".kit-version").write_text(f"{version}\n", encoding="utf-8")
    return target


def test_compare_versions_semver() -> None:
    assert update_cli.compare_versions("0.6.0", "0.6.4") == -1
    assert update_cli.compare_versions("0.6.4", "0.6.4") == 0
    assert update_cli.compare_versions("0.7.0", "0.6.4") == 1


def test_decide_action_matrix() -> None:
    assert update_cli.decide_action(installed=None, available="0.6.4", force=False) == "missing"
    assert update_cli.decide_action(installed="0.6.4", available="0.6.4", force=False) == "heal"
    assert update_cli.decide_action(installed="0.6.0", available="0.6.4", force=False) == "upgrade"
    assert update_cli.decide_action(installed="0.6.4", available="0.6.4", force=True) == "upgrade"


def test_read_installed_and_source_version(tmp_path: Path) -> None:
    target = _write_installed(tmp_path / "app", "0.6.0")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
    assert update_cli.read_installed_version(target) == "0.6.0"
    assert update_cli.read_source_version(source) == "0.6.4"
    assert update_cli.read_installed_version(tmp_path / "empty") is None


def test_cmd_update_check_heal(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.4")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
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


def test_cmd_update_check_heal_fails_on_agent_delta(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "app", "0.6.4")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
    for base in (target, source):
        agents = base / ".cursor" / "agents"
        agents.mkdir(parents=True)
        (agents / "implementer.md").write_text("# impl\n", encoding="utf-8")
    (target / ".cursor" / "agents" / "implementer.md").write_text("# edited\n", encoding="utf-8")
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
    err = capsys.readouterr().err
    assert "check: FAIL" in err


def test_cmd_update_check_upgrade(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.0")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
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
    source = _write_manifest(tmp_path / "kit", "0.6.4")
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
    target = _write_installed(tmp_path / "app", "0.6.4")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
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
    source = _write_manifest(tmp_path / "kit", "0.6.4")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _scaffold(*a, **k) -> int:
        (target / ".ai_infra" / ".kit-version").write_text("0.6.4\n", encoding="utf-8")
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
    assert update_cli.read_installed_version(target) == "0.6.4"


def test_cmd_update_repairs_stale_kit_version_stamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.3")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _scaffold(*a, **k) -> int:
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
    assert update_cli.read_installed_version(target) == "0.6.4"


def test_cmd_update_force_when_equal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.4")
    source = _write_manifest(tmp_path / "kit", "0.6.4")
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


def test_cmd_update_force_with_mcp_passes_profile_to_scaffold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "app", "0.7.0")
    marker_dir = target / ".local" / "generated-data"
    marker_dir.mkdir(parents=True)
    (marker_dir / "install-profile.json").write_text(
        '{"profile": "consumer_lite", "kit_version": "0.7.0"}',
        encoding="utf-8",
    )
    source = _write_manifest(tmp_path / "kit", "0.7.0")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    captured: dict[str, object] = {}

    def _scaffold(*_a, **kwargs) -> int:
        captured.update(kwargs)
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
    assert captured.get("profile") == "with_mcp"


def test_cmd_update_refuses_kit_dev_force(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "kit-dev", "0.6.4")
    marker = target / update_cli.KIT_TESTS_MARKER
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("# kit-dev\n", encoding="utf-8")
    source = _write_manifest(tmp_path / "payload", "0.6.4")
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
    source = _write_manifest(tmp_path / "payload", "0.6.4")
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


def test_scan_kit_agent_deltas_detects_edit(tmp_path: Path) -> None:
    target = tmp_path / "app"
    source = tmp_path / "kit"
    for base in (target, source):
        agents = base / ".cursor" / "agents"
        agents.mkdir(parents=True)
        (agents / "implementer.md").write_text("# impl\n", encoding="utf-8")
    (target / ".cursor" / "agents" / "implementer.md").write_text(
        "# modified\n", encoding="utf-8"
    )
    failures, warnings = update_cli.scan_kit_agent_deltas(target, source)
    assert failures == [".cursor/agents/implementer.md"]
    assert warnings == []


def test_scan_kit_managed_deltas_ignores_pycache_and_kit_version(tmp_path: Path) -> None:
    target = tmp_path / "app"
    source = tmp_path / "kit"
    contract = {
        "profiles": {
            "default": {
                "kit_managed_globs": [".ai_infra/**", "agent_colony/**"],
            }
        }
    }
    for base in (target, source):
        ai = base / ".ai_infra"
        ai.mkdir(parents=True, exist_ok=True)
        (ai / "install-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (ai / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    (target / ".ai_infra" / ".kit-version").write_text("0.6.6\n", encoding="utf-8")
    pyc = target / ".ai_infra" / "__pycache__" / "bootstrap.cpython-312.pyc"
    pyc.parent.mkdir(parents=True)
    pyc.write_bytes(b"compiled")
    orphan = target / ".ai_infra" / "docs" / "decisions" / "ADR-old.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("# old\n", encoding="utf-8")
    failures, warnings = update_cli.scan_kit_agent_deltas(target, source)
    assert failures == []
    assert any("ADR-old.md" in w for w in warnings)


def test_cmd_update_check_passes_heal_with_orphans_only(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "app", "0.6.6")
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    _write_payload_scaffold(source)
    (target / ".ai_infra" / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    (source / ".ai_infra" / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    orphan = target / ".ai_infra" / "orphan-only.py"
    orphan.write_text("# x\n", encoding="utf-8")
    contract = {"profiles": {"default": {"kit_managed_globs": [".ai_infra/**"]}}}
    for base in (target, source):
        (base / ".ai_infra" / "install-contract.json").write_text(
            json.dumps(contract), encoding="utf-8"
        )
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
    assert "action=heal" in out
    assert "check: PASS" in out


def test_scan_kit_managed_deltas_detects_skill_edit(tmp_path: Path) -> None:
    target = tmp_path / "app"
    source = tmp_path / "kit"
    contract = {
        "profiles": {
            "default": {
                "kit_managed_globs": [
                    ".cursor/skills/foo/SKILL.md",
                ]
            }
        }
    }
    for base in (target, source):
        ai = base / ".ai_infra"
        ai.mkdir(parents=True, exist_ok=True)
        skill = base / ".cursor" / "skills" / "foo" / "SKILL.md"
        skill.parent.mkdir(parents=True)
        skill.write_text("# skill\n", encoding="utf-8")
        (ai / "install-contract.json").write_text(json.dumps(contract), encoding="utf-8")
    (target / ".cursor" / "skills" / "foo" / "SKILL.md").write_text(
        "# edited\n", encoding="utf-8"
    )
    failures, warnings = update_cli.scan_kit_agent_deltas(target, source)
    assert failures == [".cursor/skills/foo/SKILL.md"]
    assert warnings == []


def test_scan_kit_agent_deltas_warns_extra(tmp_path: Path) -> None:
    target = tmp_path / "app"
    source = tmp_path / "kit"
    for base in (target, source):
        agents = base / ".cursor" / "agents"
        agents.mkdir(parents=True)
        for name in (
            "auditor",
            "board",
            "drift-guard",
            "implementer",
            "integrator",
            "researcher",
            "test-runner",
            "verifier",
        ):
            (agents / f"{name}.md").write_text(f"# {name}\n", encoding="utf-8")
    (target / ".cursor" / "agents" / "custom.md").write_text("# c\n", encoding="utf-8")
    failures, warnings = update_cli.scan_kit_agent_deltas(target, source)
    assert failures == []
    assert warnings == [".cursor/agents/custom.md"]


def test_cmd_update_repairs_wrong_scaffold_stamp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = _write_installed(tmp_path / "app", "0.6.5")
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)

    def _scaffold(*a, **k) -> int:
        (target / ".ai_infra" / ".kit-version").write_text("0.6.4\n", encoding="utf-8")
        _write_manifest(target, "0.6.6")
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
    assert update_cli.read_installed_version(target) == "0.6.6"


def test_scaffold_script_for_upgrade_prefers_source(tmp_path: Path) -> None:
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    target = _write_installed(tmp_path / "app", "0.6.4")
    payload_script = _write_payload_scaffold(source)
    target_script = _write_payload_scaffold(target)
    target_script.write_text("# old target scaffold\n", encoding="utf-8")
    assert update_cli.scaffold_script_for_upgrade(source, target) == payload_script


def test_run_scaffold_upgrade_invokes_source_script(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    target = _write_installed(tmp_path / "app", "0.6.4")
    payload_script = _write_payload_scaffold(source)
    captured: dict[str, object] = {}

    def _run(cmd, **kwargs):  # type: ignore[no-untyped-def]
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(update_cli.subprocess, "run", _run)
    code = update_cli._run_scaffold_upgrade(
        target,
        source,
        profile="with_mcp",
        with_venv=False,
        with_mcp_json=False,
        verify=False,
    )
    assert code == 0
    assert captured["cmd"][1] == str(payload_script)
    assert captured["cwd"] == source


def test_clean_runtime_artifacts_removes_pycache(tmp_path: Path) -> None:
    target = tmp_path / "app"
    pycache = target / ".ai_infra" / "install" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "mod.cpython-312.pyc").write_bytes(b"pyc")
    loose = target / "agent_colony" / "orphan.pyc"
    loose.parent.mkdir(parents=True)
    loose.write_bytes(b"pyc")
    summary = kit_cleanup.clean_runtime_artifacts(target)
    assert summary.runtime_dirs == 1
    assert summary.runtime_files >= 1
    assert not pycache.exists()
    assert not loose.exists()


def test_prune_kit_orphans_dry_run_vs_apply(tmp_path: Path) -> None:
    target = tmp_path / "app"
    source = tmp_path / "kit"
    contract = {"profiles": {"default": {"kit_managed_globs": [".ai_infra/**"]}}}
    for base in (target, source):
        ai = base / ".ai_infra"
        ai.mkdir(parents=True, exist_ok=True)
        (ai / "install-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (ai / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    orphan = target / ".ai_infra" / "docs" / "decisions" / "ADR-old.md"
    orphan.parent.mkdir(parents=True)
    orphan.write_text("# old\n", encoding="utf-8")
    dry = kit_cleanup.prune_kit_orphans(target, source, dry_run=True)
    assert dry.orphans_removed == 1
    assert orphan.is_file()
    applied = kit_cleanup.prune_kit_orphans(target, source, dry_run=False)
    assert applied.orphans_removed == 1
    assert not orphan.exists()


def test_cmd_update_clean_only_removes_noise_and_passes_check(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "app", "0.6.6")
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    _write_payload_scaffold(source)
    contract = {"profiles": {"default": {"kit_managed_globs": [".ai_infra/**"]}}}
    for base in (target, source):
        ai = base / ".ai_infra"
        (ai / "install-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (ai / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    pycache = target / ".ai_infra" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "x.cpython-312.pyc").write_bytes(b"pyc")
    orphan = target / ".ai_infra" / "orphan-only.py"
    orphan.write_text("# x\n", encoding="utf-8")
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
        no_clean=False,
        clean_only=True,
    )
    assert update_cli.cmd_update(args) == 0
    out = capsys.readouterr().out
    assert "check: PASS" in out
    assert not pycache.exists()
    assert not orphan.exists()


def test_cmd_update_pre_post_clean_on_upgrade(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    target = _write_installed(tmp_path / "app", "0.6.5")
    source = _write_manifest(tmp_path / "kit", "0.6.6")
    _write_payload_scaffold(source)
    contract = {"profiles": {"default": {"kit_managed_globs": [".ai_infra/**"]}}}
    for base in (target, source):
        ai = base / ".ai_infra"
        ai.mkdir(parents=True, exist_ok=True)
        (ai / "install-contract.json").write_text(json.dumps(contract), encoding="utf-8")
        (ai / "bootstrap.py").write_text("# ok\n", encoding="utf-8")
    orphan = target / ".ai_infra" / "stale-orphan.py"
    orphan.write_text("# stale\n", encoding="utf-8")
    pycache = target / "agent_colony" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "mod.cpython-312.pyc").write_bytes(b"pyc")
    monkeypatch.setattr(activate_cli, "resolve_activate_source", lambda *a, **k: source)
    def _fake_scaffold(*a, **k) -> int:
        _write_manifest(target, "0.6.6")
        (target / ".ai_infra" / ".kit-version").write_text("0.6.6\n", encoding="utf-8")
        (target / ".ai_infra" / "post-scaffold-orphan.py").write_text("# post\n", encoding="utf-8")
        return 0

    monkeypatch.setattr(update_cli, "_run_scaffold_upgrade", _fake_scaffold)
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
        with_venv=False,
        with_mcp_json=False,
        verify=False,
        profile="with_mcp",
        no_clean=False,
        clean_only=False,
    )
    assert update_cli.cmd_update(args) == 0
    out = capsys.readouterr().out
    assert "pre-clean" in out
    assert "post-clean" in out
    assert not orphan.exists()
    assert not pycache.exists()
    assert update_cli.read_installed_version(target) == "0.6.6"


def test_register_update_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    update_cli.register_update_subparser(sub)
    args = parser.parse_args(["update", "--check", "--directory", "."])
    assert args.command == "update"
    assert args.check is True
    assert args.func is update_cli.cmd_update
    args2 = parser.parse_args(["update", "--clean-only", "--directory", "."])
    assert args2.clean_only is True
    args3 = parser.parse_args(["update", "--no-clean", "--directory", "."])
    assert args3.no_clean is True
