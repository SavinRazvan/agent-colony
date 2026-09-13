"""
File: audit_artifact_schema.py
Path: .ai_infra/scripts/workflow/audit_artifact_schema.py
Role: Parse and validate audit artifact markdown (Audit-Schema: 1 accountability).
Used By:
 - .ai_infra/scripts/workflow/check_audit_artifacts.py
 - tests/modules/workflow/test_audit_accountability_schema.py
Depends On:
 - re (stdlib)
Notes:
 - Opt-in: artifacts without Audit-Schema: 1 are skipped (not errors).
 - Consumer resolve_gates stays 2 gates; kit-dev prepare appends this validator.
"""

from __future__ import annotations

import re
from typing import Any

ALLOWED_SCOPES = frozenset({"kit", "product", "model", "dataset", "ecosystem", "meta"})
ASSURANCE_LEVELS = frozenset({"high", "reasonable", "limited", "very_limited"})
ALLOWED_FINDING_STATUSES = frozenset(
    {"open", "accepted_divergence", "fixed", "deferred"}
)
ALLOWED_FINDING_CATEGORIES = frozenset(
    {
        "stale_doc_reference",
        "policy_conflict",
        "workflow_gate_drift",
        "artifact_requirement_gap",
        "module_traceability_gap",
        "ci_path_drift",
        "naming_or_precedence_drift",
        "strategy_product_boundary_drift",
        "test_coverage_mapping_gap",
        "rule_parser_or_format_risk",
        "token_contract",
    }
)

_PLACEHOLDER_VALUES = frozenset({"", "-", "tbd", "(tbd)"})
_P0_P1_REQUIRED_PATH_FIELDS = (
    "category",
    "source_path",
    "target_path",
    "recommendation",
    "evidence",
)
_FINDING_ID_RE = re.compile(
    r"^(AA|EA|DRIFT)-[A-Za-z0-9][A-Za-z0-9_-]*$",
    re.IGNORECASE,
)
_FRONTMATTER_KEY_ALIASES = {
    "audit-schema": "Audit-Schema",
    "audit_scope": "Audit-Scope",
    "audit-scope": "Audit-Scope",
    "named-target": "Named-Target",
    "named_target": "Named-Target",
    "assurance-level": "Assurance-Level",
    "assurance_level": "Assurance-Level",
    "commissioned-by": "Commissioned-By",
    "audited-by": "Audited-By",
}


def _normalize_key(key: str) -> str:
    stripped = key.strip()
    lower = stripped.lower()
    return _FRONTMATTER_KEY_ALIASES.get(lower, stripped)


def _is_placeholder(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in _PLACEHOLDER_VALUES


def parse_frontmatter(text: str) -> dict[str, str]:
    """Extract YAML-like key: value frontmatter from the document start."""
    lines = text.splitlines()
    if not lines:
        return {}

    body_start = 0
    fm_lines: list[str] = []
    if lines[0].strip() == "---":
        for idx, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                body_start = idx + 1
                break
            fm_lines.append(line)
    else:
        for idx, line in enumerate(lines):
            if not line.strip():
                body_start = idx + 1
                break
            if ":" not in line:
                body_start = idx
                break
            if line.lstrip().startswith("#"):
                body_start = idx
                break
            fm_lines.append(line)
            body_start = idx + 1

    result: dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        norm = _normalize_key(key)
        result[norm] = value.strip()
    return result


def _parse_section_fields(block: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        body = stripped[2:].strip()
        if ":" not in body:
            continue
        key, value = body.split(":", 1)
        fields[key.strip().lower()] = value.strip()
    return fields


def _parse_table_findings(text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for match in re.finditer(
        r"^\|[^\n]+\|\s*\n\|[-:\s|]+\|\s*\n((?:\|[^\n]+\|\s*\n)+)",
        text,
        re.MULTILINE,
    ):
        table_block = match.group(0)
        rows = [r.strip() for r in table_block.splitlines() if r.strip().startswith("|")]
        if len(rows) < 2:
            continue
        headers = [h.strip().lower() for h in rows[0].strip("|").split("|")]
        if "id" not in headers or "severity" not in headers:
            continue
        for row in rows[2:]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) != len(headers):
                continue
            record = dict(zip(headers, cells, strict=False))
            finding_id = record.get("id", "")
            if not finding_id or finding_id.lower() in {"id", "---"}:
                continue
            findings.append(
                {
                    "id": finding_id,
                    "severity": record.get("severity", ""),
                    "status": record.get("status", ""),
                    "category": record.get("category", ""),
                    "source_path": record.get("source_path", ""),
                    "target_path": record.get("target_path", ""),
                    "recommendation": record.get("recommendation", ""),
                    "owner": record.get("owner", ""),
                    "due_slice": record.get("due_slice", "") or record.get("deadline", ""),
                    "deadline": record.get("deadline", ""),
                    "consequence_if_ignored": record.get("consequence_if_ignored", ""),
                    "evidence": record.get("evidence", ""),
                    "expectation": record.get("expectation", ""),
                }
            )
    return findings


def _is_finding_heading(heading: str) -> bool:
    """True when ### heading is an AA/EA/DRIFT finding id (not protocol PHASE/CHK)."""
    cleaned = heading.strip().rstrip(".:")
    if cleaned.lower() in {"findings", "summary", "audit limits"}:
        return False
    return bool(_FINDING_ID_RE.match(cleaned))


def iter_findings(text: str) -> list[dict[str, Any]]:
    """Yield finding dicts from ### id sections or markdown tables."""
    findings: list[dict[str, Any]] = []

    section_pattern = re.compile(
        r"^###\s+([^\n]+)\s*\n(.*?)(?=^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    for match in section_pattern.finditer(text):
        finding_id = match.group(1).strip().rstrip(".:")
        if not _is_finding_heading(finding_id):
            continue
        fields = _parse_section_fields(match.group(2))
        severity = fields.get("severity", "")
        findings.append(
            {
                "id": finding_id,
                "severity": severity,
                "status": fields.get("status", ""),
                "category": fields.get("category", ""),
                "source_path": fields.get("source_path", ""),
                "target_path": fields.get("target_path", ""),
                "recommendation": fields.get("recommendation", ""),
                "owner": fields.get("owner", ""),
                "due_slice": fields.get("due_slice", "") or fields.get("deadline", ""),
                "deadline": fields.get("deadline", ""),
                "consequence_if_ignored": fields.get("consequence_if_ignored", ""),
                "evidence": fields.get("evidence", ""),
                "expectation": fields.get("expectation", ""),
            }
        )

    table_findings = _parse_table_findings(text)
    seen = {f["id"] for f in findings}
    for row in table_findings:
        if row["id"] not in seen:
            findings.append(row)
            seen.add(row["id"])
    return findings


def validate_audit_text(text: str) -> tuple[bool, list[str], list[str]]:
    """
    Validate audit artifact text.

    Returns (skip, errors, warnings). When skip is True, errors is empty.
    """
    frontmatter = parse_frontmatter(text)
    schema_raw = frontmatter.get("Audit-Schema", "").strip()
    if schema_raw != "1":
        return True, [], []

    errors: list[str] = []
    warnings: list[str] = []

    scope = (
        frontmatter.get("Audit-Scope", "")
        or frontmatter.get("audit_scope", "")
    ).strip().lower()
    if not scope:
        errors.append("Audit-Schema: 1 requires Audit-Scope")
    elif scope not in ALLOWED_SCOPES:
        errors.append(f"unknown Audit-Scope '{scope}' — allowed: {', '.join(sorted(ALLOWED_SCOPES))}")

    named_target = frontmatter.get("Named-Target", "").strip()
    if _is_placeholder(named_target):
        errors.append("Audit-Schema: 1 requires non-empty Named-Target")

    lower_text = text.lower()
    if "## audit limits" not in lower_text:
        errors.append("Audit-Schema: 1 requires ## Audit limits heading")
    if "## accountability summary" not in lower_text:
        errors.append("Audit-Schema: 1 requires ## Accountability summary heading")

    assurance = frontmatter.get("Assurance-Level", "").strip().lower()
    if assurance and assurance not in ASSURANCE_LEVELS:
        errors.append(
            f"Assurance-Level '{assurance}' not in "
            f"{', '.join(sorted(ASSURANCE_LEVELS))}"
        )

    audited_by = frontmatter.get("Audited-By", "").strip()
    commissioned_by = frontmatter.get("Commissioned-By", "").strip()
    if _is_placeholder(commissioned_by):
        warnings.append(
            "independence: Commissioned-By missing or placeholder — "
            "internal audit risk (ADR-013)"
        )
    elif (
        audited_by
        and audited_by.casefold() == commissioned_by.casefold()
    ):
        warnings.append(
            "independence: Audited-By equals Commissioned-By "
            f"('{audited_by}') — internal audit risk (ADR-013)"
        )

    for finding in iter_findings(text):
        severity = str(finding.get("severity", "")).strip().upper()
        if severity not in {"P0", "P1", "P2"}:
            if severity:
                errors.append(f"{finding['id']}: unknown severity '{severity}'")
            else:
                errors.append(f"{finding['id']}: requires severity P0|P1|P2")
            continue

        if severity in {"P0", "P1"}:
            if _is_placeholder(str(finding.get("owner", ""))):
                errors.append(f"{finding['id']}: P0/P1 requires non-placeholder owner")
            due = str(finding.get("due_slice", "") or finding.get("deadline", ""))
            if _is_placeholder(due):
                errors.append(f"{finding['id']}: P0/P1 requires due_slice or deadline")
            if _is_placeholder(str(finding.get("consequence_if_ignored", ""))):
                errors.append(f"{finding['id']}: P0/P1 requires consequence_if_ignored")

            status_raw = str(finding.get("status", "")).strip().lower()
            if _is_placeholder(status_raw):
                errors.append(f"{finding['id']}: P0/P1 requires status")
            elif status_raw not in ALLOWED_FINDING_STATUSES:
                errors.append(
                    f"{finding['id']}: unknown status '{status_raw}' — allowed: "
                    f"{', '.join(sorted(ALLOWED_FINDING_STATUSES))}"
                )
            elif status_raw == "open":
                errors.append(
                    f"{finding['id']}: open P0/P1 status blocks merge "
                    "(use accepted_divergence|fixed|deferred)"
                )

            for field in _P0_P1_REQUIRED_PATH_FIELDS:
                value = str(finding.get(field, "")).strip()
                if _is_placeholder(value):
                    errors.append(f"{finding['id']}: P0/P1 requires {field}")
                elif field == "category" and value not in ALLOWED_FINDING_CATEGORIES:
                    errors.append(
                        f"{finding['id']}: unknown category '{value}' — allowed: "
                        f"{', '.join(sorted(ALLOWED_FINDING_CATEGORIES))}"
                    )

            evidence = str(finding.get("evidence", "")).strip()
            if (
                not _is_placeholder(evidence)
                and assurance in {"high", "reasonable"}
                and len(evidence) < 8
            ):
                warnings.append(
                    f"{finding['id']}: thin evidence caps Assurance-Level to limited "
                    f"(declared {assurance})"
                )
    return False, errors, warnings
