"""
File: test_workflow_mcp_full.py
Path: tests/modules/workflow_mcp/test_workflow_mcp_full.py
Role: Full-branch coverage for workflow_mcp server tools, resources, and error paths
      not exercised by test_workflow_mcp.py's happy-path smoke tests.
Used By:
 - pytest
Depends On:
 - .ai_infra/mcp_servers/workflow_mcp/*
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def _env_root(root: Path = REPO_ROOT) -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(root)


def test_workflow_run_gate_invalid_index() -> None:
    _env_root()
    from workflow_mcp.server import workflow_run_gate

    text = workflow_run_gate(999)
    assert text.startswith("exit=1")
    assert "Invalid gate index" in text


def test_workflow_run_merge_check_arch_impacting(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()

    captured: dict[str, list[str]] = {}

    def fake_run_script(relative: str, args: list[str], cwd: Path, **kwargs: object):
        captured["args"] = args
        return 0, "ok"

    monkeypatch.setattr("workflow_mcp.server.run_script", fake_run_script)
    from workflow_mcp.server import workflow_run_merge_check

    workflow_run_merge_check(pr="https://x/pull/1", actor="A", arch_impacting=True)
    assert "--arch-impacting" in captured["args"]


def test_workflow_list_agents_no_dir(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_list_agents

    assert workflow_list_agents() == "No .cursor/agents directory found"
    _env_root()


def test_workflow_list_agents_empty_dir(tmp_path: Path) -> None:
    (tmp_path / ".cursor" / "agents").mkdir(parents=True)
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_list_agents

    assert workflow_list_agents() == "(no agents)"
    _env_root()


def test_workflow_get_tracker_unknown_name() -> None:
    _env_root()
    from workflow_mcp.server import workflow_get_tracker

    with pytest.raises(ValueError, match="Unknown tracker"):
        workflow_get_tracker("not-a-real-tracker")


def test_workflow_get_tracker_not_found(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_get_tracker

    text = workflow_get_tracker("plan")
    assert text.startswith("Tracker not found:")
    _env_root()


def test_workflow_integrate_validate_missing_dir(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_integrate_validate

    assert workflow_integrate_validate() == "FAIL: missing .ai_infra/scripts/integration"
    _env_root()


def test_workflow_drift_validate_missing_dir(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_drift_validate

    assert workflow_drift_validate() == "FAIL: missing .ai_infra/scripts/workflow"
    _env_root()


def test_workflow_doc_facts_validate_missing_dir(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_doc_facts_validate

    assert workflow_doc_facts_validate() == "FAIL: missing .ai_infra/scripts/architecture"
    _env_root()


def test_workflow_verify_all_missing_dir(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_verify_all

    assert workflow_verify_all() == "FAIL: missing .ai_infra/scripts/architecture"
    _env_root()


def test_workflow_activate_missing_activate_cli(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_activate

    text = workflow_activate()
    assert text.startswith("FAIL: missing activate_cli")
    _env_root()


def test_user_settings_module_missing_script(tmp_path: Path) -> None:
    from workflow_mcp.server import _user_settings_module

    with pytest.raises(FileNotFoundError):
        _user_settings_module(tmp_path)


def test_workflow_render_commit_trailers_error(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_render_commit_trailers

    assert workflow_render_commit_trailers().startswith("error:")
    _env_root()


def test_workflow_render_pr_body_error(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_render_pr_body

    assert workflow_render_pr_body().startswith("error:")
    _env_root()


def test_workflow_list_session_agents_error(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_list_session_agents

    assert workflow_list_session_agents().startswith("error:")
    _env_root()


def test_workflow_list_session_agents_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    from workflow_mcp import server

    fake_us = type(
        "FakeUS",
        (),
        {
            "collect_session_agents": staticmethod(lambda root: []),
        },
    )()
    monkeypatch.setattr(server, "_user_settings_module", lambda root: fake_us)
    text = server.workflow_list_session_agents()
    assert text == "(no session agents found in trackers)"


def test_workflow_contributors_validate_fail(tmp_path: Path) -> None:
    _env_root(tmp_path)
    from workflow_mcp.server import workflow_contributors_validate

    assert workflow_contributors_validate().startswith("FAIL:")
    _env_root()


def test_workflow_contributors_validate_with_errors_and_check_mcp(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    from workflow_mcp import server

    fake_us = type(
        "FakeUS",
        (),
        {
            "validate_github_collaboration": staticmethod(lambda root: ["bad owner"]),
            "validate_mcp_agents_worksheet": staticmethod(lambda root: ["bad mcp"]),
        },
    )()
    monkeypatch.setattr(server, "_user_settings_module", lambda root: fake_us)
    text = server.workflow_contributors_validate(check_mcp=True)
    assert text.startswith("FAIL")
    assert "bad owner" in text
    assert "bad mcp" in text


# ---------------------------------------------------------------------------
# @mcp.resource wrappers (error branches)
# ---------------------------------------------------------------------------


def test_resource_agent_not_found() -> None:
    _env_root()
    from workflow_mcp.server import resource_agent

    text = resource_agent("does-not-exist-agent")
    assert text.startswith("not found:")


def test_resource_skill_not_found() -> None:
    _env_root()
    from workflow_mcp.server import resource_skill

    text = resource_skill("does-not-exist-skill")
    assert text.startswith("not found:")


def test_resource_pr_artifact_error() -> None:
    _env_root()
    from workflow_mcp.server import resource_pr_artifact

    text = resource_pr_artifact("bogus-phase")
    assert text.startswith("error:")


def test_resource_tracker_error() -> None:
    _env_root()
    from workflow_mcp.server import resource_tracker

    text = resource_tracker("bogus-tracker-name")
    assert text.startswith("error:")


def test_resource_mcp_registry() -> None:
    _env_root()
    from workflow_mcp.server import resource_mcp_registry

    text = resource_mcp_registry()
    assert "workflow-kit" in text
