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

**Rule:** Entry = read board. Exit = update Status and **attributed Notes** for the card you touched. Prefer Pattern A recipes: `project claim` / `project handoff` (one command each). Atomics (`append-notes --agent`) remain for power use. **Never** paste Project settings UI text into a shell — humans paste `.ai_infra/templates/project-board/project-readme.md` into Project README settings.

## Surfaces — who may write

| Surface | Human | Agents | GitHub |
|---------|-------|--------|--------|
| Card Status | Yes | Yes — every agent Exit | — |
| Priority / Size | Yes | Triage + own card | — |
| Start date | Yes (UI) | Claim sets UTC today when `set_start_date_on_claim` + `fields.start_date.field_id` | — |
| Estimate | Yes (UI) | Triage + own card — `set-field --field estimate --to N` | — |
| Promote Draft→Issue | Yes (UI) | `promote-to-issue --last --agent <name> [--repo owner/repo]` | GraphQL `convertProjectV2DraftIssueItemToIssue`; same `PVTI_`; Assignees + Linked PRs after promote; Notes `promoted to Issue #N`; fine-grained PAT caveat (`doctor` / `guide`); claim does **not** auto-promote |
| Linked PRs | Yes (UI link) | `mention-pr --pr N` → Notes with PR URL; auto-promotes Draft when `promote_to_issue_on_pr` (default true) — FAIL if promote fails; WARN-only if false | GitHub **Linked pull requests** column derived from Issue↔PR (works after Issue) |
| Create cards | Yes | project-board, implementer, integrator | — |
| Ready prioritization | **Owner** | Consume; create agreed work | — |
| Views / workflows / Insights / README / status updates | **Owner only** | Never | Insights auto |
| Assignee / My items | Yes (`set-assignee` / UI) | Claim = In progress; assignee = **human** only | My items view |
| Card Notes (`append-notes --agent`) | Yes | Yes — `@user/agent · YYYY-MM-DDTHH:MM:SSZ · …`; `next=@user/agent` | — |
| PR / audits / secrets | Local | Local | — |
| Post-merge Status → Done | — | Via `merge.py` (Pattern A); Notes `@user/merge.py` | — |
| Read-only board export | Consume | `project export` (never writes Status) | — |

## Per-agent Entry / Exit

| Agent | Entry | Exit (board) |
|-------|-------|--------------|
| **project-board** | status + list | Full triage; handoff to implementer |
| **implementer** | status + `claim --agent implementer` | `handoff --agent implementer --next … --to in_review` or →Done |
| **test-runner** | status + slice card | →In review or →Done; `--agent test-runner` |
| **verifier** | status + related card | →Done or leave In review; `--agent verifier` |
| **integrator-mas-agent** | status + claim | →Done; `--agent integrator-mas-agent` |
| **enterprise-auditor** | status + audit card | →In review/Done; `--agent enterprise-auditor` + artifact paths |
| **workflow-drift-guard** | **Must** status + list In progress | Drift card →Done; `--agent workflow-drift-guard`; remediation via Notes/Ready — no silent tracker edits |
| **researcher** | status (+ research card) | Research card →Done; `--agent researcher` + corpus paths |

## Status path

```text
Ready → In progress → In review → Done
```

Handoff: `item_id=<from create or --last> · @User/implementer · Status=a→b · next=@User/verifier`

**Safe flow:** `project guide` then `create-from-template` → `claim --last` → `handoff --last`. Never paste docs placeholder ids as `--id`.

**Attribution:** Notes use `@owner.github_user/<agent> · <ISO-8601-UTC> · …` from each collaborator’s `github.collaboration.yaml` (CLI stamps UTC; do not hand-forge timestamps). Local `history/continuity-index.md` rolls ≥3 days; board Notes keep full card lifetime.

## workflow-drift-guard specifically

1. **Read board first** (`project status`, `list --status in_progress`) so dual-write checks compare board Status vs trackers.
2. Run `drift validate` (includes DRIFT-009 / DRIFT-010 when board_only; refresh `project export` for DRIFT-010).
3. Write `.local/workflow-artifacts/drift/*` (evidence stays local).
4. **Update board:** close the drift-pass card; if dual-write Confirmed, add Notes on the offending card or ask project-board to queue a Ready fix — do not write competing `in_progress` into `work-tracker.md`.

## Rate limits & outbox

GitHub GraphQL quota (~5000/hour) can block board writes. When `project_ssot.outbox.enabled`:

1. Live write fails with rate-limit → CLI **enqueues** to `.local/generated-data/board-outbox.jsonl` and returns **EXIT_QUEUED (6)**.
2. Agent continues local evidence (`change-index`, handoff line) — **do not** hammer `gh` / retry loops.
3. After quota recovers: `python3 -m cursor_workflow project outbox status` then `outbox flush` (capped by `max_flush_per_run`; refuses if `remaining < min_graphql_remaining`).
4. Explicit enqueue: `project queue --op append-notes|set-status|handoff|claim|set-assignee|set-field …`
5. Outbox is a **local buffer**, never a second Status SSOT.

Who flushes: any agent/human after reset; prefer implementer or project-board at slice close. Pending outbox is **not** a DRIFT failure.

## Exit codes (board Pattern A)

| Code | Meaning |
|------|---------|
| 0 | Success |
| 2 | Usage / config / policy |
| 3 | `gh` / network |
| 4 | Item not found |
| 5 | Validation (sections, claim policy, attribution) |
| 6 | Queued to outbox (soft-success; flush later) |

Stderr: `project <cmd>: FAIL — CODE=n · reason` or `QUEUED — …`.

## Human-only

Views, workflows, Insights, Project README, status updates, Ready prioritization / product roadmap. Paste README from `.ai_infra/templates/project-board/project-readme.md` in the GitHub UI only.
