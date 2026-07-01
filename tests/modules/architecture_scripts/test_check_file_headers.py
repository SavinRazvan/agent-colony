"""
File: test_check_file_headers.py
Path: tests/modules/architecture_scripts/test_check_file_headers.py
Role: Tests for Python module header scanner.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_file_headers.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HEADER_CHECK = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_file_headers.py"


def test_file_header_check_passes_on_kit_repo() -> None:
    proc = subprocess.run(
        [sys.executable, str(HEADER_CHECK), "--directory", str(REPO_ROOT)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_file_header_check_fails_without_header(tmp_path: Path) -> None:
    bad = tmp_path / "sample.py"
    bad.write_text("x = 1\n", encoding="utf-8")
    scripts = tmp_path / ".ai_infra" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "bad.py").write_text("y = 2\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(HEADER_CHECK), "--directory", str(tmp_path)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "bad.py" in proc.stdout
