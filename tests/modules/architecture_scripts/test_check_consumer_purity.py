"""
File: test_check_consumer_purity.py
Path: tests/modules/architecture_scripts/test_check_consumer_purity.py
Role: Tests for consumer install purity scanner.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/architecture/check_consumer_purity.py
 - .ai_infra/scripts/install/scaffold.py
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PURITY = REPO_ROOT / ".ai_infra" / "scripts" / "architecture" / "check_consumer_purity.py"
SCAFFOLD_PATH = REPO_ROOT / ".ai_infra" / "scripts" / "install" / "scaffold.py"


def _load_scaffold():
    spec = importlib.util.spec_from_file_location("scaffold", SCAFFOLD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_consumer_purity_passes_on_fresh_scaffold(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "consumer"
    mod.scaffold(target, REPO_ROOT)
    proc = subprocess.run(
        [sys.executable, str(PURITY), "--target", str(target)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_consumer_purity_fails_when_ci_fixtures_ship(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "consumer"
    mod.scaffold(target, REPO_ROOT)
    ci = target / ".ai_infra" / "templates" / "local-workspace" / "ci" / "kit-dev"
    ci.mkdir(parents=True)
    (ci / "session-pointer.md").write_text("CI-QUALITY\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(PURITY), "--target", str(target)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "ci" in proc.stdout.lower() or "ci" in proc.stderr.lower()


def test_consumer_purity_fails_when_maintainer_ops_doc_ships(tmp_path: Path) -> None:
    mod = _load_scaffold()
    target = tmp_path / "consumer"
    mod.scaffold(target, REPO_ROOT)
    leaked = (
        target
        / ".ai_infra"
        / "docs"
        / "operations"
        / "documentation-maintenance-checklist.md"
    )
    leaked.parent.mkdir(parents=True, exist_ok=True)
    leaked.write_text("# maintainer only\n", encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(PURITY), "--target", str(target)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode != 0
    assert "documentation-maintenance-checklist" in proc.stdout
