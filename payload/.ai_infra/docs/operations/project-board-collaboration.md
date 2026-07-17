<!--
File: project-board-collaboration.md
Path: .ai_infra/docs/operations/project-board-collaboration.md
Role: Ops mirror — Project surfaces + per-agent Entry/Exit continuation on the board.
Used By:
 - .cursor/skills/project-board-ssot/SKILL.md
 - .cursor/agents/*.md
 - AGENTS.md / HANDOFF.md
Depends On:
 - github.collaboration.yaml project_ssot
 - ADR-008
Notes:
 - When enabled, every agent reads the Project on Entry and updates Status on Exit.
-->

# Project board collaboration (agents + humans)

When `project_ssot.enabled` and `sync_policy: board_only`, the **GitHub Project is the only writable SSOT** for backlog, Status, and continuation. Local trackers are offline fallback only; read-only exports never compete with Status. Canonical skill: `.cursor/skills/project-board-ssot/SKILL.md`.

## Continuation (why agents update the board)

| Without board Exit | With board Exit |
|--------------------|-----------------|
| Next agent guesses from chat | Next agent lists Ready / In progress / In review |
| Status drifts from reality | Status column = truth (DRIFT-009 watches dual-write) |
| Humans cannot see progress | Project UI is the shared dashboard |

**Rule:** Entry = read board. Exit = update Status (and Notes) for the card you touched.

## Surfaces — who may write

| Surface | Human | Agents | GitHub |
|---------|-------|--------|--------|
| Card Status | Yes | Yes — every agent Exit | — |
| Priority / Size | Yes | Triage + own card | — |
| Create cards | Yes | project-board, implementer, integrator | — |
| Ready prioritization | **Owner** | Consume; create agreed work | — |
| Views / workflows / Insights / README / status updates | **Owner only** | Never | Insights auto |
| Assignee / My items | Yes | Claim = In progress | My items view |
| PR / audits / secrets | Local | Local | — |
| Post-merge Status → Done | — | Via `merge.py` (Pattern A) | — |
| Read-only board export | Consume | `project export` (never writes Status) | — |

## Per-agent Entry / Exit

| Agent | Entry | Exit (board) |
|-------|-------|--------------|
| **project-board** | status + list | Full triage; handoff to implementer |
| **implementer** | status + Ready/claim | →In review / →Done; Notes for next |
| **test-runner** | status + slice card | →In review or →Done when tests finish |
| **verifier** | status + related card | →Done or leave In review + Notes |
| **integrator-mas-agent** | status + claim | →Done on integration card |
| **enterprise-auditor** | status + audit card | →In review/Done; Notes → artifact paths |
| **workflow-drift-guard** | **Must** status + list In progress | Drift card →Done; cite board in drift-audit; remediation via Notes/Ready handoff — no silent tracker edits |
| **researcher** | status (+ research card) | Research card →Done + corpus paths in Notes |

## Status path

```text
Ready → In progress → In review → Done
```

Handoff: `item_id=PVTI_… · Status=a→b · next=<agent>`

## workflow-drift-guard specifically

1. **Read board first** (`project status`, `list --status in_progress`) so dual-write checks compare board Status vs trackers.
2. Run `drift validate` (includes DRIFT-009 / DRIFT-010 when board_only; refresh `project export` for DRIFT-010).
3. Write `.local/workflow-artifacts/drift/*` (evidence stays local).
4. **Update board:** close the drift-pass card; if dual-write Confirmed, add Notes on the offending card or ask project-board to queue a Ready fix — do not write competing `in_progress` into `work-tracker.md`.

## Human-only

Views, workflows, Insights, Project README, status updates, Ready prioritization, PORT-GATE.
