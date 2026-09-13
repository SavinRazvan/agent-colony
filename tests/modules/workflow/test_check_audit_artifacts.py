"""
File: test_check_audit_artifacts.py
Path: tests/modules/workflow/test_check_audit_artifacts.py
Role: Tests check_audit_artifacts CLI scanner.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/check_audit_artifacts.py
Notes:
 - Uses temporary audit artifact trees.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_WORKFLOW) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW))

import check_audit_artifacts as checker  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "audit_artifacts"


def _write_audit(root: Path, rel: str, name: str) -> None:
    dest = root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text((FIXTURES / name).read_text(encoding="utf-8"), encoding="utf-8")


def test_scan_passes_on_valid_alignment(tmp_path: Path) -> None:
    _write_audit(tmp_path, ".local/workflow-artifacts/alignment/alignment-audit.md", "complete_ok.md")
    code = checker.main(["--directory", str(tmp_path), "--summary"])
    assert code == 0


def test_scan_fails_on_invalid_alignment(tmp_path: Path) -> None:
    _write_audit(tmp_path, ".local/workflow-artifacts/alignment/alignment-audit.md", "missing_limits.md")
    code = checker.main(["--directory", str(tmp_path), "--summary"])
    assert code == 1


def test_arch_impacting_requires_alignment_files(tmp_path: Path) -> None:
    code = checker.main(["--directory", str(tmp_path), "--arch-impacting", "--summary"])
    assert code == 1


def test_collect_includes_workflow_audit_dir(tmp_path: Path) -> None:
    _write_audit(tmp_path, ".local/workflow-artifacts/audit/custom.md", "no_schema.md")
    paths = checker.collect_audit_paths(tmp_path)
    assert any(p.name == "custom.md" for p in paths)
