"""
File: test_drift017_audit_independence.py
Path: tests/modules/workflow_drift/test_drift017_audit_independence.py
Role: Tests DRIFT-017 audit independence WARN check (kit-dev only).
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/drift_checks.py
Notes:
 - DRIFT-017 always passes (WARN advisory); not a P0 blocker.
 - Schema validation errors belong to check_audit_artifacts, not DRIFT-017.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_WORKFLOW) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW))

from drift_checks import check_drift017, drift_paths  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "modules" / "workflow" / "fixtures" / "audit_artifacts"


def _kit_dev_root(tmp_path: Path) -> None:
    impl = tmp_path / ".ai_infra" / "docs" / "handoff" / "IMPLEMENTATION-STATUS.md"
    impl.parent.mkdir(parents=True, exist_ok=True)
    impl.write_text("# status\n", encoding="utf-8")


def test_drift017_warns_when_audited_by_equals_commissioned_by(tmp_path: Path) -> None:
    _kit_dev_root(tmp_path)
    audit = tmp_path / ".local" / "workflow-artifacts" / "alignment" / "alignment-audit.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    body = (FIXTURES / "complete_ok.md").read_text(encoding="utf-8")
    # Same actor on both fields → independence WARN (ADR-013 §5).
    body = body.replace("Commissioned-By: maintainer", "Commissioned-By: auditor")
    body = body.replace("Audited-By: auditor", "Audited-By: auditor")
    audit.write_text(body, encoding="utf-8")

    result = check_drift017(drift_paths(tmp_path))
    assert result.check_id == "DRIFT-017"
    assert result.passed is True
    assert "WARN" in result.detail
    assert "independence" in result.detail.lower() or "Audited-By" in result.detail


def test_drift017_no_warn_when_roles_distinct(tmp_path: Path) -> None:
    _kit_dev_root(tmp_path)
    audit = tmp_path / ".local" / "workflow-artifacts" / "alignment" / "alignment-audit.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text((FIXTURES / "complete_ok.md").read_text(encoding="utf-8"), encoding="utf-8")

    result = check_drift017(drift_paths(tmp_path))
    assert result.check_id == "DRIFT-017"
    assert result.passed is True
    assert "WARN" not in result.detail


def test_drift017_ignores_schema_errors(tmp_path: Path) -> None:
    """Incomplete Schema-1 fails the gate; DRIFT-017 must not echo schema errors."""
    _kit_dev_root(tmp_path)
    audit = tmp_path / ".local" / "workflow-artifacts" / "alignment" / "alignment-audit.md"
    audit.parent.mkdir(parents=True, exist_ok=True)
    audit.write_text((FIXTURES / "missing_limits.md").read_text(encoding="utf-8"), encoding="utf-8")

    result = check_drift017(drift_paths(tmp_path))
    assert result.check_id == "DRIFT-017"
    assert result.passed is True
    assert "Audit limits" not in result.detail
    assert "Accountability summary" not in result.detail


def test_drift017_skips_non_kit_dev(tmp_path: Path) -> None:
    result = check_drift017(drift_paths(tmp_path))
    assert result.passed is True
    assert "skipped" in result.detail
