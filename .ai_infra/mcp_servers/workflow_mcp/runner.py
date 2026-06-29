"""
File: runner.py
Path: .ai_infra/mcp_servers/workflow_mcp/runner.py
Role: Subprocess helpers for MCP tools wrapping existing scripts.
Used By:
 - workflow_mcp/server.py
Depends On:
 - subprocess
 - sys
 - pathlib
Notes:
 - Resolves .ai_infra/scripts/ first, then legacy scripts/ layout.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_LEGACY_PREFIX = "scripts/"
DEFAULT_SUBPROCESS_TIMEOUT_S = 300.0


def resolve_python(cmd: list[str]) -> list[str]:
    resolved = list(cmd)
    if resolved and resolved[0] == "python":
        resolved[0] = sys.executable
    return resolved


def resolve_script_path(cwd: Path, relative: str) -> Path | None:
    """Resolve PR/architecture script for kit or legacy consumer layout."""
    rel = relative.replace("\\", "/")
    if rel.startswith(_LEGACY_PREFIX):
        tail = rel[len(_LEGACY_PREFIX) :]
        canonical = cwd / ".ai_infra" / "scripts" / tail
        if canonical.is_file():
            return canonical
    direct = cwd / rel
    if direct.is_file():
        return direct
    if rel.startswith(_LEGACY_PREFIX):
        tail = rel[len(_LEGACY_PREFIX) :]
        return cwd / ".ai_infra" / "scripts" / tail
    return cwd / rel


def run_cmd(cmd: list[str], cwd: Path, *, timeout_s: float | None = DEFAULT_SUBPROCESS_TIMEOUT_S) -> tuple[int, str]:
    normalized = resolve_python(cmd)
    try:
        proc = subprocess.run(
            normalized,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_s,
        )
    except subprocess.TimeoutExpired:
        joined = " ".join(normalized)
        return 124, f"timeout after {timeout_s}s: {joined}"
    output = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, output.strip()


def run_script(
    relative: str,
    args: list[str],
    cwd: Path,
    *,
    timeout_s: float | None = DEFAULT_SUBPROCESS_TIMEOUT_S,
) -> tuple[int, str]:
    script = resolve_script_path(cwd, relative)
    if script is None or not script.is_file():
        return 1, f"Script not found: {relative} (cwd={cwd})"
    cmd = [sys.executable, str(script), *args]
    return run_cmd(cmd, cwd, timeout_s=timeout_s)
