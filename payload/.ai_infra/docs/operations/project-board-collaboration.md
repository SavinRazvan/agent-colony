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

**First-time consumer setup:** step-by-step checklist in [PLUGIN-USER-GUIDE.md § Consumer project_ssot onboarding](PLUGIN-USER-GUIDE.md#consumer-project_ssot-onboarding-checklist) (install → collab YAML → `gh auth` → `project doctor` → `/project-board` + `board-bootstrap --check` + human views-setup/README → `project status` → first card → outbox flush).

## Continuation (why agents update the board)

| Without board Exit | With board Exit |
|--------------------|-----------------|
| Next agent guesses from chat | Next agent lists Ready / In progress / In review |
| Status drifts from reality | Status column = truth (DRIFT-009 watches dual-write) |
| Humans cannot see progress | Project UI is the shared dashboard |

**Rule:** Entry = read board. Exit = update Status and **attributed Notes** for the card you touched. `validate-item` checks the card body, Tier-1 fields (including Assignee when present on the snapshot), and status-scoped Notes; it is not just a section-presence check. **Enforcement:** `handoff` and `set-status` to `in_review`|`done` call the same checks and return EXIT_VALIDATION (5) while Acceptance/Rollback are empty or `(TBD)` (including `- (TBD)` list form). Fill via `create-from-template --acceptance/--rollback` or `project set-section --section acceptance|rollback --text '…' --last`. Prefer Pattern A recipes: `project claim` / `project handoff` (one command each). Atomics (`append-notes --agent`, `set-section`) remain for power use. **Never** paste Project settings UI text into a shell — humans **follow** `.ai_infra/templates/project-board/views-setup.md` and paste **contents of** `project-readme.md` into Project README settings (or opt-in `board-bootstrap --check --apply-readme`).

### Board shell starter (first-run)

- **Desired state:** `.ai_infra/templates/project-board/board-shell.schema.yaml` — **full Playground default** (six views + Tier-1 columns).
- **Customize:** copy/edit `.local/user_settings/board-shell.schema.yaml` — `board-bootstrap --check` prefers the overlay when present. Do **not** remove Status / Priority / Size / Estimate / Start date, or hide **Priority** on Prioritized backlog.
- **Coach:** `/project-board` + `.cursor/skills/board-shell-onboard/SKILL.md`.
- **Verify:** `python3 -m cursor_workflow project board-bootstrap --check` (FAIL if a default Playground view is missing; **FAIL (exit 5)** on missing Tier-1 columns; WARN on leftover `View N` / layout mismatch).
- **Optional API:** `--ensure-fields` (create missing field definitions + print suggested YAML ids); `--apply-readme` (push README). Views stay human UI (ADR-008).

## Surfaces — who may write

| Surface | Human | Agents | GitHub |
|---------|-------|--------|--------|
| Card Status | Yes | Yes — every agent Exit | — |
| Priority / Size | Yes | Triage + own card | — |
| Start date | Yes (UI) | Set UTC today when Status → `in_progress` if empty (`claim`, `set-status`, `handoff --to in_progress`) when `set_start_date_on_claim` + `fields.start_date.field_id` | — |
| Estimate | Yes (UI) | Triage + own card — `set-field --field estimate --to N` (points; Size↔Estimate table in skill) | — |
| Promote Draft→Issue | Yes (UI) | `promote-to-issue --last --agent <name> [--repo owner/repo]` | GraphQL `convertProjectV2DraftIssueItemToIssue`; same `PVTI_`; Assignees + Linked PRs after promote; Notes `promoted to Issue #N`; fine-grained PAT caveat (`doctor` / `guide`); claim does **not** auto-promote |
| Linked PRs | Yes (UI link) | `mention-pr --pr N` → Notes with PR URL; auto-promotes Draft when `promote_to_issue_on_pr` (default true) — FAIL if promote fails; WARN-only if false | GitHub **Linked pull requests** column derived from Issue↔PR (works after Issue) |
| Create cards | Yes | project-board, implementer, integrator | — |
| Ready prioritization | **Owner** | Consume; create agreed work | — |
| Views / workflows / Insights / status updates | **Owner only** | Never mutate views | Insights auto |
| Project README | **Owner** (paste) | Opt-in `board-bootstrap --apply-readme` only | — |
| Assignee / My items | Yes (`set-assignee` / UI) | `create-from-template` assigns `owner.github_user` on Issues (default); claim re-asserts if empty; assignee = **human** only | My items view |
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
| **researcher** | status (+ research card) | Research card →Done; `--agent researcher` + `AGENT_BRIEF` / pack paths (adaptive intake from chat/Notes) |

## Status path

```text
Ready → In progress → In review → Done
```

Handoff: `item_id=<from create or --last> · @User/implementer · Status=a→b · next=@User/verifier`

**Safe flow:** `project guide` then `create-from-template` → `claim --last` → `handoff --last`. Never paste docs placeholder ids as `--id`.

**Attribution:** Notes use `@owner.github_user/<agent> · <ISO-8601-UTC> · …` from each collaborator’s `github.collaboration.yaml` (CLI stamps UTC; do not hand-forge timestamps). Local `history/continuity-index.md` rolls ≥3 days; board Notes keep full card lifetime.

## Project CLI subcommands (Pattern A)

All subcommands registered in `.ai_infra/install/cursor_workflow/project_parser.py`. Prefer recipes (`claim`, `handoff`, `guide`) over atomics.

| Subcommand | Purpose | Typical agent |
|------------|---------|---------------|
| `status` | Show `project_ssot` config from user_settings | Any (Entry) |
| `list` | List project items (optional `--status` filter) | Any (Entry) |
| `create` | Create Issue (or Draft if `item_kind_default: draft`) | project-board, implementer, integrator |
| `create-from-template` | Create Issue from slice/bug body template (default `item_kind_default: issue`) | project-board, implementer |
| `set-status` | Set item Status from YAML option ids; gates `in_review`\|`done` on body (exit 5) | Power use (prefer `handoff --to`) |
| `set-field` | Set Priority, Size, or Estimate | **Mandatory** on create/claim/own (`priority` + `size` + `estimate`); see skill § Tier-1 card fields contract |
| `set-section` | Replace ## Acceptance or ## Rollback (Notes stay append-only) | implementer, integrator (before handoff) |
| `get` | Get one project item by id | Any |
| `append-notes` | Append attributed line under ## Notes | Any (Exit atomic) |
| `claim` | Pattern A: In progress + Notes (+ Start date when configured) | implementer, integrator, researcher |
| `mention-pr` | Notes with PR URL; auto-promote Draft when configured | implementer |
| `promote-to-issue` | Convert DraftIssue → Issue (same `PVTI_`) | implementer (before shippable PR) |
| `handoff` | Pattern A: Notes `next=@user/agent` + optional set-status; gates `in_review`\|`done` | Any (Exit) |
| `validate-item` | Check body + Tier-1 fields + status-scoped Notes (exit 5 on fail) | verifier, project-board |
| `last` | Print last saved item_id (after create/claim) | Any (with `--last` recipes) |
| `guide` | Print safe recipes using `--last` (no placeholder ids) | Any (Entry) |
| `doctor` | Validate project_ssot config, templates, and gh project access | Maintainer / human |
| `board-bootstrap` | Schema-aware shell check (`--check`); opt-in `--ensure-fields` / `--apply-readme` | project-board first-run / human |
| `set-assignee` | Assign GitHub human user (Issue-backed items) | project-board, implementer |
| `find-by-pr` | Resolve project item id from PR number or URL | verifier, merge.py |
| `export` | Read-only board snapshot (never mutates Status) | workflow-drift-guard, ICC |
| `queue` | Enqueue a board op to local outbox (EXIT_QUEUED=6) | Any (rate-limit fallback) |
| `outbox status` | Outbox counts + GraphQL remaining | Any |
| `outbox flush` | Apply pending outbox ops when quota allows | implementer, project-board |

## workflow-drift-guard specifically

1. **Read board first** (`project status`, `list --status in_progress`) so dual-write checks compare board Status vs trackers.
2. Run `drift validate` (includes DRIFT-009 / DRIFT-010 when board_only; refresh `project export` for DRIFT-010).
3. Write `.local/workflow-artifacts/drift/*` (evidence stays local).
4. **Update board:** close the drift-pass card; if dual-write Confirmed, add Notes on the offending card or ask project-board to queue a Ready fix — do not write competing `in_progress` into `work-tracker.md`.

## Rate limits & outbox

GitHub GraphQL quota (~5000/hour) can block board writes. When `project_ssot.outbox.enabled`:

1. **Precheck (default):** before Pattern A writes, CLI reads cached REST `rate_limit` (TTL `quota_cache_ttl_seconds`, default 45s). If GraphQL `remaining < min_graphql_remaining`, enqueue + **EXIT_QUEUED (6)** without calling Projects GraphQL.
2. Live write fails with throttle (rate-limit / secondary / 429 / bare Forbidden) → CLI **enqueues** to `.local/generated-data/board-outbox.jsonl` and returns **EXIT_QUEUED (6)**. Permanent scope-miss errors are **not** queued.
3. **Dedupe:** identical pending `op`+`item_id`+payload fingerprint reuses one outbox row (`dedupe_pending`).
4. Agent continues local evidence (`change-index`, handoff line) — **do not** hammer `gh` / retry loops (CODE=6 = soft-success).
5. After quota recovers: `python3 -m cursor_workflow project outbox status` then `outbox flush` (capped by `max_flush_per_run`; refuses if `remaining < min_graphql_remaining`).
6. Explicit enqueue: `project queue --op append-notes|set-status|handoff|claim|set-assignee|set-field …`
7. Outbox is a **local buffer**, never a second Status SSOT. Prefer Pattern A CLI over raw `gh api graphql` (raw calls bypass the outbox).

Doctor and board-bootstrap already honor the quota cache and live-probe skips; do not wrap them in retry loops or repeated `project list` calls. For audits, prefer a single export / GraphQL dump, then flush outbox once with the configured `max_flush_per_run`.

Who flushes: any agent/human after reset; prefer implementer or project-board at slice close. Pending outbox is **not** a DRIFT failure.

### Assignee backfill (legacy cards)

New Issue creates assign `owner.github_user` automatically. For older cards missing Assignees (after throttle recovery):

```bash
python3 -m cursor_workflow project set-assignee --id PVTI_… --login <owner>
# or: gh issue edit N --add-assignee <owner> --repo <default_repo>
python3 -m cursor_workflow project outbox flush   # remaining queued ops — no retry-loop
```

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

## Live board smoke (maintainer)

Optional end-to-end check against the real Project (skipped in default CI).

**Last PASS:** 2026-07-19 — `make live-board-smoke` (evidence: `.local/workflow-artifacts/release/live-board-smoke-2026-07-19.md`).

1. Auth with Project scopes: `gh auth refresh -h github.com -s read:project,project` (plus existing `repo` scopes). If `xdg-open` fails, open **https://github.com/login/device**, paste the one-time code, and approve **Project** permissions — see [PLUGIN-USER-GUIDE § GitHub CLI auth](PLUGIN-USER-GUIDE.md#github-cli-auth-projects).
2. Confirm: `python3 -m cursor_workflow project doctor` and `project status`.
3. Clear any other card **In progress** for the same assignee (claim enforces `one_in_progress_per_assignee`).
4. Run: `make live-board-smoke`  
   (sets `PROJECT_SSOT_LIVE=1` and runs `tests/modules/install/test_project_cli_live.py`; claim retries briefly for GraphQL eventual consistency).
5. If EXIT_QUEUED / rate-limit: `project outbox status` then `outbox flush` when GraphQL remaining recovers.
6. Record PASS/FAIL under `.local/workflow-artifacts/release/` (local evidence only).

Do **not** add this to default PR gates — it mutates the live board.

## Human-only

Views, workflows, Insights, Project README, status updates, Ready prioritization / product roadmap. Paste README from `.ai_infra/templates/project-board/project-readme.md` in the GitHub UI only.
