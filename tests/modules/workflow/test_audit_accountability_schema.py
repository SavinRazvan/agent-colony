"""
File: test_audit_accountability_schema.py
Path: tests/modules/workflow/test_audit_accountability_schema.py
Role: Unit tests for audit_artifact_schema validator and parsers.
Used By:
 - pytest
Depends On:
 - .ai_infra/scripts/workflow/audit_artifact_schema.py
Notes:
 - Fixtures live under tests/modules/workflow/fixtures/audit_artifacts/.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
_WORKFLOW = REPO_ROOT / ".ai_infra" / "scripts" / "workflow"
if str(_WORKFLOW) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW))

import audit_artifact_schema as schema  # noqa: E402

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "audit_artifacts"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_complete_ok_passes() -> None:
    skip, errors, warnings = schema.validate_audit_text(_read("complete_ok.md"))
    assert skip is False
    assert errors == []
    assert warnings == []


def test_p0_missing_consequence_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("p0_missing_consequence.md"))
    assert skip is False
    assert any("consequence_if_ignored" in e for e in errors)


def test_p2_optional_passes() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("p2_optional.md"))
    assert skip is False
    assert errors == []


def test_unknown_scope_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("unknown_scope.md"))
    assert skip is False
    assert any("unknown Audit-Scope" in e for e in errors)


def test_missing_limits_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("missing_limits.md"))
    assert skip is False
    assert any("Audit limits" in e for e in errors)


def test_no_schema_skips() -> None:
    skip, errors, warnings = schema.validate_audit_text(_read("no_schema.md"))
    assert skip is True
    assert errors == []
    assert warnings == []


def test_iter_findings_section_and_table() -> None:
    text = _read("complete_ok.md") + (
        "\n| id | severity | owner | due_slice | consequence_if_ignored | evidence |\n"
        "|---|---|---|---|---|---|\n"
        "| AA-table-001 | P1 | owner | slice-1 | blocked | path/to/file |\n"
    )
    findings = schema.iter_findings(text)
    ids = {f["id"] for f in findings}
    assert "AA-gate-001" in ids
    assert "AA-table-001" in ids


def test_assurance_warning_on_empty_evidence() -> None:
    text = """---
Audit-Schema: 1
Audit-Scope: kit
Named-Target: test
Assurance-Level: high
Commissioned-By: maintainer
Audited-By: auditor
---
## Accountability summary
Test fixture.
## Audit limits
- test
### AA-001
- severity: P1
- status: fixed
- owner: alice
- due_slice: slice-a
- consequence_if_ignored: blocked
"""
    _skip, errors, warnings = schema.validate_audit_text(text)
    assert errors == []
    assert any("caps Assurance-Level" in w for w in warnings)


def test_p0_open_status_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("p0_open_status.md"))
    assert skip is False
    assert any("open P0/P1 status blocks merge" in e for e in errors)


def test_p0_accepted_divergence_passes() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("p0_accepted_divergence.md"))
    assert skip is False
    assert errors == []


def test_p1_missing_status_fails() -> None:
    text = """---
Audit-Schema: 1
Audit-Scope: kit
Named-Target: missing status
Commissioned-By: maintainer
Audited-By: auditor
---
## Accountability summary
Missing status.
## Audit limits
- fixture
### AA-missing-status
- severity: P1
- owner: alice
- due_slice: slice-a
- consequence_if_ignored: blocked
"""
    skip, errors, _warnings = schema.validate_audit_text(text)
    assert skip is False
    assert any("requires status" in e for e in errors)


def test_independence_warning_when_audited_equals_commissioned() -> None:
    text = """---
Audit-Schema: 1
Audit-Scope: kit
Named-Target: independence check
Commissioned-By: same-actor
Audited-By: Same-Actor
---
## Accountability summary
Independence fixture.
## Audit limits
- kit-process only
"""
    _skip, errors, warnings = schema.validate_audit_text(text)
    assert errors == []
    assert any("independence" in w.lower() for w in warnings)


def test_missing_severity_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("missing_severity.md"))
    assert skip is False
    assert any("requires severity" in e for e in errors)


def test_missing_accountability_summary_fails() -> None:
    skip, errors, _warnings = schema.validate_audit_text(_read("missing_summary.md"))
    assert skip is False
    assert any("Accountability summary" in e for e in errors)


def test_phase_heading_ignored() -> None:
    skip, errors, warnings = schema.validate_audit_text(_read("phase_heading_ok.md"))
    assert skip is False
    assert errors == []
    assert warnings == []
    ids = {f["id"] for f in schema.iter_findings(_read("phase_heading_ok.md"))}
    assert "AA-real-001" in ids
    assert not any(i.startswith("PHASE") for i in ids)


@pytest.mark.parametrize(
    "value",
    ["", "-", "(TBD)", "tbd", "TBD"],
)
def test_placeholder_detection(value: str) -> None:
    assert schema._is_placeholder(value) is True
