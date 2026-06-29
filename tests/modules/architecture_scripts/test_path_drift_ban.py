"""
File: test_path_drift_ban.py
Path: tests/modules/architecture_scripts/test_path_drift_ban.py
Role: Tests path-drift detection in governance consistency scanner.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_governance_consistency.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_governance_consistency.py"


def test_path_drift_scan_passes_on_kit_surfaces() -> None:
    proc = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_pr_script_resolver() -> None:
    sys.path.insert(0, str(REPO_ROOT / ".ai_infra"))
    from paths import pr_script, pr_script_rel

    prepare = pr_script("prepare.py", REPO_ROOT)
    assert prepare.is_file()
    assert pr_script_rel("prepare.py") == ".ai_infra/scripts/pr/prepare.py"
