"""
File: cli.py
Path: cursor_workflow/cli.py
Role: Root shim re-exporting install CLI for python -m cursor_workflow.
Used By:
 - python -m cursor_workflow
 - tests/modules/install/test_cursor_workflow.py
Depends On:
 - .ai_infra/install/cursor_workflow/cli.py
Notes:
 - importlib load; keep in sync with install package entrypoints.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_CLI = Path(__file__).resolve().parent.parent / ".ai_infra" / "install" / "cursor_workflow" / "cli.py"
_spec = importlib.util.spec_from_file_location("cursor_workflow_cli", _CLI)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

__version__ = "0.4.0"

main = _mod.main
cmd_gates = _mod.cmd_gates
cmd_install = _mod.cmd_install
build_parser = _mod.build_parser
kit_root = _mod.kit_root
_run = _mod._run
