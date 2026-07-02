"""
File: server.py
Path: .ai_infra/mcp_servers/workflow_mcp/server.py
Role: MCP server (stdio) — P0 tools wrap `.ai_infra/scripts/pr/*` and read trackers/agents.
Used By:
 - workflow_mcp/__main__.py
Depends On:
 - mcp.server.fastmcp
 - workflow_mcp/gates.py, runner.py, workspace.py
Notes:
 - Does not reimplement GATES; full prepare uses prepare.py subprocess.
"""

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stdout
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from workflow_mcp.gates import load_gates
from workflow_mcp.resources import (
    build_inventory,
    read_agent,
    read_mcp_connection_guide,
    read_mcp_registry,
    read_pr_artifact,
    read_project_config,
    read_skill,
    read_tracker,
)
from workflow_mcp.runner import run_cmd, run_script
from workflow_mcp.workspace import workspace_root

mcp = FastMCP("workflow-kit")

_TRACKER_NAMES = frozenset(
    {
        "session-pointer",
        "plan",
        "work-tracker",
        "change-index",
        "test-plan",
        "test-index",
        "coverage-index",
        "architecture",
    }
)


def _tracker_path(name: str, root: Path) -> Path:
    if name not in _TRACKER_NAMES:
        allowed = ", ".join(sorted(_TRACKER_NAMES))
        raise ValueError(f"Unknown tracker '{name}'. Allowed: {allowed}")
    return root / ".local" / "index-and-planning" / "current" / f"{name}.md"


@mcp.tool()
def workflow_run_prepare(pr: str, actor: str, agents: str, skip_gates: bool = False) -> str:
    """Run `.ai_infra/scripts/pr/prepare.py` (all GATES unless skip_gates)."""
    root = workspace_root()
    args = ["--pr", pr, "--actor", actor, "--agents", agents]
    if skip_gates:
        args.append("--skip-gates")
    code, out = run_script("scripts/pr/prepare.py", args, root)
    return f"exit={code}\n{out}"


@mcp.tool()
def workflow_run_review(pr: str, actor: str, agents: str = "review-pr") -> str:
    """Run `.ai_infra/scripts/pr/review.py` to stamp review.md."""
    root = workspace_root()
    code, out = run_script(
        "scripts/pr/review.py",
        ["--pr", pr, "--actor", actor, "--agents", agents],
        root,
    )
    return f"exit={code}\n{out}"


@mcp.tool()
def workflow_run_merge_check(
    pr: str,
    actor: str,
    agents: str = "review-pr | prepare-pr | merge-pr",
    arch_impacting: bool = False,
) -> str:
    """Run `.ai_infra/scripts/pr/merge.py` --check-only."""
    root = workspace_root()
    args = ["--pr", pr, "--actor", actor, "--agents", agents, "--check-only"]
    if arch_impacting:
        args.append("--arch-impacting")
    code, out = run_script("scripts/pr/merge.py", args, root)
    return f"exit={code}\n{out}"


@mcp.tool()
def workflow_run_gate(index: int) -> str:
    """Run a single gate from prepare.py GATES by zero-based index."""
    root = workspace_root()
    gates = load_gates(root)
    if index < 0 or index >= len(gates):
        return f"exit=1\nInvalid gate index {index}; GATES has {len(gates)} entries"
    code, out = run_cmd(gates[index], root)
    return f"exit={code}\n{out}"


@mcp.tool()
def workflow_check_governance() -> str:
    """Run scripts/architecture/check_governance_consistency.py."""
    root = workspace_root()
    code, out = run_script("scripts/architecture/check_governance_consistency.py", [], root)
    return f"exit={code}\n{out}"


@mcp.tool()
def workflow_list_agents() -> str:
    """List agent ids from .cursor/agents/*.md."""
    root = workspace_root()
    agents_dir = root / ".cursor" / "agents"
    if not agents_dir.is_dir():
        return "No .cursor/agents directory found"
    names = sorted(p.stem for p in agents_dir.glob("*.md"))
    return "\n".join(names) if names else "(no agents)"


@mcp.tool()
def workflow_get_tracker(name: str) -> str:
    """Read .local/index-and-planning/current/{name}.md."""
    root = workspace_root()
    path = _tracker_path(name, root)
    if not path.is_file():
        return f"Tracker not found: {path}"
    return path.read_text(encoding="utf-8")


@mcp.tool()
def workflow_gate_count() -> str:
    """Return number of gates in prepare.py GATES (no command list in output)."""
    return str(len(load_gates()))


@mcp.tool()
def workflow_get_project_config() -> str:
    """Read project.config.yaml or return example template paths when absent."""
    return read_project_config(workspace_root())


@mcp.tool()
def workflow_list_mcp_registry() -> str:
    """Return MCP registry YAML as JSON (kit + external servers)."""
    return read_mcp_registry(workspace_root())


@mcp.tool()
def workflow_mcp_connection_guide() -> str:
    """Return connect-external-mcp operations doc for users and agents."""
    return read_mcp_connection_guide(workspace_root())


def _user_settings_module(root: Path):
    import importlib.util
    import sys

    script = root / ".ai_infra" / "scripts" / "pr" / "user_settings.py"
    if not script.is_file():
        raise FileNotFoundError(f"missing {script}")
    pr_dir = str(script.parent)
    if pr_dir not in sys.path:
        sys.path.insert(0, pr_dir)
    spec = importlib.util.spec_from_file_location("workflow_kit_user_settings", script)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@mcp.tool()
def workflow_render_commit_trailers() -> str:
    """Render git commit trailer block from .local/user_settings/github.collaboration.yaml."""
    root = workspace_root()
    try:
        us = _user_settings_module(root)
        return us.render_commit_trailers(root)
    except (FileNotFoundError, ValueError) as exc:
        return f"error: {exc}"


@mcp.tool()
def workflow_render_pr_body(pipeline: str = "default", agents_from_session: bool = True) -> str:
    """Render gh pr create body; merges change-index/session agents with PR pipeline by default."""
    root = workspace_root()
    try:
        us = _user_settings_module(root)
        return us.render_pr_body(root, pipeline=pipeline, agents_from_session=agents_from_session)
    except (FileNotFoundError, ValueError) as exc:
        return f"error: {exc}"


@mcp.tool()
def workflow_list_session_agents() -> str:
    """List implementation agents recorded in change-index.md and session-pointer.md."""
    root = workspace_root()
    try:
        us = _user_settings_module(root)
        agents = us.collect_session_agents(root)
        if not agents:
            return "(no session agents found in trackers)"
        merged = us.resolve_agents_for_pr(
            root=root,
            cfg=us.load_github_collaboration(root),
            pipeline="default",
            agents_from_session=True,
        )
        return f"session: {' | '.join(agents)}\nmerged: {merged}"
    except (FileNotFoundError, ValueError) as exc:
        return f"error: {exc}"


@mcp.tool()
def workflow_integrate_validate() -> str:
    """Run integrate validate (agent/registry/pipeline parity and user_settings schemas)."""
    root = workspace_root()
    integration_dir = root / ".ai_infra" / "scripts" / "integration"
    if not integration_dir.is_dir():
        return "FAIL: missing .ai_infra/scripts/integration"
    import sys

    integration_str = str(integration_dir)
    if integration_str not in sys.path:
        sys.path.insert(0, integration_str)
    import validate

    results = validate.run_checks(root)
    report = validate.format_report(results)
    code = validate.exit_code_for(results)
    return f"exit={code}\n{report}"


@mcp.tool()
def workflow_drift_validate() -> str:
    """Run drift validate (plan/tracker/session coherence and handoff parity)."""
    root = workspace_root()
    workflow_dir = root / ".ai_infra" / "scripts" / "workflow"
    if not workflow_dir.is_dir():
        return "FAIL: missing .ai_infra/scripts/workflow"
    import sys

    workflow_str = str(workflow_dir)
    if workflow_str not in sys.path:
        sys.path.insert(0, workflow_str)
    import check_drift

    results = check_drift.run_checks(root)
    profile = check_drift.resolve_profile(root, None)
    report = check_drift.format_report(results, profile=profile)
    code = check_drift.exit_code_for(results)
    return f"exit={code}\nprofile={profile}\n{report}"


@mcp.tool()
def workflow_activate(force: bool = False) -> str:
    """Ensure all three planes are installed (cursor_workflow activate)."""
    root = workspace_root()
    activate_pkg = root / ".ai_infra" / "install" / "cursor_workflow"
    if not (activate_pkg / "activate_cli.py").is_file():
        return "FAIL: missing activate_cli — run workflow-activate skill or install kit first"
    import sys

    pkg = str(activate_pkg)
    if pkg not in sys.path:
        sys.path.insert(0, pkg)
    import activate_cli

    args = argparse.Namespace(
        directory=root,
        source=None,
        profile="with_mcp",
        with_venv=True,
        with_mcp_json=True,
        verify=True,
        force=force,
        allow_settings_pending=True,
    )
    buffer = io.StringIO()
    with redirect_stdout(buffer):
        code = activate_cli.cmd_activate(args)
    return f"exit={code}\n{buffer.getvalue()}"


@mcp.tool()
def workflow_doc_facts_validate() -> str:
    """Run doc validate (canonical README/AGENTS/status vs repo facts)."""
    root = workspace_root()
    arch_dir = root / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        return "FAIL: missing .ai_infra/scripts/architecture"
    import sys

    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import check_doc_facts

    results = check_doc_facts.run_checks(root)
    report = check_doc_facts.format_report(results)
    code = check_doc_facts.exit_code_for(results)
    return f"exit={code}\n{report}"


@mcp.tool()
def workflow_verify_all() -> str:
    """Run maintainer verify-all matrix (sync-plugin, gates, drift, integrate, check-plugin, health)."""
    root = workspace_root()
    arch_dir = root / ".ai_infra" / "scripts" / "architecture"
    if not arch_dir.is_dir():
        return "FAIL: missing .ai_infra/scripts/architecture"
    import sys

    arch_str = str(arch_dir)
    if arch_str not in sys.path:
        sys.path.insert(0, arch_str)
    import verify_all

    results = verify_all.run_verify_all(root, sys.executable)
    report = verify_all.format_report(results)
    code = verify_all.exit_code_for(results)
    return f"exit={code}\n{report}"


@mcp.tool()
def workflow_contributors_validate(check_mcp: bool = False) -> str:
    """Validate .local/user_settings/github.collaboration.yaml (optional MCP worksheet)."""
    root = workspace_root()
    try:
        us = _user_settings_module(root)
    except (FileNotFoundError, ValueError) as exc:
        return f"FAIL: {exc}"
    errors = us.validate_github_collaboration(root)
    if check_mcp:
        errors.extend(us.validate_mcp_agents_worksheet(root))
    if errors:
        return "FAIL\n" + "\n".join(f"- {e}" for e in errors)
    return "PASS"


# --- P1 resources (workflow:// URIs) ---


@mcp.resource("workflow://inventory", mime_type="application/json")
def resource_inventory() -> str:
    """Live inventory: agent ids, skill ids, gate_count (no gate commands)."""
    return build_inventory(workspace_root())


@mcp.resource("workflow://agents/{agent_id}")
def resource_agent(agent_id: str) -> str:
    """Agent prompt from .cursor/agents/{agent_id}.md."""
    try:
        return read_agent(workspace_root(), agent_id)
    except FileNotFoundError as exc:
        return f"not found: {exc}"


@mcp.resource("workflow://skills/{skill_id}")
def resource_skill(skill_id: str) -> str:
    """Skill body from .cursor/skills or .agents/skills."""
    try:
        return read_skill(workspace_root(), skill_id)
    except FileNotFoundError as exc:
        return f"not found: {exc}"


@mcp.resource("workflow://artifacts/pr/{phase}")
def resource_pr_artifact(phase: str) -> str:
    """PR artifact: phase = review | prep | prepare | merge."""
    try:
        return read_pr_artifact(workspace_root(), phase)
    except (FileNotFoundError, ValueError) as exc:
        return f"error: {exc}"


@mcp.resource("workflow://trackers/{name}")
def resource_tracker(name: str) -> str:
    """Tracker markdown from .local/index-and-planning/current/{name}.md."""
    try:
        return read_tracker(workspace_root(), name)
    except (FileNotFoundError, ValueError) as exc:
        return f"error: {exc}"


@mcp.resource("workflow://mcp/registry")
def resource_mcp_registry() -> str:
    """JSON MCP registry for programmatic agent reads."""
    return read_mcp_registry(workspace_root())
