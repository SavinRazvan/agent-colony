"""
File: test_bootstrap_and_misc.py
Path: tests/modules/ai_infra/test_bootstrap_and_misc.py
Role: Coverage for small, otherwise-untested kit surfaces: .ai_infra/__init__.py,
      .ai_infra/bootstrap.py, .ai_infra/scripts/architecture/consumer_bundle_paths.py,
      cursor_workflow/__main__.py.
Used By:
 - pytest
Depends On:
 - .ai_infra/__init__.py
 - .ai_infra/bootstrap.py
 - .ai_infra/scripts/architecture/consumer_bundle_paths.py
 - cursor_workflow/__main__.py
"""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


def test_ai_infra_package_exposes_version() -> None:
    spec = importlib.util.spec_from_file_location(
        "ai_infra_pkg_test", REPO_ROOT / ".ai_infra" / "__init__.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__version__ == "0.4.0"


def test_bootstrap_ensure_paths_import_inserts_ai_infra_dir() -> None:
    spec = importlib.util.spec_from_file_location(
        "bootstrap_test", REPO_ROOT / ".ai_infra" / "bootstrap.py"
    )
    assert spec is not None and spec.loader is not None
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)

    ai_infra_str = str(REPO_ROOT / ".ai_infra")
    present = ai_infra_str in sys.path
    if present:
        sys.path.remove(ai_infra_str)
    try:
        kit = bootstrap.ensure_paths_import(str(REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"))
        assert kit == REPO_ROOT
        assert ai_infra_str in sys.path
    finally:
        if ai_infra_str not in sys.path:
            sys.path.insert(0, ai_infra_str)


def test_bootstrap_ensure_paths_import_skips_reinsert_when_present() -> None:
    spec = importlib.util.spec_from_file_location(
        "bootstrap_test2", REPO_ROOT / ".ai_infra" / "bootstrap.py"
    )
    assert spec is not None and spec.loader is not None
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)

    ai_infra_str = str(REPO_ROOT / ".ai_infra")
    if ai_infra_str not in sys.path:
        sys.path.insert(0, ai_infra_str)
    kit = bootstrap.ensure_paths_import(str(REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"))
    assert kit == REPO_ROOT


def test_bootstrap_raises_when_paths_py_not_found(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "bootstrap_test3", REPO_ROOT / ".ai_infra" / "bootstrap.py"
    )
    assert spec is not None and spec.loader is not None
    bootstrap = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bootstrap)

    isolated = tmp_path / "isolated" / "nested"
    isolated.mkdir(parents=True)
    with pytest.raises(RuntimeError, match="paths.py not found above"):
        bootstrap.ensure_paths_import(str(isolated / "script.py"))


def test_consumer_bundle_paths_ignore_returns_empty_when_no_ci_dir() -> None:
    spec = importlib.util.spec_from_file_location(
        "consumer_bundle_paths_test",
        REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "consumer_bundle_paths.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.ignore_local_workspace_ci("/some/other/dir", ["ci", "other.txt"]) == set()
    assert mod.ignore_local_workspace_ci("/some/other/dir", ["other.txt"]) == set()
    assert mod.ignore_local_workspace_ci(
        "/repo/.ai_infra/templates/local-workspace", ["ci", "index.html"]
    ) == {"ci"}
    assert mod.is_local_workspace_copy("templates/local-workspace") is True
    assert mod.is_local_workspace_copy("templates/local-workspace/") is True
    assert mod.is_local_workspace_copy("other/path") is False


def test_cursor_workflow_dunder_main_guard(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "argv", ["cursor_workflow", "--version"])
    with pytest.raises(SystemExit) as exc_info:
        runpy.run_path(str(REPO_ROOT / "cursor_workflow" / "__main__.py"), run_name="__main__")
    assert exc_info.value.code == 0


def test_cursor_workflow_dunder_main_module_load_without_guard() -> None:
    module = runpy.run_path(
        str(REPO_ROOT / "cursor_workflow" / "__main__.py"), run_name="cursor_workflow_main_test"
    )
    assert "_mod" in module
