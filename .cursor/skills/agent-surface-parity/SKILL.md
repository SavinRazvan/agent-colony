---
name: agent-surface-parity
description: Deep per-agent map of card, skills, CLI/MCP, docs, and canvases vs machine truth; Schema-1 findings for implementer remediations.
Audit-Schema: 1
Audit-Scope: kit
Named-Target: agent surface parity
Commissioned-By: maintainer workflow
---
<!--
File: SKILL.md
Path: .cursor/skills/agent-surface-parity/SKILL.md
Role: Auditor-owned deep per-agent doc/canvas parity vs card + machine enforcement.
Used By:
 - .cursor/agents/auditor.md
 - .cursor/skills/auditor-protocol/SKILL.md
Depends On:
 - .cursor/skills/evidence-first/SKILL.md
 - .ai_infra/docs/roadmap/alignment-audit-schema.md
 - .cursor/skills/board-ssot/SKILL.md
 - .ai_infra/scripts/pr/local_workflow_paths.py
Notes:
 - Advisory-only during the audit pass. Remediations → implementer. Disproof → verifier.
 - Not a substitute for drift validate or full enterprise CHK-* scorecard.
-->

# Agent surface parity

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

- Docs or canvases may not match how an agent actually works
- After Exit / gate / verifier-before-Done changes
- Before claiming “agent X canvas is current”
- Kit `[AUDIT]` cards scoped to agent-surface / DOC-ALIGN content parity

**Hard boundary:** Findings only. Do not edit `.cursor/agents`, canvases, or ops docs in this pass. Do not replace `drift validate` or full enterprise CHK-* .

## Inventory

For each kit agent id, open every layer (blank → **Unknown**):

| Layer | Must open / search |
|-------|-------------------|
| Card | `.cursor/agents/<id>.md` (mirrors via `sync_plugin_bundle` later) |
| Primary skill(s) | Card Read first + AGENTS.md role table |
| Board Exit | `board-ssot` § Continuation / Verifier-before-Done |
| Machine | Grep CLI/MCP/tests per [Per-agent roots](#per-agent-roots) |
| Docs | AGENTS row; `project-board-collaboration` Exit row; gate-matrix / README only if they name the agent |
| Canvas | `canvases/agent-<id>.canvas.tsx` + hubs when they name Exit/gates for that agent |

**Matrix columns:** `Surface | Doc/canvas claim | Evidence path | Match? (Yes/No/Unknown) | Severity | Notes`

Evidence labels: Confirmed / Probable / Unknown — `evidence-first` skill.

Hubs when Exit/gate prose appears: `agent-relations`, `agent-board-collaboration`, `agents-artifacts-board`, `board-ssot-vs-trackers`.

## Steps

1. Pick one or more agent ids for this wave.
2. Open Inventory layers for each id; cite paths or mark Unknown.
3. Fill one matrix per agent under Artifacts depth path.
4. If `alignment/alignment-audit.md` (or todos) already exists and is still relevant, **copy** both to `alignment/archive/YYYYMMDDTHHMMZ-<slug>-audit.md` (+ todos twin) before overwrite.
5. Write Schema-1 tip pair for **this wave** (canonical alignment paths). Finding ids `AA-ASP-<agent>-<nn>`. Categories from allowlist only (`stale_doc_reference`, `workflow_gate_drift`, `policy_conflict`, `module_traceability_gap`, …).
6. Frontmatter: `Commissioned-By` ≠ `Audited-By` (ADR-013 / DRIFT-017). Include `## Accountability summary` + `## Audit limits`.
7. Board Notes cite artifact paths. Shippable `[AUDIT]` → `handoff --next verifier --to in_review`.

## Artifacts

| Path | Role |
|------|------|
| `.local/workflow-artifacts/audit/agent-surface/<id>.md` | Depth matrix + method |
| `.local/workflow-artifacts/alignment/alignment-audit.md` | Schema-1 rollup tip for this wave’s PR |
| `.local/workflow-artifacts/alignment/alignment-todos.md` | `AA-ASP-*` findings |
| `.local/workflow-artifacts/alignment/archive/*` | Prior tip copies |

**Frontmatter (tip pair):**

```text
Audit-Schema: 1
Audit-Scope: kit
Named-Target: agent-surface parity (<ids>)
Audit-Type: agent-surface-parity
Commissioned-By: <human or board owner>
Audited-By: auditor
Action-By: <name>
GitHub-User: <handle>
Date: <ISO-8601>
```

Depth matrices are never the merge tip alone — `--arch-impacting` requires the canonical alignment pair.

## Overlap

| Concern | Owner |
|---------|-------|
| DRIFT scripts / goal pulse | `drift-guard` + `drift-audit` |
| Module topology | `audit-module-map` |
| Full CHK-* enterprise | `auditor-protocol` |
| Claim disproof after remediations | `verifier` |
| Apply doc/canvas fixes | `implementer` (+ `canvas sync`, `sync_plugin_bundle`) |

## Exit

- Notes cite `audit/agent-surface/` + alignment paths.
- `[AUDIT]` / shippable → verifier hop before Done (CLI EXIT_VALIDATION without hop / allow-skip).
- Prefer MCP `workflow_check_audit_artifacts` before handoff.

## Per-agent roots

Minimum machine/doc roots — cite or mark Unknown:

| Agent | Primary skill(s) | Machine / tests (start here) |
|-------|------------------|------------------------------|
| `verifier` | `evidence-first`, board-ssot Verifier-before-Done | `project_atomics` (`item_is_shippable`, `assert_verifier_ready_for_done`); `validate-item`; MCP `workflow_project_validate_item`, `workflow_run_gate`; `tests/modules/**/test_verifier_before_done.py` |
| `implementer` | `implementer-loop`, board-ssot | `prepare.py` / `resolve_gates`; claim/handoff Exit; PR Pattern A skills |
| `test-runner` | `test-coverage` | pytest/coverage paths; Exit when tests gate PR |
| `auditor` | `auditor-protocol`, `audit-orchestration`, `audit-module-map`, **this skill** | Schema-1 alignment paths; `check_audit_artifacts`; MCP `workflow_check_audit_artifacts`; ADR-013 independence |
| `drift-guard` | `drift-audit` | `drift validate` / `drift_checks.py` DRIFT-001…017; write scope drift artifacts only |
| `board` | `board-ssot`, `board-shell` | `board-bootstrap`, doctor, heal-cards; human-owned views |
| `integrator` | `integrator-protocol` | `integrate validate` INT-*; registry parity |
| `researcher` | `research-corpus` | research CLI; `_research_results/`; **no product code** hard boundary |
| `debugger` | `debug-protocol`, `debug-handoff`, lazy `debug-*` | `agent_colony debug` CLI; `.local/workflow-artifacts/debug/`; not on consumer_lite |
