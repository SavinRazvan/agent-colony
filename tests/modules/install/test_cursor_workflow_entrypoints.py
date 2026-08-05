"""
File: test_cursor_workflow_entrypoints.py
Path: tests/modules/install/test_cursor_workflow_entrypoints.py
Role: Cover install-tree cursor_workflow __init__ and __main__ (Miss=0).
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/__init__.py
 - .ai_infra/install/cursor_workflow/__main__.py
"""

from __future__ import annotations

import importlib
import importlib.util
import runpy
import sys
from pathlib import Path
from types import ModuleType

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
INSTALL_PARENT = REPO_ROOT / ".ai_infra" / "install"
PKG = INSTALL_PARENT / "cursor_workflow"


def test_install_init_version() -> None:
    """Execute install package __init__.py so coverage sees __version__."""
    spec = importlib.util.spec_from_file_location(
        "cursor_workflow_install_init",
        PKG / "__init__.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__version__ == "0.4.0"


def test_install_main_module(monkeypatch) -> None:
    """Run install __main__ with a stub cursor_workflow.cli.main."""
    calls: list[object] = []

    stub_cli = ModuleType("cursor_workflow.cli")

    def fake_main(argv=None):
        calls.append(argv)
        return 7

    stub_cli.main = fake_main  # type: ignore[attr-defined]

    stub_pkg = ModuleType("cursor_workflow")
    stub_pkg.cli = stub_cli  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "cursor_workflow", stub_pkg)
    monkeypatch.setitem(sys.modules, "cursor_workflow.cli", stub_cli)

    with pytest.raises(SystemExit) as exc:
        runpy.run_path(str(PKG / "__main__.py"), run_name="__main__")
    assert exc.value.code == 7
    assert calls == [None] or len(calls) == 1
