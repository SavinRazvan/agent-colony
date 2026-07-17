"""
File: test_sys_path_bootstrap_branches.py
Path: tests/modules/workflow_mcp/test_sys_path_bootstrap_branches.py
Role: Forces the True branch of "if <dir> not in sys.path: sys.path.insert(...)" guards
      shared across cursor_workflow dispatcher modules and workflow_mcp/server.py.
      These lines only execute once per process by design (idempotent sys.path setup);
      running under pytest's shared process, an earlier test may have already inserted
      the same directory. Removing the exact path first guarantees True-branch coverage
      independent of collection order.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/cursor_workflow/{contributors_cli,doc_cli,drift_cli,integrate_cli,verify_cli}.py
 - .ai_infra/mcp_servers/workflow_mcp/server.py
"""

from __future__ import annotations

import os
import runpy
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow"

if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import contributors_cli  # noqa: E402
import doc_cli  # noqa: E402
import drift_cli  # noqa: E402
import integrate_cli  # noqa: E402
import verify_cli  # noqa: E402


@contextmanager
def _without_path(entry: str) -> Iterator[None]:
    """Remove every occurrence of ``entry`` from sys.path for the duration of the block.

    Several scripts share the same bootstrap-insert target (e.g. .ai_infra), so a single
    ``sys.path.remove`` only strips the first duplicate and leaves the guard condition
    ("entry not in sys.path") false elsewhere in the suite. Removing all copies up front
    guarantees the True branch fires; deduping back to at most one copy afterwards (rather
    than restoring the original duplicate count) stops duplicates from re-accumulating.
    """
    was_present = entry in sys.path
    while entry in sys.path:
        sys.path.remove(entry)
    try:
        yield
    finally:
        added_by_block = entry in sys.path
        while entry in sys.path:
            sys.path.remove(entry)
        if was_present or added_by_block:
            sys.path.insert(0, entry)


def test_contributors_cli_inserts_pr_dir() -> None:
    pr_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "pr")
    with _without_path(pr_dir):
        contributors_cli._import_user_settings(REPO_ROOT)
    assert pr_dir in sys.path


def test_doc_cli_inserts_architecture_dir() -> None:
    arch_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "architecture")
    with _without_path(arch_dir):
        doc_cli._import_check_doc_facts(REPO_ROOT)
    assert arch_dir in sys.path


def test_verify_cli_inserts_architecture_dir() -> None:
    arch_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "architecture")
    with _without_path(arch_dir):
        verify_cli._import_verify_all(REPO_ROOT)
    assert arch_dir in sys.path


def test_drift_cli_inserts_workflow_dir() -> None:
    workflow_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "workflow")
    with _without_path(workflow_dir):
        drift_cli._import_check_drift(REPO_ROOT)
    assert workflow_dir in sys.path


def test_integrate_cli_inserts_integration_dir() -> None:
    integration_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "integration")
    with _without_path(integration_dir):
        integrate_cli._import_validate(REPO_ROOT)
    assert integration_dir in sys.path


def _env_root() -> None:
    os.environ["WORKFLOW_KIT_ROOT"] = str(REPO_ROOT)


def test_server_user_settings_module_inserts_pr_dir() -> None:
    _env_root()
    from workflow_mcp.server import _user_settings_module

    pr_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "pr")
    with _without_path(pr_dir):
        _user_settings_module(REPO_ROOT)
    assert pr_dir in sys.path


def test_server_drift_validate_inserts_workflow_dir() -> None:
    _env_root()
    from workflow_mcp.server import workflow_drift_validate

    workflow_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "workflow")
    with _without_path(workflow_dir):
        workflow_drift_validate()
    assert workflow_dir in sys.path


def test_server_activate_inserts_pkg_dir() -> None:
    _env_root()
    from workflow_mcp.server import workflow_activate

    pkg = str(REPO_ROOT / ".ai_infra" / "install" / "cursor_workflow")
    with _without_path(pkg):
        workflow_activate(force=False)
    assert pkg in sys.path


def test_server_integrate_validate_inserts_integration_dir() -> None:
    _env_root()
    from workflow_mcp.server import workflow_integrate_validate

    integration_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "integration")
    with _without_path(integration_dir):
        workflow_integrate_validate()
    assert integration_dir in sys.path


def test_server_doc_facts_validate_inserts_architecture_dir() -> None:
    _env_root()
    from workflow_mcp.server import workflow_doc_facts_validate

    arch_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "architecture")
    with _without_path(arch_dir):
        workflow_doc_facts_validate()
    assert arch_dir in sys.path


def test_server_verify_all_inserts_architecture_dir(monkeypatch: pytest.MonkeyPatch) -> None:
    _env_root()
    arch_dir_path = REPO_ROOT / ".ai_infra" / "scripts" / "architecture"
    arch_dir = str(arch_dir_path)
    if arch_dir not in sys.path:
        sys.path.insert(0, arch_dir)
    import verify_all

    monkeypatch.setattr(verify_all, "run_verify_all", lambda root, py: [])
    monkeypatch.setattr(verify_all, "format_report", lambda results: "summary: failed=0 total=0")
    monkeypatch.setattr(verify_all, "exit_code_for", lambda results: 0)

    from workflow_mcp.server import workflow_verify_all

    with _without_path(arch_dir):
        workflow_verify_all()
    assert arch_dir in sys.path


def test_server_user_settings_module_spec_none_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from workflow_mcp.server import _user_settings_module

    monkeypatch.setattr(importlib.util, "spec_from_file_location", lambda *a, **k: None)
    with pytest.raises(ImportError, match="cannot load"):
        _user_settings_module(REPO_ROOT)


def test_validate_import_check_drift_inserts_workflow_dir() -> None:
    validate_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "integration")
    if validate_dir not in sys.path:
        sys.path.insert(0, validate_dir)
    import validate

    workflow_dir = str(REPO_ROOT / ".ai_infra" / "scripts" / "workflow")
    with _without_path(workflow_dir):
        validate._import_check_drift(REPO_ROOT)
    assert workflow_dir in sys.path


def test_gates_load_prepare_module_spec_none_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    import importlib.util

    from workflow_mcp import gates

    monkeypatch.setattr(importlib.util, "spec_from_file_location", lambda *a, **k: None)
    with pytest.raises(ImportError, match="Cannot load prepare module"):
        gates._load_prepare_module(REPO_ROOT)


@pytest.mark.parametrize(
    "rel_path",
    [
        ".ai_infra/scripts/architecture/check_doc_facts.py",
        ".ai_infra/scripts/architecture/verify_all.py",
        ".ai_infra/scripts/install/scaffold.py",
        ".ai_infra/scripts/integration/validate.py",
        ".ai_infra/scripts/release/sync_plugin_bundle.py",
        ".ai_infra/scripts/workflow/check_drift.py",
    ],
)
def test_module_bootstrap_loop_inserts_ai_infra_when_absent(rel_path: str) -> None:
    """Each of these scripts has its own module-level bootstrap walk-up loop that
    inserts .ai_infra into sys.path only the first time it runs in this process.
    Force a fresh exec with the entry removed first to cover the insert's True branch,
    independent of test collection order in the full suite.
    """
    ai_infra_entry = str(REPO_ROOT / ".ai_infra")
    with _without_path(ai_infra_entry):
        runpy.run_path(str(REPO_ROOT / rel_path), run_name=f"bootstrap_reload_{Path(rel_path).stem}")
    assert ai_infra_entry in sys.path
