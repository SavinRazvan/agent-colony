---
name: audit-module-map
description: Builds a deep per-module workflow map with importance, goals, and visual architecture output.
---

# Audit module map (advisory-only)

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Relationship to audits

Depth tool for **`auditor`**, not a separate audit authority. Run when enterprise audit (or focused alignment pass) needs HTML/topology evidence. Fold outputs into parent audit citations.

## When

- **`auditor`** requests deep module topology or `module-audit.html` export
- Team needs current module map before architecture reconciliation
- Documentation drift suspected across module boundaries

## Required sources

- `README.md`, `AGENTS.md`
- Project strategy/plan docs (when consumer defines them)
- `tests/modules/*`
- `.cursor/rules/*`, `.cursor/skills/*`
- `.agents/skills/*` (maintainer context)

## Constraints

1. Advisory-only: do not auto-remediate during this audit.
2. Evidence-backed statements only; concrete file paths per claim.
3. Distinguish canonical docs from archival/historical docs.
4. Uncertain ownership → `TBD` + follow-up callout.

## Steps

1. Inventory module roots under `src/`; map test ownership under `tests/modules/`.
2. Per module document: goal, workflow (entrypoints, contracts, control flow), importance (`CRITICAL`|`HIGH`|`MEDIUM`|`LOW`) + rationale, dependencies, dependents.
3. Build architecture-layer graphic (placement + data/control flow).
4. Identify drift/gaps: module-to-test mapping, doc coverage, rules/skill guidance.
5. Emit:
   - `.local/module-map.md`
   - `.local/agents-control-center/audits/module-audit.html`
   - Optional: append to `alignment-audit.md` + `alignment-todos.md`

## Output contract (per module)

`module_name` · `source_paths` · `test_paths` · `importance` · `goal` · `workflow` · `key_contracts` · `dependencies` · `dependents` · `evidence` · `gaps_or_risks`

## Exit criteria

- Every production module has ownership entry (or `TBD` + rationale).
- Architecture graphic and module deep-dive are readable.
- Rules/skills/agent updates listed with evidence when needed.
