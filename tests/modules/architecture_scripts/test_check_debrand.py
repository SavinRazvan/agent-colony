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
    assert mod.text_has_banned_pattern(
        "Install from mas-workflow-kit-project-ssot today.",
        mod.BANNED_PATTERNS[9][1],
    )


def test_debrand_allows_formerly_line() -> None:
    mod = _load_debrand_module()
    # Formerly is now banned, so this must be flagged
    assert mod.text_has_banned_pattern(
        "Formerly MAS Workflow Kit — Project SSOT.",
        mod.BANNED_PATTERNS[15][1],
    )


def test_debrand_allows_upstream_lineage() -> None:
    mod = _load_debrand_module()
    # upstream is now banned, so this must be flagged
    assert mod.text_has_banned_pattern(
        "Do not mutate upstream mas-workflow-kit.",
        mod.BANNED_PATTERNS[16][1],
    )
