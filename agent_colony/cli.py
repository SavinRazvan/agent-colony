"""
File: cli.py
Path: agent_colony/cli.py
Role: Root shim re-exporting install CLI for python -m agent_colony.
Used By:
 - python -m agent_colony
 - tests/modules/install/test_agent_colony.py
Depends On:
 - .ai_infra/install/agent_colony/cli.py
Notes:
 - importlib load; keep in sync with install package entrypoints.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

_CLI = Path(__file__).resolve().parent.parent / ".ai_infra" / "install" / "agent_colony" / "cli.py"
_spec = importlib.util.spec_from_file_location("agent_colony_cli", _CLI)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

__version__ = "0.6.5"

main = _mod.main
cmd_gates = _mod.cmd_gates
cmd_install = _mod.cmd_install
build_parser = _mod.build_parser
kit_root = _mod.kit_root
_run = _mod._run
