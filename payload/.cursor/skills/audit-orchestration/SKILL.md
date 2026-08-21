---
name: audit-orchestration
description: Orchestrate verify-all preflight, auditor (CHK-*), implementer doc-sync, drift-guard goal pulse, and verifier with Task delegation.
---
<!--
File: SKILL.md
Path: .cursor/skills/audit-orchestration/SKILL.md
Role: Phased Task delegation for enterprise audits with script preflight and agent handoffs.
Used By:
 - Maintainers running full audit + closure slices
 - Parent agents orchestrating auditor pipeline
Depends On:
 - .cursor/skills/auditor-protocol/SKILL.md
 - .cursor/skills/drift-audit/SKILL.md
 - .cursor/skills/implementer-loop/SKILL.md
Notes:
 - Human-triggered only; scripts run before prose agents consume results.
 - Full CHK-* on quarterly/release only — not every PR.
-->

# Audit orchestration

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Goal

Run **full audit closure** efficiently: scripts establish facts first; specialized agents write artifacts — without one agent re-running every shell command.

## Cadence

| Trigger | Auditor depth | Drift |
|---------|---------------|-------|
| **Architecture-impacting PR** | Focused alignment + scoped CHK-* | `drift validate` via prepare; optional drift-guard |
| **Quarterly / kit release** | Full EA report + **all CHK-*** | drift-guard goal pulse after implementer |
| **Ad-hoc full audit** | Same as quarterly | Same |

Do **not** run full CHK-* scorecard on every PR.

## When

- Full enterprise architecture audit (scorecard + canvases + closure)
- Post-audit doc-sync and housekeeping PR
- Quarterly kit release readiness review

## Phase 0 — Script preflight (parallel, no prose)

Run **once**; capture JSON for downstream agents:

```bash
make verify-all
# or with artifacts:
python -m agent_colony verify all --write-preflight
python -m agent_colony doc validate --write-preflight
python -m agent_colony drift validate --directory .
```

**MCP (Cursor):** `workflow_verify_all`, `workflow_doc_facts_validate`, `workflow_drift_validate`, `workflow_integrate_validate`, `workflow_activate`.

**Read:** `.local/workflow-artifacts/audit/preflight.json`, `doc-facts-preflight.json` if present.

**Stop on P0** from doc validate or drift; hand to **implementer** only for approved mechanical fixes.

## Phase 1 — Parallel discovery (Task delegation)

| Subagent | Mode | Deliverable |
|----------|------|-------------|
| `auditor` | artifact-write (`.local/` only) | Full: `enterprise-architecture-audit.md` + actions + CHK-* table. PR-scoped: alignment only |
| `audit-module-map` (optional) | artifact-write | `.local/module-map.md` summary for audit §3 |

Parent consumes subagent outputs + preflight JSON — no duplicate inventory searches.

## Phase 2 — Mechanical remediation (user-approved only)

When `enterprise-audit-actions.md` or doc validate lists **DOC-*** items:

| Subagent | Scope |
|----------|-------|
| `implementer` | Tracked doc/template fixes only |

After edits:

```bash
make sync-plugin
make gates
make doc-validate
```

## Phase 3 — Closure artifacts

| Subagent | When |
|----------|------|
| `drift-guard` | After tracker/doc edits; goal pulse + DRIFT-011; P0/P1 drift |
| `verifier` | Spot-check top audit claims vs preflight + repo paths |

## Phase 4 — Maintainer PR

Human or maintainer: `review-pr` → `prepare-pr` → `merge-pr` on `feature/` or `chore/` branch.

## Delegation rules

1. **Scripts before agents** — do not re-run five gates if preflight JSON is fresh (<1 session).
2. **One primary `in_progress`:** board SSOT when enabled; else `work-tracker.md`. No dual-write under `board_only`.
3. **Do not auto-edit** slice scope from audit agents — propose in `enterprise-audit-actions.md`.
4. **Canvases** — optional IDE artifacts; not merge gates.
5. **Token efficiency** — cite preflight pass/fail; paste failing stderr only.
6. **Ownership** — plan/agent-doctrine = `drift-guard`; deep CHK-* = `auditor`.

## Handoff format

Preflight exit · audit artifact paths · CHK-* gaps · P0/P1 counts · branch name · next: implementer | drift-guard | verifier | maintainer PR
