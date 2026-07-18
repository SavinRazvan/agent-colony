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
 - Pattern A: prefer recipes (claim/handoff/create-from-template); atomics for power use; no dual-write when board_only.
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
| **Exit** | **Always** update Status for the card you worked: → `in_review` (PR/handoff) or → `done` (your part closed) or leave `in_progress` with **Notes** naming the next agent. Notes **must** use `append-notes --agent <this-agent>` → `@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · …` (CLI stamps UTC). Print handoff line. **If EXIT_QUEUED (6)** / rate-limit: do **not** retry in a loop — op is in `.local/generated-data/board-outbox.jsonl`; continue local evidence; later `project outbox flush`. |
| **Never** | Finish in chat only while leaving the card Stuck in Ready/Backlog. Never dual-write tracker `in_progress` under `board_only`. Never write bare `Agent: implementer` without `@user/` namespace. |

Handoff line (chat + card Notes):

```text
item_id=<from project last or create> · @User/implementer · Status=before→after · next=@User/verifier
```

Prefer `--last` after create so agents never invent ids.

Multi-collaborator: each human’s `owner.github_user` namespaces their agents (`@Alice/implementer` vs `@Bob/implementer`) on the same board.
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
| My items | Assign in UI or `project set-assignee` (human login) | Claim = Status In progress + Notes `@user/agent`; assignee = human only | View filter |
| PR gates, audits, secrets | Local | Local (`local_only`) | — |

### Tier-1 board fields (agents)

| Field / action | When | CLI | Notes |
|----------------|------|-----|-------|
| **Start date** | Claim | `project claim --last --agent <agent>` | UTC today when `conventions.set_start_date_on_claim: true` and `fields.start_date.field_id` is set; WARN only on failure — claim still succeeds |
| **Estimate** | Triage / own card | `project set-field --field estimate --to N` | Number field; N ≥ 0 |
| **Linked PR** | PR open | `project mention-pr --pr N --last --agent <agent>` | Appends Notes with canonical PR URL; GitHub **Linked pull requests** column is derived (Issue↔PR; DraftIssue warns) |
| **Out of scope (agents default)** | — | — | Iteration, Labels, Reviewers, End date — human / UI only |

### Rules

1. One primary **In progress** per **human assignee** — do not steal others'.
2. Pull from **Ready** or continue your In progress.
3. Acceptance / Rollback / Notes on **card body** = continuation index. Attribution = `@owner.github_user/<agent> · <ISO-8601-UTC> · …` via `append-notes --agent` (or `claim`/`handoff` recipes).
4. Under `board_only`: no competing tracker `in_progress` (DRIFT-009); no dual-mirror “for safety.”
5. Humans own views, workflows, README, Insights, status updates.
6. Read-only `project export` (if used) never writes Status.
7. Post-merge Done is Pattern A (`merge.py`), Notes prefixed `@user/merge.py`.

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

## Procedure (CLI) — prefer Pattern A recipes

**Never paste docs placeholders as `--id`.** After create, use `--last`. Print recipes: `project guide`.

Human Project README: paste `.ai_infra/templates/project-board/project-readme.md` in the Project settings UI (not into a shell).

### Template routing

| Need | Who | Template / action |
|------|-----|-------------------|
| slice / feature / `chore/` | implementer, project-board, integrator | `create-from-template --template slice` |
| bug / defect / `fix/` | implementer, project-board | `create-from-template --template bug` |
| audit pass | enterprise-auditor | `--template slice` + title `[AUDIT] …` then `claim --last` |
| consume existing card | test-runner, verifier | **No** `create-from-template` — claim/continue only |
| Project README | **Humans only** | paste `project-readme.md` in Project settings UI |

Index: `.ai_infra/templates/project-board/README.md`. After create, always `claim --last` / `handoff --last` (never invent ids).

**Notes format:** `@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · text` — auto-stamped by CLI on `claim`, `handoff`, and `append-notes --agent`. Idempotent when timestamp already present. Do not hand-forge times.

**Local continuity:** append UTC-prefixed lines to `history/updates-log.md`; optional row in `history/continuity-index.md` (rolling ≥3 days). Board Notes retain full card lifetime.

1. **Doctor / guide:** `project doctor` · `project guide --agent implementer`
2. **Status / list:** `project status` · `project list [--status ready|in_progress|in_review]`
3. **Create:** `project create-from-template --title "[SLICE] short-name" --template slice --status ready`
4. **Claim:** `project claim --last --agent <this-agent>`
5. **Handoff:** `project handoff --last --agent <this-agent> --next <agent> [--to in_review|done]`
6. **Validate:** `project validate-item --last`
7. **Atomics (power use):** `set-status` · `set-field` (priority · size · estimate) · `mention-pr` · `append-notes --agent` · `get --last` · `export`
8. **Verify:** `project list` + handoff line; `project last` prints saved id

Exit codes: `0` ok · `2` usage/config (includes placeholder `--id`) · `3` gh · `4` not found · `5` validation · `6` queued (outbox; soft-success — flush later).

Rate-limit: `project outbox status` / `project queue` / `project outbox flush` — see `project_ssot.outbox` in collaboration YAML.

## Dual-write ban

When `sync_policy: board_only`, do **not** mark the same slice `in_progress` in `work-tracker.md`. PR/audit artifacts stay local (`local_only`).

## Exit criteria

- [ ] Entry read board (or explicit offline fallback)
- [ ] Exit updated Status (or Notes + next agent if still In progress)
- [ ] If EXIT_QUEUED: confirmed via `outbox status`; no API hammering
- [ ] Handoff line printed with real item_id
- [ ] Handoff line printed when another agent continues
- [ ] No dual-write; no edits to Project views/workflows/README/Insights

## Anti-patterns

- Chat-only completion with stale board Status
- Hardcoding field/option ids
- Reshuffling Ready/P0 without human or project-board ask
- Editing Project views, workflows, Insights, or status updates
- Pasting Project settings UI text into a terminal
- Dual-write board + tracker under `board_only`
- Multi-step claim without `project claim` / bare Notes without `--agent`
- Do not push to upstream mas-workflow-kit
