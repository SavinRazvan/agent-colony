"""
File: test_check_debrand.py
Path: tests/modules/architecture_scripts/test_check_debrand.py
Role: Smoke test for de-brand scanner on MAS Workflow Kit layout.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_debrand.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DEBRAND = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_debrand.py"
GOVERNANCE = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_governance_consistency.py"


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
