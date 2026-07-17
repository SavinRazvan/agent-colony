"""
File: test_check_governance_consistency.py
Path: tests/modules/architecture_scripts/test_check_governance_consistency.py
Role: Smoke test for governance drift scanner on MAS Workflow Kit layout.
Used By:
 - scripts/pr/prepare.py GATES (pytest -q)
Depends On:
 - scripts/architecture/check_governance_consistency.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_governance_consistency.py"


def test_governance_consistency_passes_without_ci_workflow() -> None:
  """MAS Workflow Kit may ship without .github/workflows until consumer adds CI."""
  proc = subprocess.run(
      [sys.executable, str(SCRIPT)],
      cwd=REPO_ROOT,
      capture_output=True,
      text=True,
      check=False,
  )
  assert proc.returncode == 0, proc.stdout + proc.stderr
  assert "passed" in proc.stdout.lower()
