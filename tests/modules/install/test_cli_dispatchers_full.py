"""
File: test_cli_dispatchers_full.py
Path: tests/modules/install/test_cli_dispatchers_full.py
Role: Full-branch in-process coverage for the thin CLI dispatcher modules
      (doc_cli, verify_cli, drift_cli, integrate_cli, contributors_cli).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/{doc_cli,verify_cli,drift_cli,integrate_cli,contributors_cli}.py
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import contributors_cli  # noqa: E402
import doc_cli  # noqa: E402
import drift_cli  # noqa: E402
import integrate_cli  # noqa: E402
import verify_cli  # noqa: E402


def _severity(value: str) -> SimpleNamespace:
    return SimpleNamespace(value=value)


# ---------------------------------------------------------------------------
# doc_cli
# ---------------------------------------------------------------------------


def test_import_check_doc_facts_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        doc_cli._import_check_doc_facts(tmp_path)


def test_import_check_doc_facts_real() -> None:
    mod = doc_cli._import_check_doc_facts(REPO_ROOT)
    assert hasattr(mod, "run_checks")


def _fake_doc_facts_result() -> SimpleNamespace:
    return SimpleNamespace(check_id="DOC-001", severity=_severity("P1"), passed=True, detail="ok")


def test_cmd_doc_validate_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path, json=False, write_preflight=False, preflight_out=None)
    assert doc_cli.cmd_doc_validate(args) == 1


def test_cmd_doc_validate_json_with_preflight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(
        run_checks=lambda root: [_fake_doc_facts_result()],
        write_preflight_json=lambda results, path: path.parent.mkdir(parents=True, exist_ok=True)
        or path.write_text("{}", encoding="utf-8"),
        exit_code_for=lambda results: 0,
        format_report=lambda results: "report",
    )
    monkeypatch.setattr(doc_cli, "_import_check_doc_facts", lambda root: fake)
    args = argparse.Namespace(
        directory=tmp_path, json=True, write_preflight=True, preflight_out=None
    )
    assert doc_cli.cmd_doc_validate(args) == 0
    assert (tmp_path / ".local" / "workflow-artifacts" / "audit" / "doc-facts-preflight.json").is_file()


def test_cmd_doc_validate_text_explicit_preflight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    written: dict[str, Path] = {}
    fake = SimpleNamespace(
        run_checks=lambda root: [_fake_doc_facts_result()],
        write_preflight_json=lambda results, path: written.setdefault("path", path),
        exit_code_for=lambda results: 1,
        format_report=lambda results: "report",
    )
    monkeypatch.setattr(doc_cli, "_import_check_doc_facts", lambda root: fake)
    custom = tmp_path / "custom-preflight.json"
    args = argparse.Namespace(directory=tmp_path, json=False, write_preflight=False, preflight_out=custom)
    assert doc_cli.cmd_doc_validate(args) == 1
    assert written["path"] == custom


def test_register_doc_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    doc_cli.register_doc_subparser(sub)
    args = parser.parse_args(["doc", "validate"])
    assert args.func is doc_cli.cmd_doc_validate


# ---------------------------------------------------------------------------
# verify_cli
# ---------------------------------------------------------------------------


def test_import_verify_all_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        verify_cli._import_verify_all(tmp_path)


def test_import_verify_all_real() -> None:
    mod = verify_cli._import_verify_all(REPO_ROOT)
    assert hasattr(mod, "run_verify_all")


def test_cmd_verify_all_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path, json=False, write_preflight=False, preflight_out=None)
    assert verify_cli.cmd_verify_all(args) == 1


def test_cmd_verify_all_json_with_preflight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(
        run_verify_all=lambda root, py: [SimpleNamespace(name="gates", exit_code=0, command="make gates")],
        write_preflight_json=lambda results, path: path.parent.mkdir(parents=True, exist_ok=True)
        or path.write_text("{}", encoding="utf-8"),
        exit_code_for=lambda results: 0,
        format_report=lambda results: "report",
    )
    monkeypatch.setattr(verify_cli, "_import_verify_all", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path, json=True, write_preflight=True, preflight_out=None)
    assert verify_cli.cmd_verify_all(args) == 0
    assert (tmp_path / ".local" / "workflow-artifacts" / "audit" / "preflight.json").is_file()


def test_cmd_verify_all_text_explicit_preflight(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    written: dict[str, Path] = {}
    fake = SimpleNamespace(
        run_verify_all=lambda root, py: [SimpleNamespace(name="gates", exit_code=1, command="make gates")],
        write_preflight_json=lambda results, path: written.setdefault("path", path),
        exit_code_for=lambda results: 1,
        format_report=lambda results: "report",
    )
    monkeypatch.setattr(verify_cli, "_import_verify_all", lambda root: fake)
    custom = tmp_path / "custom.json"
    args = argparse.Namespace(directory=tmp_path, json=False, write_preflight=False, preflight_out=custom)
    assert verify_cli.cmd_verify_all(args) == 1
    assert written["path"] == custom


def test_register_verify_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    verify_cli.register_verify_subparser(sub)
    args = parser.parse_args(["verify", "all"])
    assert args.func is verify_cli.cmd_verify_all


# ---------------------------------------------------------------------------
# drift_cli
# ---------------------------------------------------------------------------


def test_import_check_drift_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        drift_cli._import_check_drift(tmp_path)


def test_cmd_drift_validate_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path, profile=None, json=False)
    assert drift_cli.cmd_drift_validate(args) == 1


def test_cmd_drift_validate_json_real() -> None:
    args = argparse.Namespace(directory=REPO_ROOT, profile="kit-dev", json=True)
    assert drift_cli.cmd_drift_validate(args) == 0


def test_cmd_drift_validate_text_real() -> None:
    args = argparse.Namespace(directory=REPO_ROOT, profile="kit-dev", json=False)
    assert drift_cli.cmd_drift_validate(args) == 0


def test_register_drift_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    drift_cli.register_drift_subparser(sub)
    args = parser.parse_args(["drift", "validate"])
    assert args.func is drift_cli.cmd_drift_validate
    assert args.profile is None


# ---------------------------------------------------------------------------
# integrate_cli
# ---------------------------------------------------------------------------


def test_import_validate_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        integrate_cli._import_validate(tmp_path)


def test_cmd_integrate_validate_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path, json=False)
    assert integrate_cli.cmd_integrate_validate(args) == 1


def test_cmd_integrate_validate_json_real() -> None:
    args = argparse.Namespace(directory=REPO_ROOT, json=True)
    code = integrate_cli.cmd_integrate_validate(args)
    assert code in (0, 1)


def test_cmd_integrate_validate_text_real() -> None:
    args = argparse.Namespace(directory=REPO_ROOT, json=False)
    code = integrate_cli.cmd_integrate_validate(args)
    assert code in (0, 1)


def test_register_integrate_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    integrate_cli.register_integrate_subparser(sub)
    args = parser.parse_args(["integrate", "validate"])
    assert args.func is integrate_cli.cmd_integrate_validate


# ---------------------------------------------------------------------------
# contributors_cli
# ---------------------------------------------------------------------------


def test_import_user_settings_missing(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        contributors_cli._import_user_settings(tmp_path)


def test_cmd_contributors_validate_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path, check_mcp=False)
    assert contributors_cli.cmd_contributors_validate(args) == 1


def test_cmd_contributors_validate_errors(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(
        validate_github_collaboration=lambda root: ["bad owner"],
        validate_mcp_agents_worksheet=lambda root: ["mcp issue"],
    )
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path, check_mcp=True)
    assert contributors_cli.cmd_contributors_validate(args) == 1


def test_cmd_contributors_validate_pass(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(validate_github_collaboration=lambda root: [])
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path, check_mcp=False)
    assert contributors_cli.cmd_contributors_validate(args) == 0


def test_cmd_contributors_show_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_show(args) == 1


def test_cmd_contributors_show_missing_config(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(load_github_collaboration=lambda root: {}, GITHUB_COLLAB_REL="settings.yaml")
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_show(args) == 1


def test_cmd_contributors_show_with_session_agents(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(
        load_github_collaboration=lambda root: {"owner": {}},
        resolve_default_actor=lambda root: "Jane Doe",
        resolve_github_user=lambda root: "@jane",
        pipeline_agents_string=lambda cfg, name: f"agents-for-{name}",
        collect_session_agents=lambda root: ["implementer"],
        resolve_agents_for_pr=lambda **kw: "implementer",
        github_collaboration_path=lambda root: tmp_path / "settings.yaml",
    )
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_show(args) == 0


def test_cmd_contributors_show_no_session_agents(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(
        load_github_collaboration=lambda root: {"owner": {}},
        resolve_default_actor=lambda root: None,
        resolve_github_user=lambda root: "@jane",
        pipeline_agents_string=lambda cfg, name: "",
        collect_session_agents=lambda root: [],
        github_collaboration_path=lambda root: tmp_path / "settings.yaml",
    )
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_show(args) == 0


def test_cmd_contributors_commit_trailers_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_commit_trailers(args) == 1


def test_cmd_contributors_commit_trailers_render_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(render_commit_trailers=lambda root: (_ for _ in ()).throw(ValueError("bad")))
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_commit_trailers(args) == 1


def test_cmd_contributors_commit_trailers_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(render_commit_trailers=lambda root: "Author: X\nGitHub-User: @x")
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(directory=tmp_path)
    assert contributors_cli.cmd_contributors_commit_trailers(args) == 0


def test_cmd_contributors_pr_body_import_fails(tmp_path: Path) -> None:
    args = argparse.Namespace(
        directory=tmp_path, summary=None, test_plan=None, pipeline="default", no_agents_from_session=False
    )
    assert contributors_cli.cmd_contributors_pr_body(args) == 1


def test_cmd_contributors_pr_body_success_with_summary(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(render_pr_body=lambda root, **kw: "PR body")
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(
        directory=tmp_path,
        summary=["- did a thing"],
        test_plan=["- [ ] ran tests"],
        pipeline="default",
        no_agents_from_session=True,
    )
    assert contributors_cli.cmd_contributors_pr_body(args) == 0


def test_cmd_contributors_pr_body_render_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    fake = SimpleNamespace(render_pr_body=lambda root, **kw: (_ for _ in ()).throw(FileNotFoundError("no cfg")))
    monkeypatch.setattr(contributors_cli, "_import_user_settings", lambda root: fake)
    args = argparse.Namespace(
        directory=tmp_path, summary=None, test_plan=None, pipeline="default", no_agents_from_session=False
    )
    assert contributors_cli.cmd_contributors_pr_body(args) == 1


def test_register_contributors_subparser() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command")
    contributors_cli.register_contributors_subparser(sub)

    v = parser.parse_args(["contributors", "validate"])
    assert v.func is contributors_cli.cmd_contributors_validate

    s = parser.parse_args(["contributors", "show"])
    assert s.func is contributors_cli.cmd_contributors_show

    t = parser.parse_args(["contributors", "commit-trailers"])
    assert t.func is contributors_cli.cmd_contributors_commit_trailers

    p = parser.parse_args(["contributors", "pr-body"])
    assert p.func is contributors_cli.cmd_contributors_pr_body
    assert p.pipeline == "default"
