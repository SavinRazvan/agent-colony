<!--
File: alignment-audit-schema.md
Path: .ai_infra/docs/roadmap/alignment-audit-schema.md
Role: Required fields and taxonomy for advisory alignment audit findings (.local/workflow-artifacts/alignment/).
Used By:
 - .cursor/skills/enterprise-architecture-audit/SKILL.md
 - enterprise-auditor alignment passes
 - .cursor/rules/advisory-audit-alignment-enforcement.mdc
Depends On:
 - docs/governance/workflow-source-owners.md
Notes:
 - Universal MAS Workflow Kit schema; product-specific vocabulary belongs in project overlays.
 - Last reviewed: 2026-06-14
-->

# Alignment Audit Schema

## Purpose

Standardize advisory audit findings so outputs from skills, rules checks, and manual review merge into one deterministic report.

**Product vocabulary:** When findings involve domain boundaries, cite your project's strategy/architecture docs as `target_path` (e.g. `docs/architecture/*`, overlay rules in `overlays/rules/`).

## Finding Object (Required Fields)

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | `string` | yes | Unique stable ID (`AA-<domain>-<number>`). |
| `severity` | `P0 \| P1 \| P2` | yes | Priority classification. |
| `category` | `string` | yes | Drift class from allowed taxonomy below. |
| `source_path` | `string` | yes | Path where mismatch is observed. |
| `target_path` | `string` | yes | Path that defines expected behavior. |
| `evidence` | `string` | yes | Concise quote or factual mismatch proof. |
| `recommendation` | `string` | yes | Concrete remediation guidance. |
| `status` | `open \| accepted_divergence \| fixed \| deferred` | yes | Lifecycle state. |
| `owner` | `string` | no | Responsible person or role. |
| `due_slice` | `string` | no | Planned implementation slice. |

## Severity Taxonomy

- `P0`: Critical policy, safety, or architecture drift that can break mandatory workflow gates or enable unsafe behavior.
- `P1`: Significant consistency drift with moderate delivery risk (stale docs, conflicting workflow guidance).
- `P2`: Minor clarity, naming, or housekeeping drift with low immediate operational risk.

## Allowed Categories

- `stale_doc_reference`
- `policy_conflict`
- `workflow_gate_drift`
- `artifact_requirement_gap`
- `module_traceability_gap`
- `ci_path_drift`
- `naming_or_precedence_drift`
- `strategy_product_boundary_drift`
- `test_coverage_mapping_gap`
- `rule_parser_or_format_risk`

## Canonical Outputs

- `.local/workflow-artifacts/alignment/alignment-audit.md`
- `.local/workflow-artifacts/alignment/alignment-todos.md`

**Focused alignment pass** (architecture-impacting PR, no full enterprise scorecard): `enterprise-auditor` writes only the two files above; scope is the PR's touched docs/code/tests. See `.cursor/skills/enterprise-architecture-audit/SKILL.md` § “Focused alignment pass”.

## Precedence Rule (When Sources Conflict)

1. `.cursor/rules/*` and `AGENTS.md`
2. `.agents/skills/pr-workflow/SKILL.md` and phase skills (`review-pr`, `prepare-pr`, `merge-pr`)
3. `.ai_infra/scripts/pr/prepare.py` (`GATES`) and `.ai_infra/scripts/pr/local_workflow_paths.py`
4. `docs/governance/*`, `docs/operations/*`
5. `docs/roadmap/*`
6. Project overlay rules (`overlays/rules/*.mdc`)

## Minimal JSON Example

```json
{
  "id": "AA-policy-001",
  "severity": "P1",
  "category": "workflow_gate_drift",
  "source_path": "docs/operations/agent-workflow-procedures.md",
  "target_path": ".ai_infra/scripts/pr/prepare.py",
  "evidence": "Prose lists four gates; prepare.py GATES has two.",
  "recommendation": "Point prose to prepare.py only; remove duplicated gate list.",
  "status": "open",
  "owner": "platform-architecture",
  "due_slice": "feature/starter-phase-2"
}
```
