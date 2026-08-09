---
name: board-ssot
description: Drive GitHub Project SSOT via project_ssot YAML and agent_colony project CLI.
---

<!--
File: SKILL.md
Path: .cursor/skills/board-ssot/SKILL.md
Role: Procedural skill for board-first backlog/status + multi-agent continuation on the Project.
Used By:
 - .cursor/agents/board.md
 - All kit agents when project_ssot.enabled
Depends On:
 - .local/user_settings/github.collaboration.yaml (project_ssot)
 - .ai_infra/install/agent_colony/project_cli.py
 - .ai_infra/install/agent_colony/project_atomics.py
 - .ai_infra/install/agent_colony/gh_project_adapter.py
 - .ai_infra/install/agent_colony/project_recipes.py
 - .ai_infra/install/agent_colony/project_outbox.py
 - .ai_infra/docs/operations/project-board-collaboration.md
 - ADR-008-project-board-ssot.md
Notes:
 - Pattern A: prefer recipes (claim/handoff/create-from-template); atomics for power use; no dual-write when board_only.
 - Continuation is board-anchored: every agent Entry reads the Project; Exit updates Status.
-->

# Board SSOT

## Goal

When `project_ssot.enabled` and `sync_policy: board_only`, use the GitHub Project as the **only writable SSOT** for backlog, Status, and multi-agent continuation. Prefer CLI over inventing `gh` flags. Local trackers are offline fallback only; read-only exports never compete with board Status.

**Agent:** `.cursor/agents/board.md`  
**Ops mirror:** `.ai_infra/docs/operations/project-board-collaboration.md`  
**ADR:** `.ai_infra/docs/decisions/ADR-008-project-board-ssot.md`

## Two-tier plans (ADR-010)

| Tier | Location | Role |
|------|----------|------|
| **Live** | Board card body (`board_only`) or `.local/index-and-planning/current/plan.md` (offline) | Acceptance, scope, rollback — only writable plan SSOT |
| **History** | `.local/plans/` (`plan snapshot`, `plan list`, `plan open` for human Build) | Dated snapshots + `index.md` — **never** competing Status or live plan under `board_only` (**DRIFT-012**) |

Agents: `plan list` → read snapshot → execute. Exit: `plan snapshot --slug … --board-item …`. See `.cursor/skills/canvas-artifacts/SKILL.md`.

## First-run (board shell) — before day-to-day cards

Day-0 requires the kit **default** shell: `.ai_infra/templates/project-board/board-shell.schema.yaml` (six Playground views; Priority/Size/Estimate/Start date on Status board + Prioritized backlog). Overlay: `.local/user_settings/board-shell.schema.yaml` when present.

0. **Wire YAML from URLs (if ids missing):** after `gh` auth, human pastes Project URL + repo URL → use `gh project view` / `field-list` → propose `project_ssot` + `default_repo` → human confirms before save. Discovery only — **no** `--ensure-fields` until CONSENT.
1. Load `.cursor/skills/board-shell/SKILL.md` (coach) and the schema above.
2. **CONSENT GATE (mandatory):** ask board description (or `use template default`) + `May I proceed to set up the kit default shell?` — only continue on `yes`.
3. Run `python3 -m agent_colony project doctor` → `project board-bootstrap --check`.
4. On **exit 5** (view FAIL or Tier-1 column FAIL): TURN PROTOCOL (agent coaches one view at a time; human uses `views-setup.md` as click reference). Optional `--ensure-fields` / `--apply-readme` only after consent. **No** `--apply-shell` CLI today.
5. Refuse “ready for agents” until `board-bootstrap --check` exits **0** (README non-empty, six views, Tier-1 columns on Status board / Prioritized backlog). Then resume day-to-day Pattern A below.

**Not first-run:** `/auditor` (architecture-impacting / pre-merge later).

## Continuation contract (all agents — non-negotiable when enabled)

Work is **indexed on the Project**, not in chat alone.

| Phase | Required |
|-------|----------|
| **Entry** | Prefer `python3 -m agent_colony project entry` (quota-aware: live \| conserve \| offline_artifacts). Then `get` / `claim` **one** card. Read Acceptance / Rollback / Notes on that card body. Avoid unfiltered `project list` / full `export` every turn — use `export --reuse-if-fresh` when a snapshot is enough. Parallel agents may each Entry, but **one export refresh per parent wave**. |
| **During** | Keep **one** In progress card for your assignee. Put progress notes on the card body when handing off mid-slice. |
| **Exit** | **Always** update Status for the card you worked: → `in_review` (PR/handoff) or → `done` (your part closed) or leave `in_progress` with **Notes** naming the next agent. Notes **must** use `append-notes --agent <this-agent>` → `@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · …` (CLI stamps UTC). Print handoff line. **If EXIT_QUEUED (6)** / rate-limit / Forbidden throttle / precheck low quota: do **not** retry in a loop — op is in `.local/generated-data/board-outbox.jsonl`; continue local evidence; later `project outbox flush`. |
| **Never** | Finish in chat only while leaving the card Stuck in Ready/Backlog. Never dual-write tracker `in_progress` under `board_only`. Never write bare `Agent: implementer` without `@user/` namespace. |

Handoff line (chat + card Notes):

```text
item_id=<from project last or create> · @User/implementer · Status=before→after · Priority=p1 · Size=s · Estimate=1 · next=@User/verifier
Tasks: [P1] …; [P2] …; [P3] …
```

Prefer `--last` after create so agents never invent ids.

Multi-collaborator: each human’s `owner.github_user` namespaces their agents (`@Alice/implementer` vs `@Bob/implementer`) on the same board.

## Tier-1 card fields contract (all agents — mandatory)

When you **create** or **own** a Project card, fill the Tier-1 fields below. Do **not** leave them empty and move on. Verifier spot-checks this on closure.

### Priority scale

| Chat / plan label | Board `set-field --field priority --to` | When |
|-------------------|----------------------------------------|------|
| **P0** | `p0` | Blocks merge / release / SSOT integrity |
| **P1** | `p1` | Must do next |
| **P2** | `p2` | Planned hygiene / polish |
| **P3** (deferred) | `p2` + Notes line `deferred` | Optional later — **no** `p3` option id in YAML |

Priority is **independent** of Size (a P0 can be XS).

### Size ↔ Estimate rubric (points, not hours)

**Estimate** is relative **points**. Do not invent hours unless the consumer’s Project README defines hours→points.

| Size | Typical slice | Estimate band | Default if unsure |
|------|---------------|---------------|-------------------|
| **xs** | Trivial (&lt; ~1h), one file / one paragraph | **1** | 1 |
| **s** | Small, clear boundary | **1–2** | **1** |
| **m** | Multi-file / multi-step, one PR | **3–5** | **3** |
| **l** | Large or high risk — prefer split | **5–8** | **5** |
| **xl** | Too big for one agent turn — **split** before coding | **8+** | refuse / split |

**Honesty rules**

1. Prefer smaller cards; if Size would be `l`/`xl`, create multiple Ready cards.
2. If Size and Estimate disagree with the table, explain in Notes.
3. Unknown → Size=`s`, Estimate=`1`, and Notes: `Size/Estimate guessed (default s/1)`.
4. Keep Size and Estimate aligned with this table (e.g. Size=`m` → Estimate in 3–5).

### Timing matrix

| Moment | Status | Priority | Size | Estimate | Start date | Assignee | Linked PR |
|--------|--------|----------|------|----------|------------|----------|-----------|
| Create (Ready/Backlog) | ✓ | ✓ required | ✓ | ✓ | — | ✓ Issue (owner; `--no-assignee` to skip) | — |
| First In progress | ✓ | confirm | confirm | confirm | **✓ required** | ✓ (Issue) | — |
| Open PR | — | — | — | — | — | — | ✓ `mention-pr` |
| Exit In review / Done | ✓ | Notes | Notes | Notes | already set | — | if PR |

**Start date** = UTC calendar day work began. Set when Status becomes `in_progress` if empty — via `claim`, `set-status --to in_progress`, or `handoff --to in_progress` (master switch: `conventions.set_start_date_on_claim`). Never set on create while Ready/Backlog. End date is human-only.

### Mandatory field checklist

| Field | When | CLI | Rules |
|-------|------|-----|-------|
| **Status** | Always | `claim` / `handoff` / `set-status` | Create → `ready` (or claim → `in_progress`); Exit → `in_review` / `done` |
| **Priority** | Create / claim / own | `create-from-template --priority p0\|p1\|p2` or `set-field` | Required on template create — no silent default |
| **Size** | Create / claim / own | `--size` / `set-field --field size --to xs\|s\|m\|l\|xl` | Per Size↔Estimate table; default `s` + Notes if guessed |
| **Estimate** | Create / claim / own | `--estimate` / `set-field --field estimate --to N` | Points per table; default `1` + Notes if guessed |
| **Start date** | First In progress | `claim` / `set-status --to in_progress` / `handoff --to in_progress` | Auto when `set_start_date_on_claim` + `fields.start_date.field_id`; if WARN, retry — do not ignore |
| **Assignee** | Create (Issue) / claim re-assert | `create-from-template` auto-assigns `owner.github_user`; `claim` / `set-assignee --login …` | **Create as Issue** (`item_kind_default: issue`). Draft is scratch-only; `--no-assignee` escape hatch |
| **Linked PR** | When a PR exists | `mention-pr --pr N --last --agent <agent>` | Auto-promotes Draft when `promote_to_issue_on_pr` |

```bash
# Pattern A — Tier-1 at create + Start date on claim
python3 -m agent_colony project create-from-template \
  --template slice --title "[P1] …" --status ready \
  --priority p1 --size s --estimate 1 --agent implementer
python3 -m agent_colony project claim --last --agent implementer
# When opening a shippable PR:
python3 -m agent_colony project mention-pr --pr N --last --agent implementer
```

Plain `project create` (non-template) still needs follow-up `set-field` for Priority/Size/Estimate.

Rules:

1. After create: **Priority + Size + Estimate** before coding; on first In progress confirm **Start date** from CLI output.
2. Exit Notes and chat: `[P0]…; [P1]…; [P2]…; [P3]…` and `Priority=p? · Size=? · Estimate=?`.
3. `auditor` / `drift-guard`: recommend Priority/Size/Estimate (per table) when seeding Ready cards.
4. `verifier`: spot-check Status, Priority, Size, Estimate, **Start date on In progress / In review / Done**; Assignee when Issue-backed; Linked PR when a PR opened. Missing Start date on those statuses = **incomplete Exit**.
5. Missing Tier-1 fields = incomplete Exit — fill or document blocker in Notes before handoff.

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
| **Start date** | First In progress | `claim` / `set-status --to in_progress` / `handoff --to in_progress` | **Mandatory** when empty — UTC today if `conventions.set_start_date_on_claim: true`; see § Tier-1 card fields contract |
| **Estimate** | Create / claim / own | `project set-field --field estimate --to N` | **Mandatory** — default `1` if unknown |
| **Size** | Create / claim / own | `project set-field --field size --to xs\|s\|m\|l\|xl` | **Mandatory** — default `s` if unknown |
| **Priority** | Create / claim / own | `project set-field --field priority --to p0\|p1\|p2` | **Mandatory** — chat P3 → `p2` + Notes `deferred` |
| **Assignee** | Create Issue (owner) | `create-from-template` (default) / `claim` / `set-assignee` | **Mandatory on Issue create** — `owner.github_user`; Draft cannot hold Assignees |
| **Linked PR** | PR open | `project mention-pr --pr N --last` | **Mandatory when a PR exists** for the card |
| **Promote Draft→Issue** | Only if card is still Draft | `project promote-to-issue --last --agent <name>` | Prefer never needing this — create as Issue |
| **Out of scope (agents default)** | — | — | Iteration, Labels, Reviewers, End date — human / UI only |

### Issue lifecycle (Draft vs Issue)

| Path | CLI / config | Notes |
|------|--------------|-------|
| Default create | `create-from-template` + `item_kind_default: issue` | **Issue** on the Project + linked repo (`default_repo`) — Assignees + Linked PRs work from claim |
| Scratch only | `item_kind_default: draft` (override) | DraftIssue — no Assignees until `promote-to-issue`; do **not** use for shippable work |
| Explicit promote | `promote-to-issue --last --agent <name>` | Same `PVTI_`; needed only if card was created as Draft |
| Auto on PR | `mention-pr` | When `promote_to_issue_on_pr: true` (still useful if a Draft slipped through) |

### Issue state vs board Status (they're independent by default)

Board `Status=Done` and the linked GitHub Issue's own `open`/`closed` state are **separate signals** — Status is the continuation SSOT; Issue state is GitHub-native (Issues list, notifications). A card can be `Done` while its Issue stays `open` — this is expected, not a bug, unless you opt in below.

- **Opt-in bridge:** `conventions.close_linked_issue_on_cleanup` (default `false`). When `true`, `full-pr-workflow`'s `finalize.py` best-effort closes the Issue linked to the merged PR's board item, **after** branch cleanup succeeds — never on `set-status`/`claim`/`handoff`, so it can't race ahead of merge/cleanup evidence.
- **CLI:** `project close-linked-issue --pr N [--dry-run]` — resolves the item via `find-by-pr`, skips silently (no error) when there's no linked Issue, the flag is off, or the Issue is already closed; a `gh` error is `DEFERRED` (non-blocking, printed but never fails cleanup).
- **Evidence:** outcome recorded in `finalize.md § Linked Issue Closure` (`PASS` / `SKIPPED` / `DEFERRED` / `DRY-RUN` when `finalize.py --dry-run` is used).

### Rules

1. One primary **In progress** per **human assignee** — do not steal others'.
2. Pull from **Ready** or continue your In progress.
3. Acceptance / Rollback / Notes on **card body** = continuation index. Attribution = `@owner.github_user/<agent> · <ISO-8601-UTC> · …` via `append-notes --agent` (or `claim`/`handoff` recipes).
4. Under `board_only`: no competing tracker `in_progress` (DRIFT-009); no dual-mirror “for safety.”
5. Humans own views, workflows, README, Insights, status updates by default (no view API). If the human **asks** for browser help on views/columns, `/board` may use browser MCP for that turn (see `board-shell`).
6. Read-only `project export` (if used) never writes Status.
7. Post-merge Done is Pattern A (`merge.py`), Notes prefixed `@user/merge.py`.

### Per-agent rights (what / when / where)

| Agent | Entry (read board) | Exit (must update board) | Local writes |
|-------|--------------------|--------------------------|--------------|
| **board** | status + list | create/move any Status; Priority/Size; hand off to implementer | change-index, updates-log |
| **implementer** | status + Ready/claim | In progress → In review (PR) → Done; fields on own card; may create slice cards | code; change-index; PR |
| **test-runner** | status + slice card | Stay on card; → In review when tests gate PR; Done when test-only slice closes | test-index / test-plan |
| **verifier** | status + related card | Confirm → Done or leave In review with Notes (failures) | evidence / PR artifacts |
| **integrator** | status + Ready/claim | claim → Done on integration card; may create cards | integrate / payload |
| **auditor** | status + audit card | Audit card → In review/Done; Notes point to artifact paths | `.local/workflow-artifacts/…` |
| **drift-guard** | **Must** status + list In progress (dual-write check) | Drift-pass card → Done (or In review if P0/P1 need human); cite board Status in drift-audit; hand remediation to board/implementer via Ready card or Notes — **do not** silent-edit trackers | drift-audit / drift-todos |
| **researcher** | status + research card if any | If a research card exists → Done + Notes with corpus paths; else read-only | `_research_results/` |

### Status path

```text
Ready → In progress → In review → Done
```

| Moment | Actor | CLI |
|--------|-------|-----|
| Start work | implementer / integrator / test-runner / board | `set-status --to in_progress` |
| PR open / peer handoff | implementer | `set-status --to in_review` |
| Part verified closed | implementer / verifier / test-runner | `set-status --to done` |
| Drift / audit pass closed | drift-guard / auditor | `set-status --to done` (their card) |
| Queue triage | board or human | create / set-status / set-field |

## Procedure (CLI) — prefer Pattern A recipes

**Never paste docs placeholders as `--id`.** After create, use `--last`. Print recipes: `project guide`.

Human Project README: paste `.ai_infra/templates/project-board/project-readme.md` in the Project settings UI (board brief only — not into a shell). CLI recipes stay in `project guide` and `project-board-collaboration.md`.

### Template routing

| Need | Who | Template / action |
|------|-----|-------------------|
| slice / feature / `chore/` | implementer, board, integrator | `create-from-template --template slice` |
| bug / defect / `fix/` | implementer, board | `create-from-template --template bug` |
| external / corpus research | researcher, board | `create-from-template --template research` |
| audit pass | auditor | `--template slice` + title `[AUDIT] …` then `claim --last` |
| consume existing card | test-runner, verifier | **No** `create-from-template` — claim/continue only |
| Project README | **Humans only** | paste `project-readme.md` (board brief) in Project settings UI — or `--apply-readme` |

Index: `.ai_infra/templates/project-board/README.md`. After create, always `claim --last` / `handoff --last` (never invent ids).

**Notes format:** `@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · text` — auto-stamped by CLI on `claim`, `handoff`, and `append-notes --agent`. Idempotent when timestamp already present. Do not hand-forge times.

**Local continuity:** append UTC-prefixed lines to `history/updates-log.md`; optional row in `history/continuity-index.md` (rolling ≥3 days). Board Notes retain full card lifetime.

1. **Doctor / guide:** `project doctor` · `project guide --agent implementer`
2. **Status / list:** `project status` · `project list [--status ready|in_progress|in_review]`
3. **Create:** `project create-from-template --title "[SLICE] short-name" --template slice --status ready --priority p1 --size s --estimate 1 --agent <agent>` (prefer `--acceptance` / `--rollback` at create)
4. **Claim:** `project claim --last --agent <this-agent>`
5. **Fill body (if still TBD):** `project set-section --section acceptance|rollback --text '…' --last --agent <this-agent>` — Notes stay append-only
6. **Handoff:** `project handoff --last --agent <this-agent> --next <agent> [--to in_review|done]` — **EXIT_VALIDATION (5)** when Acceptance/Rollback are still placeholders (also enforced on `set-status --to in_review|done`)
7. **Validate:** `project validate-item --last` (same checks; handoff/`set-status` already gate closes)
8. **Atomics (power use):** `set-status` · `set-field` (priority · size · estimate) · `set-section` · `promote-to-issue` · `mention-pr` · `append-notes --agent` · `get --last` · `export`
9. **Verify:** `project list` + handoff line; `project last` prints saved id

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
- [ ] No dual-write; no unprompted edits to Project views/workflows/Insights (browser assist only if human asked)

## Anti-patterns

- Chat-only completion with stale board Status
- Hardcoding field/option ids
- Reshuffling Ready/P0 without human or board ask
- Editing Project views/workflows/Insights unprompted (browser assist only when human asks)
- Pasting Project settings UI text into a terminal
- Dual-write board + tracker under `board_only`
- Multi-step claim without `project claim` / bare Notes without `--agent`
- Do not push to unrelated repositories
