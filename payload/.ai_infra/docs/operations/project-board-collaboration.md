<!--
File: project-board-collaboration.md
Path: .ai_infra/docs/operations/project-board-collaboration.md
Role: Ops mirror — Project surfaces + per-agent Entry/Exit continuation on the board.
Used By:
 - .cursor/skills/board-ssot/SKILL.md
 - .cursor/agents/*.md
 - AGENTS.md
Depends On:
 - github.collaboration.yaml project_ssot
 - ADR-008
Notes:
 - When enabled, every agent reads the Project on Entry and updates Status on Exit.
-->

# Project board collaboration (agents + humans)

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)


When `project_ssot.enabled` and `sync_policy: board_only`, the **GitHub Project is the only writable SSOT** for backlog, Status, and continuation. Local trackers are offline fallback only; read-only exports never compete with Status. Canonical skill: `.cursor/skills/board-ssot/SKILL.md`.

**First-time consumer setup:** step-by-step checklist in [PLUGIN-USER-GUIDE.md § Consumer project_ssot onboarding](PLUGIN-USER-GUIDE.md#consumer-project_ssot-onboarding-checklist) (install → identity → `gh auth status` → **`/board`** wire → optional minimal 2-view overlay → CONSENT + TURN → `board-bootstrap --check` exit **0** → `project status` → first card → outbox flush).

## Continuation (why agents update the board)

| Without board Exit | With board Exit |
|--------------------|-----------------|
| Next agent guesses from chat | Next agent lists Ready / In progress / In review |
| Status drifts from reality | Status column = truth (DRIFT-009 watches dual-write) |
| Humans cannot see progress | Project UI is the shared dashboard |

**Rule:** Entry = read board. Exit = update Status and **attributed Notes** for the card you touched. `validate-item` checks the card body, Tier-1 fields (including Assignee when present on the snapshot), and status-scoped Notes; it is not just a section-presence check. **Enforcement:** `handoff` and `set-status` to `in_review`|`done` call the same checks and return EXIT_VALIDATION (5) while Acceptance/Rollback are empty or `(TBD)` (including `- (TBD)` list form). Fill via `create-from-template --acceptance/--rollback` or `project set-section --section acceptance|rollback --text '…' --last`. Prefer Pattern A recipes: `project claim` / `project handoff` (one command each). Atomics (`append-notes --agent`, `set-section`) remain for power use. **Never** paste Project settings UI text into a shell — humans **follow** `.ai_infra/templates/project-board/views-setup.md` and paste **contents of** `project-readme.md` (board brief — not a CLI dump) into Project README settings (or opt-in `board-bootstrap --check --apply-readme`). Day-to-day CLI: `project guide`.

### Board shell starter (first-run)

- **Desired state:** `.ai_infra/templates/project-board/board-shell.schema.yaml` — **full Playground default** (six views + Tier-1 columns). **Or** copy `board-shell.schema.minimal.yaml` for **two views** ([Playground #3](https://github.com/users/SavinRazvan/projects/3)).
- **Customize:** copy/edit `.local/user_settings/board-shell.schema.yaml` — `board-bootstrap --check` prefers the overlay when present. Do **not** remove Status / Priority / Size / Estimate / Start date / End date, or hide **Priority** on Prioritized backlog.
- **Coach:** `/board` + `.cursor/skills/board-shell/SKILL.md`.
- **Verify:** `python3 -m agent_colony project board-bootstrap --check` (FAIL if a default Playground view is missing; **FAIL (exit 5)** on missing Tier-1 columns; WARN on leftover `View N` / layout mismatch).
- **Optional API:** `--ensure-fields` (create missing field definitions + print suggested YAML ids); `--apply-readme` (push README). Views stay human UI (ADR-008).

## Day-0 / Day-N playbook (no confusion)

| Who | Day-0 | Day-N |
|-----|-------|-------|
| **Human** | `/board` wire YAML → CONSENT → TURN → `board-bootstrap --check` exit **0** | Ready order, views, Insights, README |
| **Agent** | Refuse day-to-day claim until bootstrap exit 0 | `project entry` → one card → Exit Status + Notes |
| **Both** | Fill Acceptance/Rollback before In review / Done | `heal-cards --check` = inventory WARN only |

**Incomplete cards WARN:** `doctor` / `heal-cards --check` often flag **Done** cards missing **End date** (historical hygiene). That is **not** blocked Ready work. Repair with human consent: `heal-cards --apply` (sets End date on Done). Use `--fill-tier1` only when you want Priority→p2 / Size defaults on gaps. Do **not** invent Acceptance/Rollback on old Done cards. Empty Ready → `create-from-template` + `claim`. During `heal-cards --apply [--fill-tier1]`, each live write goes through `guard_write_or_queue` — individual field ops may return **EXIT_QUEUED (6)** mid-sweep; continue local work, then `project api-ready` && re-run apply / `outbox flush` (do not retry-loop).

**Owner hygiene:** `project_ssot.owner` must be a **bare login** for `gh --owner` (e.g. `SavinRazvan`). `load_project_ssot` runs `normalize_project_owner`, which strips `@` and `users/`|`user/`|`orgs/`|`org/` prefixes. Paths like `users/a/b` fail load. Prefer bare login in YAML; `project doctor` WARNs when the raw YAML value still looks URL-shaped after normalize (prefix was stripped for runtime). Wrong prefix historically produced `unknown owner type` on `gh project` calls and failed outbox rows — fix YAML, then triage with `outbox drop --force` for stale failed rows (do not blind-flush).

**Entry modes:** Prefer `project api-ready` then `project entry` (or `--digest`). `live` / `conserve` when GraphQL works; `offline_artifacts` only when remaining is known-low or no usable snapshot. On EXIT_QUEUED (6): `project api-ready` then `outbox flush` after quota recovers — do not retry-loop.

**`--last`:** Use after create/claim. If guide prints `(invalid …)`, clear `.local/generated-data/project-last-item.json` and recreate — never paste docs placeholders as `--id`.

## Surfaces — who may write

| Surface | Human | Agents | GitHub |
|---------|-------|--------|--------|
| Card Status | Yes | Yes — every agent Exit | — |
| Priority / Size | Yes | Triage + own card | — |
| Start date | Yes (UI) | Set UTC today when Status → `in_progress` if empty (`claim`, `set-status`, `handoff --to in_progress`) when `set_start_date_on_claim` + `fields.start_date.field_id` | — |
| End date | Yes (UI) | Set UTC today when Status → `done` if empty (`set-status`, `handoff`, merge sync, `heal-cards`) when `set_end_date_on_done` + `fields.end_date.field_id` | — |
| Estimate | Yes (UI) | Triage + own card — `set-field --field estimate --to N` (points; Size↔Estimate table in skill) | — |
| Promote Draft→Issue | Yes (UI) | `promote-to-issue --last --agent <name> [--repo owner/repo]` | GraphQL `convertProjectV2DraftIssueItemToIssue`; same `PVTI_`; Assignees + Linked PRs after promote; Notes `promoted to Issue #N`; fine-grained PAT caveat (`doctor` / `guide`); claim does **not** auto-promote |
| Linked PRs | Yes (UI link) | `mention-pr --pr N` → Notes with PR URL; auto-promotes Draft when `promote_to_issue_on_pr` (default true) — FAIL if promote fails; WARN-only if false | GitHub **Linked pull requests** column derived from Issue↔PR (works after Issue) |
| Create cards | Yes | board, implementer, integrator | — |
| Ready prioritization | **Owner** | Consume; create agreed work | — |
| Views / workflows / Insights / status updates | **Owner only** | Never mutate views | Insights auto |
| Project README | **Owner** (paste) | Opt-in `board-bootstrap --apply-readme` only | — |
| Assignee / My items | Yes (`set-assignee` / UI) | `create-from-template` assigns `owner.github_user` on Issues (default); claim re-asserts if empty; assignee = **human** only | My items view |
| Card Notes (`append-notes --agent`) | Yes | Yes — `@user/agent · YYYY-MM-DDTHH:MM:SSZ · …`; `next=@user/agent` | — |
| PR / audits / secrets | Local | Local | — |
| Post-merge Status → Done | — | Via `merge.py` (Pattern A); Notes `@user/merge.py` | — |
| Linked Issue close (opt-in) | — | `full-pr-workflow` finalize.py → `close-linked-issue --pr N`, after branch cleanup; gated by `conventions.close_linked_issue_on_cleanup` (default false); **requires board Status=Done** | Board `Status=Done` and Issue `open`/`closed` are independent by default — this is the opt-in bridge, not a second Status writer (ADR-008 §10) |
| Read-only board export | Consume | `project export` (never writes Status) | — |

## Per-agent Entry / Exit

| Agent | Entry | Exit (board) |
|-------|-------|--------------|
| **board** | status + list | Full triage; handoff to implementer |
| **implementer** | status + `claim --agent implementer` | `handoff --agent implementer --next … --to in_review` or →Done |
| **test-runner** | status + slice card | →In review or →Done; `--agent test-runner` |
| **verifier** | status + related card | →Done or leave In review; `--agent verifier` |
| **integrator** | status + claim | →Done; `--agent integrator` |
| **auditor** | status + audit card | →In review/Done; `--agent auditor` + artifact paths |
| **drift-guard** | **Must** status + list In progress | Drift card →Done; `--agent drift-guard`; remediation via Notes/Ready — no silent tracker edits |
| **researcher** | status (+ research card) | Research card →Done; `--agent researcher` + `AGENT_BRIEF` / pack paths (adaptive intake from chat/Notes) |

## Status path

```text
Ready → In progress → In review → Done
```

Handoff: `item_id=<from create or --last> · @User/implementer · Status=a→b · next=@User/verifier`

**Safe flow:** `project guide` then `create-from-template` → `claim --last` → `handoff --last`. Never paste docs placeholder ids as `--id`.

**Attribution:** Notes use `@owner.github_user/<agent> · <ISO-8601-UTC> · …` from each collaborator’s `github.collaboration.yaml` (CLI stamps UTC; do not hand-forge timestamps). Local `history/continuity-index.md` rolls ≥3 days; board Notes keep full card lifetime.

## Project CLI subcommands (Pattern A)

All subcommands registered in `.ai_infra/install/agent_colony/project_parser.py`. Prefer recipes (`entry`, `claim`, `handoff`, `guide`) over atomics.

| Subcommand | Purpose | Typical agent |
|------------|---------|---------------|
| `status` | Show `project_ssot` config from user_settings | Any |
| `entry` | Quota-aware Continuation Entry (live \| conserve \| offline_artifacts) | **Any (preferred Entry)** |
| `list` | List project items (optional `--status` filter); WARN if unfiltered high `--limit` | Any (prefer `entry`) |
| `create` | Create Issue (or Draft if `item_kind_default: draft`) | board, implementer, integrator |
| `create-from-template` | Create Issue from slice/bug body template (default `item_kind_default: issue`) | board, implementer |
| `set-status` | Set item Status from YAML option ids; gates `in_review`\|`done` on body (exit 5) | Power use (prefer `handoff --to`) |
| `set-field` | Set Priority, Size, or Estimate | **Mandatory** on create/claim/own (`priority` + `size` + `estimate`); see skill § Tier-1 card fields contract |
| `set-section` | Replace ## Acceptance or ## Rollback (Notes stay append-only) | implementer, integrator (before handoff) |
| `get` | Get one project item by id | Any |
| `append-notes` | Append attributed line under ## Notes | Any (Exit atomic) |
| `claim` | Pattern A: In progress + Notes (+ Start date when configured) | implementer, integrator, researcher |
| `mention-pr` | Notes with PR URL; auto-promote Draft when configured | implementer |
| `promote-to-issue` | Convert DraftIssue → Issue (same `PVTI_`) | implementer (before shippable PR) |
| `handoff` | Pattern A: Notes `next=@user/agent` + optional set-status; gates `in_review`\|`done` | Any (Exit) |
| `validate-item` | Check body + Tier-1 + Status + Notes; **audit cards:** WARN if Notes lack `.local/workflow-artifacts/` path; **exit 5** if cited path fails Schema-1 | verifier, board |
| `heal-cards` | Inventory incomplete Status/Tier-1; `--apply` sets Done when Issue CLOSED + Status empty/non-done; per-op queue on throttle | board, maintainer |
| `last` | Print last saved item_id (after create/claim) | Any (with `--last` recipes) |
| `guide` | Print safe recipes using `--last` (no placeholder ids) | Any (Entry) |
| `doctor` | Validate project_ssot config, templates, gh access; WARN incomplete cards + URL-shaped owner YAML | Maintainer / human |
| `board-bootstrap` | Schema-aware shell check (`--check`); opt-in `--ensure-fields` / `--apply-readme` | board first-run / human |
| `set-assignee` | Assign GitHub human user (Issue-backed items) | board, implementer |
| `find-by-pr` | Resolve project item id from PR number or URL | verifier, merge.py |
| `export` | Read-only board snapshot (`--reuse-if-fresh` / `--force`); never mutates Status | drift-guard |
| `api-ready` | Exit 0 if board API may proceed; EXIT_QUEUED(6) if cooldown / low GraphQL remaining | **Any (gate before writes)** |
| `cooldown status` | Inspect `board-api-cooldown.json` circuit-breaker | Any |
| `cooldown clear` | Clear cooldown (`--force`; maintainer escape only) | Maintainer |
| `queue` | Enqueue a board op to local outbox (EXIT_QUEUED=6) | Any (rate-limit fallback) |
| `outbox status` | Outbox counts + GraphQL remaining | Any |
| `outbox list` | List outbox rows (`--status pending\|failed\|done`) for triage | board, maintainer |
| `outbox drop` | Mark a row failed/triaged (`--id` + `--force`; smoke/stale only) | board, maintainer |
| `outbox flush` | Apply pending outbox ops when quota allows | implementer, board |

## Three coordination layers (do not conflate)

| Layer | When | Writable Status? |
|-------|------|------------------|
| **Live board** | GraphQL healthy (`project entry` → `live`) | Yes — only writable SSOT under `board_only` |
| **Outbox JSONL** | Writes throttled / precheck low / EXIT_QUEUED | Buffer only — `outbox flush` restores board; never SSOT |
| **Offline artifacts / local_trackers** | `entry` → `offline_artifacts`, board unreachable, or `fallback: local_trackers` | Fallback only — resume board when up; do not dual-write Status |

## Quota bands (`project_ssot.efficiency`)

| Remaining (approx) | `project entry` mode | Reads | Writes |
|--------------------|----------------------|-------|--------|
| ≥ `conserve_below_remaining` (default 1500) | `live` | Scoped `item-list` (`entry_list_limit`) | Live Pattern A |
| Below conserve, ≥ `offline_artifacts_below_remaining` (200) | `conserve` | Reuse snapshot if fresh TTL | Live or queue |
| Below offline threshold / Forbidden | `offline_artifacts` | Snapshot + tracker paths | `project queue` only |

## drift-guard specifically

1. **Read board first** via `project entry` (or `list --status in_progress` if already in live mode) so dual-write checks compare board Status vs trackers.
2. Run `drift validate` (includes DRIFT-009 / DRIFT-010 when board_only; prefer `project export --reuse-if-fresh` before validate so one snapshot serves the wave).
3. Write `.local/workflow-artifacts/drift/*` (evidence stays local).
4. **Update board:** close the drift-pass card; if dual-write Confirmed, add Notes on the offending card or ask board to queue a Ready fix — do not write competing `in_progress` into `work-tracker.md`.

## Rate limits & outbox

GitHub GraphQL quota (~5000/hour) can block board writes. When `project_ssot.outbox.enabled`:

1. **Gate:** `python3 -m agent_colony project api-ready` (EXIT_OK = may write; EXIT_QUEUED(6) = skip). MCP: `workflow_project_api_ready`.
2. **Circuit-breaker:** throttle / low remaining opens `.local/generated-data/board-api-cooldown.json` (`limited_until`). While open, Pattern A writes hard-skip live REST/GraphQL and enqueue with EXIT_QUEUED. `project cooldown status` / `project cooldown clear --force` (maintainer escape only).
3. **Precheck (default):** before Pattern A writes, CLI reads cached REST `rate_limit` (TTL `quota_cache_ttl_seconds`, default 45s). If GraphQL `remaining < min_graphql_remaining`, enqueue + **EXIT_QUEUED (6)** without calling Projects GraphQL.
4. Live write fails with throttle (rate-limit / secondary / 429 / bare Forbidden without permanent-permission text) → CLI **enqueues** to `.local/generated-data/board-outbox.jsonl` and returns **EXIT_QUEUED (6)**. Permanent scope-miss / permission Forbidden are **not** queued.
5. **Dedupe / Notes coalesce:** identical pending `op`+`item_id`+payload reuses one row; pending `append-notes` for the same item are capped (`max_pending_notes_per_item`, default 3).
6. Agent continues local evidence (`change-index`, handoff line) — **do not** hammer `gh` / retry loops (CODE=6 = soft-success).
7. After quota recovers: `project api-ready` then `outbox status` then `outbox flush` (capped by `max_flush_per_run`; refuses if cooldown open or `remaining < min`).
8. Explicit enqueue: `project queue --op append-notes|set-status|set-section|handoff|claim|set-assignee|set-field|promote-to-issue …`
9. Outbox is a **local buffer**, never a second Status SSOT. Prefer Pattern A CLI over raw `gh api graphql` (raw calls bypass the outbox).
10. **Card-touch budget:** one claimed/`--last` card per wave; `heal-cards --apply --fill-tier1` requires `--id`/`--last`. Each heal write uses `guard_write_or_queue` — mid-sweep EXIT_QUEUED is expected under throttle; flush / re-apply after `api-ready`.

Doctor and board-bootstrap already honor the quota cache and live-probe skips; do not wrap them in retry loops or repeated `project list` calls. For audits, prefer a single export / GraphQL dump, then flush outbox once with the configured `max_flush_per_run`.

Who flushes: any agent/human after `api-ready` recovers; prefer implementer or board at slice close. Pending outbox is **not** a DRIFT failure.

### Outbox triage

1. `project api-ready` must exit 0.
2. `project outbox list --status pending` — drop fake/smoke with `project outbox drop --id <uuid> --force`.
3. Do not blind-flush claims that would wrong-transition Status.
4. Then `project outbox flush` once (capped).


### Assignee backfill (legacy cards)

New Issue creates assign `owner.github_user` automatically. For older cards missing Assignees (after throttle recovery):

```bash
python3 -m agent_colony project set-assignee --id PVTI_… --login <owner>
# or: gh issue edit N --add-assignee <owner> --repo <default_repo>
python3 -m agent_colony project outbox flush   # remaining queued ops — no retry-loop
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

1. Auth with Project scopes: `gh auth refresh -h github.com -s read:project,project` (plus existing `repo` scopes). If `xdg-open` fails, open **https://github.com/login/device**, paste the one-time code, and approve **Project** permissions — see [permissions-and-prerequisites.md § GitHub CLI](permissions-and-prerequisites.md#2-github-cli-gh--main-github-authorization).
2. Confirm: `python3 -m agent_colony project doctor` and `project status`.
3. Clear any other card **In progress** for the same assignee (claim enforces `one_in_progress_per_assignee`).
4. Run: `make live-board-smoke`  
   (sets `PROJECT_SSOT_LIVE=1` and runs `tests/modules/install/test_project_cli_live.py`; claim retries briefly for GraphQL eventual consistency).
5. If EXIT_QUEUED / rate-limit: `project api-ready` then `outbox status` / `cooldown status`, triage with `outbox list`/`drop` if needed, then `outbox flush` when GraphQL remaining recovers.
6. Record PASS/FAIL under `.local/workflow-artifacts/release/` (local evidence only).

Do **not** add this to default PR gates — it mutates the live board.

## Human-only

Views, workflows, Insights, Project README, status updates, Ready prioritization / product roadmap. Paste the board brief from `.ai_infra/templates/project-board/project-readme.md` in the GitHub UI only (or `--apply-readme`). CLI recipes: `project guide` — not the Project README.
