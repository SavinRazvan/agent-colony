"""
File: test_debug_cli.py
Path: tests/modules/debug/test_debug_cli.py
Role: Tests for debugger CLI parser and command flow.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/cli.py
 - .ai_infra/install/agent_colony/debug_cli.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(PKG_DIR) not in sys.path:
    sys.path.insert(0, str(PKG_DIR))

import cli  # noqa: E402


def _workspace(tmp_path: Path) -> Path:
    root = tmp_path / "workspace"
    (root / ".ai_infra" / "templates").mkdir(parents=True)
    shutil.copytree(
        REPO_ROOT / ".ai_infra" / "templates" / "debug-campaign",
        root / ".ai_infra" / "templates" / "debug-campaign",
    )
    return root


def test_debug_cli_flow(tmp_path: Path) -> None:
    root = _workspace(tmp_path)
    assert cli.main(["debug", "init", "--directory", str(root), "--slug", "cli-flow", "--item-id", "PVTI_test"]) == 0
    assert cli.main(["debug", "inventory", "--directory", str(root), "--slug", "cli-flow"]) == 0
    assert (
        cli.main(
            [
                "debug",
                "capture",
                "--directory",
                str(root),
                "--slug",
                "cli-flow",
                "--",
                sys.executable,
                "-c",
                "import sys; print('cli ok'); sys.exit(3)",
            ]
        )
        == 0
    )
    assert cli.main(["debug", "analyze", "--directory", str(root), "--slug", "cli-flow", "--run", "run-000001"]) == 0
    assert (
        cli.main(
            [
                "debug",
                "finding",
                "add",
                "--directory",
                str(root),
                "--slug",
                "cli-flow",
                "--kind",
                "TR",
                "--summary",
                "Add regression coverage",
            ]
        )
        == 0
    )
    assert cli.main(["debug", "probe", "scan", "--directory", str(root), "--slug", "cli-flow"]) == 0
    assert cli.main(["debug", "handoff", "--directory", str(root), "--slug", "cli-flow", "--next-agent", "test-runner"]) == 0
    assert cli.main(["debug", "repair", "--check", "--directory", str(root), "--slug", "cli-flow"]) == 0
    assert cli.main(["debug", "validate", "--directory", str(root), "--slug", "cli-flow"]) == 0


def test_debug_cli_registers_help() -> None:
    parser = cli.build_parser()
    args = parser.parse_args(["debug", "status", "--directory", ".", "--slug", "x", "--digest"])
    assert args.command == "debug"
    assert args.debug_command == "status"
