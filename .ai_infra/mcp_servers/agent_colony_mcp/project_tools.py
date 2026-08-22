"""
File: project_tools.py
Path: .ai_infra/mcp_servers/agent_colony_mcp/project_tools.py
Role: Thin MCP adapters for board Pattern A — wrap project_cli / doc_cli only.
Used By:
 - agent_colony_mcp/server.py
Depends On:
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/doc_cli.py
Notes:
 - ADR-012: no second GraphQL client; envelope JSON for agents.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any


EXIT_QUEUED = 6


def _install_pkg(root: Path) -> Path:
    return root / ".ai_infra" / "install" / "agent_colony"


def _ensure_install_path(root: Path) -> Path:
    pkg = _install_pkg(root)
    if not pkg.is_dir():
        raise FileNotFoundError(f"missing install package: {pkg}")
    pkg_str = str(pkg)
    if pkg_str not in sys.path:
        sys.path.insert(0, pkg_str)
    return pkg


def format_envelope(
    exit_code: int,
    summary: str,
    next_recommended_tool: str | None,
    detail: str | None = None,
) -> str:
    """JSON envelope: exit_code, summary, next_recommended_tool, detail."""
    summary_text = summary.strip() if summary else ""
    if exit_code == EXIT_QUEUED:
        next_recommended_tool = "workflow_project_outbox_status"
        # Always include do-not-retry guidance (agents must not hammer GraphQL).
        base = summary_text or "EXIT_QUEUED"
        if "do not retry" not in base.lower():
            summary_text = f"{base} — do not retry; flush after quota recovers"
        else:
            summary_text = base
    payload: dict[str, Any] = {
        "exit_code": exit_code,
        "summary": summary_text,
        "next_recommended_tool": next_recommended_tool,
        "detail": detail,
    }
    return json.dumps(payload, ensure_ascii=False)


def _run_cmd(
    root: Path,
    cmd_fn: Any,
    args: argparse.Namespace,
    *,
    next_ok: str | None,
) -> str:
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        code = int(cmd_fn(args))
    out = buf_out.getvalue().strip()
    err = buf_err.getvalue().strip()
    summary = out.splitlines()[0] if out else (err.splitlines()[0] if err else f"exit={code}")
    detail: str | None = None
    if code not in (0, EXIT_QUEUED):
        detail = (out + ("\n" + err if err else "")).strip() or None
    elif err and code == 0:
        detail = err
    next_tool = next_ok if code == 0 else None
    return format_envelope(code, summary, next_tool, detail)


def run_project_entry(
    root: Path,
    *,
    digest: bool = True,
    also_ready: bool = False,
    force_live: bool = False,
) -> str:
    _ensure_install_path(root)
    import project_cli as pc

    args = argparse.Namespace(
        directory=root,
        digest=digest,
        json=False,
        force_live=force_live,
        limit=None,
    )
    next_ok = "workflow_project_claim"
    return _run_cmd(root, pc.cmd_entry, args, next_ok=next_ok)


def run_project_claim(root: Path, *, agent: str, text: str = "claimed") -> str:
    _ensure_install_path(root)
    import project_cli as pc

    args = argparse.Namespace(
        directory=root,
        last=True,
        id="",
        agent=agent,
        text=text,
        limit=200,
    )
    return _run_cmd(root, pc.cmd_claim, args, next_ok="workflow_project_handoff")


def run_project_handoff(
    root: Path,
    *,
    agent: str,
    next_agent: str,
    to: str = "",
    text: str = "",
) -> str:
    _ensure_install_path(root)
    import project_cli as pc

    args = argparse.Namespace(
        directory=root,
        last=True,
        id="",
        agent=agent,
        next=next_agent,
        to=to or "",
        text=text or "",
        limit=200,
    )
    return _run_cmd(root, pc.cmd_handoff, args, next_ok="workflow_session_entry")


def run_project_outbox_status(root: Path) -> str:
    _ensure_install_path(root)
    import project_cli as pc

    args = argparse.Namespace(directory=root)
    return _run_cmd(
        root,
        pc.cmd_outbox_status,
        args,
        next_ok="workflow_project_entry",
    )


def _change_index_first_row(root: Path) -> str | None:
    path = root / ".local" / "index-and-planning" / "current" / "change-index.md"
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if not cells:
            continue
        # Skip markdown separator and header rows.
        if all(set(c) <= {"-", ":"} and c for c in cells):
            continue
        if cells[0].lower() in {"date", "when", "day"}:
            continue
        return " · ".join(cells[:4])
    return None


def run_session_entry(root: Path, *, agent: str | None = None) -> str:
    """Composite: entry digest + last item + change-index row."""
    _ensure_install_path(root)
    import project_cli as pc

    entry_raw = run_project_entry(root, digest=True)
    entry = json.loads(entry_raw)
    last_id = ""
    buf = io.StringIO()
    with redirect_stdout(buf), redirect_stderr(io.StringIO()):
        last_code = int(pc.cmd_last(argparse.Namespace(directory=root)))
    if last_code == 0:
        last_id = buf.getvalue().strip()
    ci_row = _change_index_first_row(root)
    parts = [entry.get("summary") or ""]
    if last_id:
        parts.append(f"last={last_id}")
    if ci_row:
        parts.append(f"change-index={ci_row}")
    if agent:
        parts.append(f"agent={agent}")
    summary = " · ".join(p for p in parts if p)
    next_tool = "workflow_project_claim"
    if entry.get("exit_code") == EXIT_QUEUED:
        return format_envelope(
            EXIT_QUEUED,
            entry.get("summary") or "",
            "workflow_project_outbox_status",
            entry.get("detail"),
        )
    if entry.get("exit_code") not in (0, None):
        return format_envelope(
            int(entry.get("exit_code") or 1),
            summary or entry.get("summary") or "session entry failed",
            None,
            entry.get("detail"),
        )
    return format_envelope(0, summary, next_tool, None)


def run_doc_skill_section(root: Path, *, skill: str, section: str) -> str:
    _ensure_install_path(root)
    import doc_cli

    args = argparse.Namespace(
        directory=root,
        skill=skill,
        section=section,
        json=False,
    )
    buf_out = io.StringIO()
    buf_err = io.StringIO()
    with redirect_stdout(buf_out), redirect_stderr(buf_err):
        code = int(doc_cli.cmd_doc_skill_section(args))
    out = buf_out.getvalue().strip()
    err = buf_err.getvalue().strip()
    if code != 0:
        return format_envelope(
            code,
            err.splitlines()[0] if err else f"skill-section failed: {skill}",
            None,
            (out + ("\n" + err if err else "")).strip() or None,
        )
    # Prefer short summary + body in detail for section content
    first = out.splitlines()[0] if out else f"skill={skill} section={section}"
    return format_envelope(
        0,
        first[:200],
        "workflow_session_entry",
        out if len(out) > 200 else None,
    )
