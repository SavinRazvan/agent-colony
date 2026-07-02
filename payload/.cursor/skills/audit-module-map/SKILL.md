---
name: audit-module-map
description: Builds a deep per-module workflow map with importance, goals, and visual architecture output.
---

# Audit Module Map (Advisory-Only)

## Relationship to audits

This is a **depth tool** for **`enterprise-auditor`**, not a separate audit authority. Run it when the enterprise architecture audit (or a focused alignment pass) needs HTML/topology evidence; fold outputs into the parent audit’s citations.

## Goal

Produce a module-by-module audit that explains workflow, behavior, importance, and intended goal, with a visual architecture map and detailed results.

## When to Use

- **`enterprise-auditor`** requests deep module topology or `module-audit.html` export.
- Team needs a current module map before architecture reconciliation.
- Documentation drift is suspected across module boundaries and ownership.

## Required Sources

- `README.md` and `AGENTS.md`
- Project strategy/plan docs (when the consumer repo defines them)
- `tests/modules/*` (or project test tree)
- `.cursor/rules/*` and `.cursor/skills/*`
- `.agents/skills/*` (maintainer workflow context)

## Mandatory Constraints

1. Advisory-only: do not auto-remediate findings during this audit.
2. Use evidence-backed statements only; include concrete file paths for each claim.
3. Distinguish canonical current-state docs from archival/historical docs.
4. Mark uncertain ownership as `TBD` and call out required follow-up.

## Execution Steps

1. Inventory module roots under `src/` and map corresponding test ownership under `tests/modules/`.
2. For each module, document:
   - goal
   - workflow/how it works (entrypoints, key contracts, control flow)
   - importance (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`) with rationale
   - key dependencies and key dependents
3. Build an architecture-layer graphic showing module placement and directional data/control flow.
4. Identify drift/gaps in:
   - module-to-test mapping
   - module documentation coverage
   - rules/skill guidance needed for repeatable audits
5. Emit:
   - `.local/module-map.md` (detailed module catalog)
   - `.local/agents-control-center/audits/module-audit.html` (visual report with architecture graphic and per-module cards)
   - Optional reconciliation findings appended into `.local/workflow-artifacts/alignment/alignment-audit.md` and `.local/workflow-artifacts/alignment/alignment-todos.md`

## Output Contract

For each module entry, include:

- `module_name`
- `source_paths`
- `test_paths`
- `importance`
- `goal`
- `workflow`
- `key_contracts`
- `dependencies`
- `dependents`
- `evidence`
- `gaps_or_risks`

## Exit Criteria

- Every production module has an explicit ownership/mapping entry (or `TBD` with rationale).
- The architecture graphic and module deep-dive results are generated and readable.
- Any accuracy-improving updates needed for rules/skills/agents are explicitly listed with evidence.
