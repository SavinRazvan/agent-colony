"""
File: test_workflow_mcp.py
Path: tests/modules/workflow_mcp/test_workflow_mcp.py
Role: Tests for workflow_mcp skeleton (gates, workspace, list agents).
Used By:
 - pytest
Depends On:
 - workflow_mcp/*
Notes:
 - Does not start stdio MCP server in tests.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_workspace_root_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("WORKFLOW_KIT_ROOT", str(REPO_ROOT))
    from workflow_mcp.workspace import workspace_root

    assert workspace_root() == REPO_ROOT.resolve()


def test_load_gates_matches_prepare() -> None:
    from workflow_mcp.gates import load_gates

    gates = load_gates(REPO_ROOT)
    assert len(gates) == 2
    assert gates[0][-1].endswith("check_testing_artifacts.py")
    assert gates[1][-2:] == ["pytest", "-q"]


def test_list_agents_tool() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_list_agents

    result = workflow_list_agents()
    assert "implementer" in result
    assert "workflow-intelligence-mapper" not in result


def test_get_tracker_session_pointer() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_get_tracker

    text = workflow_get_tracker("session-pointer")
    assert "Next read" in text


def test_gate_count() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_gate_count

    assert workflow_gate_count() == "2"


def test_build_inventory() -> None:
    from workflow_mcp.resources import build_inventory

    raw = build_inventory(REPO_ROOT)
    assert "implementer" in raw
    assert '"gate_count": 2' in raw or '"gate_count": 2,' in raw


def test_read_agent() -> None:
    from workflow_mcp.resources import read_agent

    body = read_agent(REPO_ROOT, "implementer")
    assert "Implementer" in body


def test_read_skill() -> None:
    from workflow_mcp.resources import read_skill

    body = read_skill(REPO_ROOT, "implementation-execution-loop")
    assert "implementation execution loop" in body.lower()


def test_read_pr_artifact_invalid_phase() -> None:
    from workflow_mcp.resources import read_pr_artifact

    with pytest.raises(ValueError, match="Unknown PR phase"):
        read_pr_artifact(REPO_ROOT, "bogus")


def test_run_script_resolves_ai_infra_layout() -> None:
    from workflow_mcp.runner import resolve_script_path

    prepare = resolve_script_path(REPO_ROOT, "scripts/pr/prepare.py")
    assert prepare is not None
    assert prepare.is_file()
    assert prepare == (REPO_ROOT / ".ai_infra" / "scripts" / "pr" / "prepare.py").resolve()


def test_run_cmd_times_out() -> None:
    from workflow_mcp.runner import run_cmd

    code, out = run_cmd(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        REPO_ROOT,
        timeout_s=0.2,
    )
    assert code == 124
    assert "timeout after 0.2s" in out


def test_resource_inventory_fn() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import resource_inventory

    assert "implementer" in resource_inventory()


def test_workflow_get_project_config() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_get_project_config

    text = workflow_get_project_config()
    assert "project:" in text or "project.config" in text


def test_workflow_list_mcp_registry() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_list_mcp_registry

    text = workflow_list_mcp_registry()
    assert "workflow-kit" in text


def test_workflow_mcp_connection_guide() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_mcp_connection_guide

    text = workflow_mcp_connection_guide()
    assert "external MCP" in text or "Connect external" in text
