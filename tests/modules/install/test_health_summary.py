"""
File: test_health_summary.py
Path: tests/modules/install/test_health_summary.py
Role: Tests health --summary one-line output.
Used By:
 - pytest
Depends On:
 - .ai_infra/install/agent_colony/cli.py
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_PKG_DIR = REPO_ROOT / ".ai_infra" / "install" / "agent_colony"
if str(_PKG_DIR) not in sys.path:
    sys.path.insert(0, str(_PKG_DIR))

import cli  # noqa: E402


def test_health_summary_pass(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(directory=REPO_ROOT, summary=True)
    code = cli.cmd_health(args)
    out = capsys.readouterr().out.strip()
    assert out in ("health: PASS",) or out.startswith("health: FAIL")
    assert "health:" in out
    assert code in (0, 1)
