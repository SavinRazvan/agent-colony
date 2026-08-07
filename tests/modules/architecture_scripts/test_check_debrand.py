"""
File: test_check_debrand.py
Path: tests/modules/architecture_scripts/test_check_debrand.py
Role: Smoke test for de-brand scanner on Agent Colony layout.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_debrand.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEBRAND = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_debrand.py"
GOVERNANCE = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_governance_consistency.py"


def _load_debrand_module():
    spec = importlib.util.spec_from_file_location("check_debrand", DEBRAND)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_debrand_check_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(DEBRAND)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_governance_brand_scan_passes() -> None:
    proc = subprocess.run(
        [sys.executable, str(GOVERNANCE)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_debrand_flags_legacy_product_slug() -> None:
    mod = _load_debrand_module()
    pattern = dict(mod.BANNED_PATTERNS)["mas-workflow-kit-project-ssot"]
    assert mod.text_has_banned_pattern(
        "Install from mas-workflow-kit-project-ssot today.",
        pattern,
    )


def test_debrand_allows_formerly_line() -> None:
    mod = _load_debrand_module()
    # Formerly is now banned, so this must be flagged
    pattern = dict(mod.BANNED_PATTERNS)["Formerly"]
    assert mod.text_has_banned_pattern(
        "Formerly MAS Workflow Kit — Project SSOT.",
        pattern,
    )


def test_debrand_allows_upstream_lineage() -> None:
    mod = _load_debrand_module()
    # upstream is now banned, so this must be flagged
    pattern = dict(mod.BANNED_PATTERNS)["upstream"]
    assert mod.text_has_banned_pattern(
        "Do not mutate upstream mas-workflow-kit.",
        pattern,
    )


def test_debrand_flags_legacy_cli_module_name() -> None:
    mod = _load_debrand_module()
    pattern = dict(mod.BANNED_PATTERNS)["cursor_workflow"]
    assert mod.text_has_banned_pattern(
        "Run python -m cursor_workflow health",
        pattern,
    )


def test_debrand_text_suffixes_include_html_and_js() -> None:
    mod = _load_debrand_module()
    assert ".html" in mod.TEXT_SUFFIXES
    assert ".js" in mod.TEXT_SUFFIXES


def test_debrand_flags_workflow_mcp_underscore_prefix() -> None:
    mod = _load_debrand_module()
    pattern = dict(mod.BANNED_PATTERNS)["workflow_mcp_"]
    assert mod.text_has_banned_pattern(
        "def workflow_mcp_connection_guide():\n    pass\n",
        pattern,
    )
    exact = dict(mod.BANNED_PATTERNS)["workflow_mcp_connection_guide"]
    assert mod.text_has_banned_pattern("workflow_mcp_connection_guide", exact)
