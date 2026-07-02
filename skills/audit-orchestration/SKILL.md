---
name: audit-orchestration
description: Orchestrate verify-all preflight, enterprise-auditor, implementer doc-sync, drift-guard, and verifier with Task delegation.
---
<!--
File: SKILL.md
Path: .cursor/skills/audit-orchestration/SKILL.md
Role: Phased Task delegation for enterprise audits with script preflight and agent handoffs.
Used By:
 - Maintainers running full audit + closure slices
 - Parent agents orchestrating enterprise-auditor pipeline
Depends On:
 - .cursor/skills/enterprise-architecture-audit/SKILL.md
 - .cursor/skills/workflow-drift-audit/SKILL.md
 - .cursor/skills/implementation-execution-loop/SKILL.md
Notes:
 - Human-triggered only; scripts run before prose agents consume results.
-->

# Audit orchestration

## Goal

Run a **full audit closure** efficiently: scripts establish facts first; specialized agents write artifacts and apply approved fixes — without one agent re-running every shell command.

## When

- Full enterprise architecture audit (scorecard + canvases + closure)
- Post-audit doc-sync and housekeeping PR
- Quarterly kit release readiness review

## Phase 0 — Script preflight (parallel, no prose)

Run **once**; capture JSON for downstream agents:

```bash
make verify-all
# or with artifacts for agents:
python -m cursor_workflow verify all --write-preflight
python -m cursor_workflow doc validate --write-preflight
```

**MCP (preferred in Cursor):** `workflow_verify_all`, `workflow_doc_facts_validate`, `workflow_drift_validate`, `workflow_integrate_validate`, `workflow_activate`.

**Read:** `.local/workflow-artifacts/audit/preflight.json` and `doc-facts-preflight.json` if present.

**Stop on P0** from doc validate or drift; hand to **implementer** only for mechanical fixes the user approved.

## Phase 1 — Parallel discovery (Task delegation)

Launch concurrently:

| Subagent | Mode | Deliverable |
|----------|------|-------------|
| `enterprise-auditor` | artifact-write (`.local/` only) | `enterprise-architecture-audit.md`, `enterprise-audit-actions.md` |
| `audit-module-map` skill (optional) | artifact-write (`.local/` only) | `.local/module-map.md` summary for audit §3 |

Parent **does not** duplicate inventory searches — consumes subagent outputs + preflight JSON.

## Phase 2 — Mechanical remediation (user-approved only)

When `enterprise-audit-actions.md` or doc validate lists **DOC-*** / doc-sync items:

| Subagent | Scope |
|----------|-------|
| `implementer` | Tracked doc/template fixes only; no scope creep |

After edits:

```bash
make sync-plugin
make gates
make doc-validate
```

## Phase 3 — Closure artifacts

| Subagent | When |
|----------|------|
| `workflow-drift-guard` | After tracker/doc edits; P0/P1 drift findings |
| `verifier` | Spot-check top audit claims vs preflight + repo paths |

## Phase 4 — Maintainer PR

Human or maintainer agent: `review-pr` → `prepare-pr` → `merge-pr` on a `feature/` or `chore/` branch.

## Delegation rules

1. **Scripts before agents** — never let an agent re-run five gates if preflight JSON is fresh (<1 session).
2. **One primary `in_progress`** in `work-tracker.md` during implementer slice.
3. **Do not auto-edit** `plan.md` / `work-tracker.md` from audit agents — propose in actions file.
4. **Canvases** — optional IDE artifacts; not merge gates.
5. **Token efficiency** — cite preflight pass/fail in chat; paste failing command output only.

## Handoff format

Preflight exit • audit artifact paths • P0/P1 counts • branch name • suggested next: implementer | drift-guard | verifier | maintainer PR
