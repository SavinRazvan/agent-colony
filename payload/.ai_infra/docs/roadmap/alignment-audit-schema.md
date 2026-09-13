<!--
File: alignment-audit-schema.md
Path: .ai_infra/docs/roadmap/alignment-audit-schema.md
Role: Required fields and taxonomy for advisory alignment audit findings (.local/workflow-artifacts/alignment/).
Used By:
 - .cursor/skills/auditor-protocol/SKILL.md
 - auditor alignment passes
 - .cursor/rules/advisory-audit-alignment-enforcement.mdc
Depends On:
 - docs/governance/workflow-source-owners.md
 - .ai_infra/scripts/workflow/audit_artifact_schema.py
Notes:
 - Universal Agent Colony schema; product-specific vocabulary belongs in project overlays.
 - Last reviewed: 2026-09-13
-->

# Alignment Audit Schema

## Purpose

Standardize advisory audit findings so outputs from skills, rules checks, and manual review merge into one deterministic report.

**Product vocabulary:** When findings involve domain boundaries, cite your project's strategy/architecture docs as `target_path` (e.g. `docs/architecture/*`, overlay rules in `overlays/rules/`).

## Artifact-level frontmatter (Audit-Schema: 1)

When an artifact opts in with `Audit-Schema: 1`, these fields apply at the document level:

| Field | Required | Description |
|---|---|---|
| `Audit-Schema` | yes (opt-in) | Set to `1` to enable machine validation |
| `Audit-Scope` / `audit_scope` | yes when schema 1 | `kit` \| `product` \| `model` \| `dataset` \| `ecosystem` \| `meta` |
| `Named-Target` | yes when schema 1 | Non-empty subject of the audit (repo, module, release, etc.) |
| `Assurance-Level` | reserved | `high` \| `reasonable` \| `limited` \| `very_limited` — caps when P0/P1 evidence is thin |
| `Commissioned-By` | recommended | Human or role that requested the pass |

Mandatory sections: **`## Accountability summary`** and **`## Audit limits`** — state what the audit covers at a glance and what it does **not** cover (see evidence-first audit scope boundary).

Validator: `.ai_infra/scripts/workflow/audit_artifact_schema.py` · gate: `check_audit_artifacts.py`. Architecture-impacting merges use `--arch-impacting` (both alignment files must exist, carry `Audit-Schema: 1`, and pass — no skip).

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
| `owner` | `string` | P0/P1 | Responsible person or role (non-placeholder). |
| `due_slice` | `string` | P0/P1 | Planned implementation slice (or `deadline`). |
| `consequence_if_ignored` | `string` | P0/P1 | What happens if the finding is not addressed. |
| `expectation` | `string` | optional | Desired end state when helpful. |

**P2:** `owner`, `due_slice`, and `consequence_if_ignored` are optional.

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
- `token_contract`

## Canonical Outputs

- `.local/workflow-artifacts/alignment/alignment-audit.md`
- `.local/workflow-artifacts/alignment/alignment-todos.md`

**Focused alignment pass** (architecture-impacting PR, no full enterprise scorecard): `auditor` writes only the two files above; scope is the PR's touched docs/code/tests. See `.cursor/skills/auditor-protocol/SKILL.md` § “Focused alignment pass”.

## Precedence Rule (When Sources Conflict)

1. `.cursor/rules/*` and `AGENTS.md`
2. `.agents/skills/pr-workflow/SKILL.md` and phase skills (`review-pr`, `prepare-pr`, `merge-pr`)
3. `.ai_infra/scripts/pr/prepare.py` (`resolve_gates()`; `GATES` = 2-gate alias) and `.ai_infra/scripts/pr/local_workflow_paths.py`
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
  "evidence": "Prose gate count stale; see resolve_gates() in prepare.py for authoritative kit-dev append list.",
  "recommendation": "Point prose to prepare.py resolve_gates() only; remove duplicated gate list.",
  "status": "open",
  "owner": "platform-architecture",
  "due_slice": "feature/starter-phase-2",
  "consequence_if_ignored": "merge prep may pass with outdated gate documentation"
}
```
