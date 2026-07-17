---
name: project-board-ssot
description: Drive GitHub Project SSOT via project_ssot YAML and cursor_workflow project CLI.
---

<!--
File: SKILL.md
Path: .cursor/skills/project-board-ssot/SKILL.md
Role: Procedural skill for board-first backlog/status + multi-agent continuation on the Project.
Used By:
 - .cursor/agents/project-board.md
 - All kit agents when project_ssot.enabled
Depends On:
 - .local/user_settings/github.collaboration.yaml (project_ssot)
 - .ai_infra/install/cursor_workflow/project_cli.py
 - .ai_infra/docs/operations/project-board-collaboration.md
 - ADR-008-project-board-ssot.md
Notes:
 - Pattern A: one CLI command per action; no dual-write of work-tracker when board_only.
 - Continuation is board-anchored: every agent Entry reads the Project; Exit updates Status.
-->

# Project board SSOT

## Goal

When `project_ssot.enabled` and `sync_policy: board_only`, use the GitHub Project as the **only writable SSOT** for backlog, Status, and multi-agent continuation. Prefer CLI over inventing `gh` flags. Local trackers are offline fallback only; read-only exports never compete with board Status.

**Agent:** `.cursor/agents/project-board.md`  
**Ops mirror:** `.ai_infra/docs/operations/project-board-collaboration.md`  
**ADR:** `.ai_infra/docs/decisions/ADR-008-project-board-ssot.md`

## Continuation contract (all agents — non-negotiable when enabled)

Work is **indexed on the Project**, not in chat alone.

| Phase | Required |
|-------|----------|
| **Entry** | `project status` → find/claim related card (`list --status ready` or your In progress). Read Acceptance / Rollback / Notes on the card body. |
| **During** | Keep **one** In progress card for your assignee. Put progress notes on the card body when handing off mid-slice. |
| **Exit** | **Always** update Status for the card you worked: → `in_review` (PR/handoff) or → `done` (your part closed) or leave `in_progress` with **Notes** naming the next agent. Print handoff line. |
| **Never** | Finish in chat only while leaving the card Stuck in Ready/Backlog. Never dual-write tracker `in_progress` under `board_only`. |

Handoff line (chat + optional card Notes):

```text
item_id=PVTI_… · title=… · Status=before→after · next=implementer|verifier|test-runner|…
```

## When to use

- Any session where `project_ssot.enabled: true`
- Triage, create, claim, Priority/Size, Status transitions
- Multi-agent handoffs (implementer → test-runner → verifier, etc.)

## Evidence contract

- Cite CLI output or `gh project` JSON for claims.
- Label **Unknown** when board unreachable → then `fallback: local_trackers` only.

## Collaboration

### Human vs agent vs GitHub

| Surface | Human | Agents | Derived |
|---------|-------|--------|---------|
| Status / Priority / Size / create cards | Yes | Yes (rights table) | — |
| Ready prioritization / roadmap shape | **Owner** | Consume Ready; create cards for agreed work | — |
| Views, workflows, Insights, Project README, status updates | **Owner only** | **Never** | Insights auto |
| My items | Assign in UI | Claim = Status In progress (assignee CLI TBD) | View filter |
| PR gates, audits, secrets | Local | Local (`local_only`) | — |

### Rules

1. One primary **In progress** per assignee — do not steal others'.
2. Pull from **Ready** or continue your In progress.
3. Acceptance / Rollback / Notes on **card body** = continuation index.
4. Under `board_only`: no competing tracker `in_progress` (DRIFT-009); no dual-mirror “for safety.”
5. Humans own views, workflows, README, Insights, status updates.
6. Read-only `project export` (if used) never writes Status.
7. Post-merge Done is Pattern A (`merge.py`), not a dedicated agent.

### Per-agent rights (what / when / where)

| Agent | Entry (read board) | Exit (must update board) | Local writes |
|-------|--------------------|--------------------------|--------------|
| **project-board** | status + list | create/move any Status; Priority/Size; hand off to implementer | change-index, updates-log |
| **implementer** | status + Ready/claim | In progress → In review (PR) → Done; fields on own card; may create slice cards | code; change-index; PR |
| **test-runner** | status + slice card | Stay on card; → In review when tests gate PR; Done when test-only slice closes | test-index / test-plan |
| **verifier** | status + related card | Confirm → Done or leave In review with Notes (failures) | evidence / PR artifacts |
| **integrator-mas-agent** | status + Ready/claim | claim → Done on integration card; may create cards | integrate / payload |
| **enterprise-auditor** | status + audit card | Audit card → In review/Done; Notes point to artifact paths | `.local/workflow-artifacts/…` |
| **workflow-drift-guard** | **Must** status + list In progress (dual-write check) | Drift-pass card → Done (or In review if P0/P1 need human); cite board Status in drift-audit; hand remediation to project-board/implementer via Ready card or Notes — **do not** silent-edit trackers | drift-audit / drift-todos |
| **researcher** | status + research card if any | If a research card exists → Done + Notes with corpus paths; else read-only | `_research_results/` |

### Status path

```text
Ready → In progress → In review → Done
```

| Moment | Actor | CLI |
|--------|-------|-----|
| Start work | implementer / integrator / test-runner / project-board | `set-status --to in_progress` |
| PR open / peer handoff | implementer | `set-status --to in_review` |
| Part verified closed | implementer / verifier / test-runner | `set-status --to done` |
| Drift / audit pass closed | drift-guard / auditor | `set-status --to done` (their card) |
| Queue triage | project-board or human | create / set-status / set-field |

## Procedure (CLI)

1. **Status:** `python -m cursor_workflow project status --directory .`
2. **List:** `python -m cursor_workflow project list [--status ready|in_progress|in_review] --directory .`
3. **Claim:** `set-status --id PVTI_… --to in_progress`
4. **Create:** `project create --title "…" [--body "…"]`
5. **Fields:** `set-field --id … --field priority|size --to …`
6. **Close / handoff:** `set-status --to in_review|done`
7. **Notes:** `append-notes --id PVTI_… --text "…"` — agents always pass the project item id (`PVTI_…`); CLI resolves DraftIssue content id (`DI_…`) for body edits and keeps Status on `PVTI_…`
8. **Verify:** `project list` matches intent + handoff line printed

## Dual-write ban

When `sync_policy: board_only`, do **not** mark the same slice `in_progress` in `work-tracker.md`. PR/audit artifacts stay local (`local_only`).

## Exit criteria

- [ ] Entry read board (or explicit offline fallback)
- [ ] Exit updated Status (or Notes + next agent if still In progress)
- [ ] Handoff line printed when another agent continues
- [ ] No dual-write; no edits to Project views/workflows/README/Insights

## Anti-patterns

- Chat-only completion with stale board Status
- Hardcoding field/option ids
- Reshuffling Ready/P0 without human or project-board ask
- Editing Project views, workflows, Insights, or status updates
- Dual-write board + tracker under `board_only`
- Port to production kit without PORT-GATE
