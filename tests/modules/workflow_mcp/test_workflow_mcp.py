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
    assert len(gates) == 4
    assert gates[0][-1].endswith("check_testing_artifacts.py")
    assert gates[1][-2:] == ["pytest", "-q"]
    joined = " ".join(" ".join(cmd) for cmd in gates)
    assert "drift" in joined
    assert "check_doc_facts" in joined


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

    assert workflow_gate_count() == "4"


def test_build_inventory() -> None:
    from workflow_mcp.resources import build_inventory

    raw = build_inventory(REPO_ROOT)
    assert "implementer" in raw
    assert '"gate_count": 4' in raw or '"gate_count": 4,' in raw


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


def test_workflow_doc_facts_validate() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)
    from workflow_mcp.server import workflow_doc_facts_validate

    text = workflow_doc_facts_validate()
    assert "exit=0" in text
    assert "DOC-001" in text


def _env_root() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)


def _mock_run_script(monkeypatch: pytest.MonkeyPatch, *, code: int = 0, out: str = "ok") -> None:
    def fake_run_script(relative: str, args: list[str], cwd: Path, **kwargs: object) -> tuple[int, str]:
        return code, out

    monkeypatch.setattr("workflow_mcp.server.run_script", fake_run_script)


def test_workflow_run_gate_index_zero() -> None:
    _env_root()
    from workflow_mcp.server import workflow_run_gate

    text = workflow_run_gate(0)
    assert text.startswith("exit=")
    assert "exit=0" in text


def test_workflow_check_governance() -> None:
    _env_root()
    from workflow_mcp.server import workflow_check_governance

    text = workflow_check_governance()
    assert text.startswith("exit=")
    assert "exit=0" in text


def test_workflow_run_prepare_skip_gates_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    _mock_run_script(monkeypatch)
    from workflow_mcp.server import workflow_run_prepare

    text = workflow_run_prepare(
        pr="https://github.com/example/repo/pull/1",
        actor="Test User",
        agents="review-pr",
        skip_gates=True,
    )
    assert text == "exit=0\nok"


def test_workflow_run_review_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    _mock_run_script(monkeypatch)
    from workflow_mcp.server import workflow_run_review

    text = workflow_run_review(
        pr="https://github.com/example/repo/pull/1",
        actor="Test User",
    )
    assert text == "exit=0\nok"


def test_workflow_run_merge_check_smoke(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    _mock_run_script(monkeypatch)
    from workflow_mcp.server import workflow_run_merge_check

    text = workflow_run_merge_check(
        pr="https://github.com/example/repo/pull/1",
        actor="Test User",
    )
    assert text == "exit=0\nok"


def test_workflow_render_commit_trailers() -> None:
    _env_root()
    from workflow_mcp.server import workflow_render_commit_trailers

    text = workflow_render_commit_trailers()
    assert "Author:" in text or text.startswith("error:")


def test_workflow_render_pr_body() -> None:
    _env_root()
    from workflow_mcp.server import workflow_render_pr_body

    text = workflow_render_pr_body(pipeline="default", agents_from_session=False)
    assert "## Summary" in text or text.startswith("error:")


def test_workflow_list_session_agents() -> None:
    _env_root()
    from workflow_mcp.server import workflow_list_session_agents

    text = workflow_list_session_agents()
    assert "session:" in text or text.startswith("error:") or text.startswith("(no session")


def test_workflow_integrate_validate() -> None:
    _env_root()
    from workflow_mcp.server import workflow_integrate_validate

    text = workflow_integrate_validate()
    assert text.startswith("exit=0")
    assert "INT-001" in text


def test_workflow_drift_validate() -> None:
    _env_root()
    from workflow_mcp.server import workflow_drift_validate

    text = workflow_drift_validate()
    assert text.startswith("exit=0")
    assert "DRIFT-" in text


def test_workflow_verify_all(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    arch_dir = REPO_ROOT / ".ai_infra" / "scripts" / "architecture"
    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import verify_all

    class _Result:
        def __init__(self, name: str, code: int) -> None:
            self.name = name
            self.code = code

    def fake_run_verify_all(root: Path, python: str) -> list:
        return [_Result("gates", 0), _Result("health", 0)]

    monkeypatch.setattr(verify_all, "run_verify_all", fake_run_verify_all)
    monkeypatch.setattr(verify_all, "format_report", lambda results: "summary: failed=0 total=2")
    monkeypatch.setattr(verify_all, "exit_code_for", lambda results: 0)

    from workflow_mcp.server import workflow_verify_all

    text = workflow_verify_all()
    assert text.startswith("exit=0")
    assert "summary:" in text


def test_workflow_contributors_validate() -> None:
    _env_root()
    from workflow_mcp.server import workflow_contributors_validate

    text = workflow_contributors_validate()
    assert text == "PASS" or text.startswith("FAIL")


def test_workflow_activate_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    activate_pkg = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"
    pkg = str(activate_pkg)
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    import activate_cli

    monkeypatch.setattr(activate_cli, "cmd_activate", lambda args: 0)

    from workflow_mcp.server import workflow_activate

    text = workflow_activate(force=False)
    assert text.startswith("exit=0")


@pytest.mark.live
def test_workflow_mcp_stdio_initialize_smoke() -> None:
    """Opt-in: spawn workflow_mcp stdio server and verify initialize handshake."""
    pytest.importorskip("mcp")
    import json
    import os
    import subprocess
    import threading

    env = {**os.environ, "WORKFLOW_KIT_ROOT": str(REPO_ROOT)}
    proc = subprocess.Popen(
        [sys.executable, "-m", "workflow_mcp"],
        cwd=REPO_ROOT,
        env=env,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    assert proc.stdin is not None and proc.stdout is not None

    init = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest-live", "version": "0"},
        },
    }
    proc.stdin.write(json.dumps(init) + "\n")
    proc.stdin.flush()

    response: dict | None = None

    def _read_stdout() -> None:
        nonlocal response
        line = proc.stdout.readline()
        if line.strip():
            response = json.loads(line)

    reader = threading.Thread(target=_read_stdout, daemon=True)
    reader.start()
    reader.join(timeout=5.0)
    proc.terminate()
    try:
        proc.wait(timeout=2.0)
    except subprocess.TimeoutExpired:
        proc.kill()

    assert response is not None, proc.stderr.read() if proc.stderr else ""
    assert response.get("id") == 1
    assert "result" in response
    assert response["result"].get("serverInfo", {}).get("name") == "workflow-kit"
