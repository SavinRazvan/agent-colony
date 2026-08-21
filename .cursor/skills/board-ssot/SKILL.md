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
 - .ai_infra/docs/operations/project-board-collaboration.md
 - ADR-008-project-board-ssot.md
Notes:
 - Pattern A: prefer recipes (claim/handoff/create-from-template); no dual-write when board_only.
-->

# Board SSOT

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

When `project_ssot.enabled` and `sync_policy: board_only`, the GitHub Project is the **only writable SSOT** for backlog, Status, and continuation. Prefer CLI over inventing `gh` flags. Local trackers = offline fallback only; read-only exports never compete with board Status.

**Agent:** `.cursor/agents/board.md` · **Ops:** `.ai_infra/docs/operations/project-board-collaboration.md` · **ADR:** `.ai_infra/docs/decisions/ADR-008-project-board-ssot.md`

## Two-tier plans (ADR-010)

| Tier | Location | Role |
|------|----------|------|
| **Live** | Board card body (`board_only`) or `plan.md` (offline) | Acceptance, scope, rollback — only writable plan SSOT |
| **History** | `.local/plans/` (`plan snapshot\|list\|open`) | Snapshots only — **never** competing Status under `board_only` (**DRIFT-012**) |

Agents: `plan list` → read snapshot → execute. Exit: `plan snapshot --slug … --board-item …`. See `.cursor/skills/canvas-artifacts/SKILL.md`.

## First-run (board shell)

Kit default shell: `.ai_infra/templates/project-board/board-shell.schema.yaml` (six Playground views; Tier-1 columns on Status board + Prioritized backlog). Overlay: `.local/user_settings/board-shell.schema.yaml` when present.

1. Wire YAML from Project + repo URLs (human confirms before save). Discovery only — **no** `--ensure-fields` until CONSENT.
2. Load `.cursor/skills/board-shell/SKILL.md`. **CONSENT GATE:** ask description + `May I proceed to set up the kit default shell?` — continue only on `yes`.
3. `python3 -m agent_colony project doctor` → `project board-bootstrap --check`.
4. **Exit 5:** TURN PROTOCOL (human UI via `views-setup.md`). Optional `--ensure-fields` / `--apply-readme` only after consent. **No** `--apply-shell` CLI.
5. Refuse “ready for agents” until `board-bootstrap --check` exits **0**. Then Pattern A below. **`/auditor`** is not day-0.

## Continuation contract

Work is **indexed on the Project**, not chat alone.

| Phase | Required |
|-------|----------|
| **Entry** | Prefer `python3 -m agent_colony project entry` (live \| conserve \| offline_artifacts). Then `get` / `claim` **one** card. Read Acceptance / Rollback / Notes. Avoid unfiltered `list` / full `export` every turn — use `export --reuse-if-fresh`. One export refresh per parent wave. |
| **During** | **One** In progress card for your assignee. Mid-slice progress → card Notes. |
| **Exit** | Update Status → `in_review` / `done`, or stay `in_progress` with **Notes** naming next agent. Notes via `append-notes --agent <this-agent>` → `@owner.github_user/<agent> · YYYY-MM-DDTHH:MM:SSZ · …` (CLI stamps UTC). Print handoff line. **EXIT_QUEUED (6)** / rate-limit / Forbidden / precheck low quota: **do not** retry-loop — op in `.local/generated-data/board-outbox.jsonl`; later `project outbox flush`. |
| **Never** | Chat-only completion with stale Status. No dual-write tracker `in_progress` under `board_only`. No bare `Agent: implementer` without `@user/` namespace. |

Handoff line (chat + Notes):

```text
item_id=<from project last or create> · @User/implementer · Status=before→after · Priority=p1 · Size=s · Estimate=1 · next=@User/verifier
Tasks: [P1] …; [P2] …; [P3] …
```

Prefer `--last` after create. Multi-collaborator: each `owner.github_user` namespaces agents (`@Alice/implementer` vs `@Bob/implementer`).

## Tier-1 card fields contract

When you **create** or **own** a card, fill Tier-1 fields. Verifier spot-checks on closure.

### Priority

| Label | `set-field --field priority --to` | When |
|-------|-----------------------------------|------|
| P0 | `p0` | Blocks merge / release / SSOT |
| P1 | `p1` | Must do next |
| P2 | `p2` | Hygiene / polish |
| P3 (deferred) | `p2` + Notes `deferred` | No `p3` option id in YAML |

Priority is independent of Size (P0 can be XS).

### Size ↔ Estimate (points, not hours)

| Size | Typical slice | Estimate band | Default if unsure |
|------|---------------|---------------|-------------------|
| **xs** | Trivial, one file | **1** | 1 |
| **s** | Small, clear boundary | **1–2** | **1** |
| **m** | Multi-file, one PR | **3–5** | **3** |
| **l** | Large / high risk — split | **5–8** | **5** |
| **xl** | Too big — **split** before coding | **8+** | refuse / split |

Honesty: prefer smaller cards; if Size=`l`/`xl`, split. If table mismatch, explain in Notes. Unknown → Size=`s`, Estimate=`1`, Notes: `Size/Estimate guessed (default s/1)`.

### Timing matrix

| Moment | Status | Priority | Size | Estimate | Start | End | Assignee | Linked PR |
|--------|--------|----------|------|----------|-------|-----|----------|-----------|
| Create (Ready/Backlog) | ✓ | ✓ | ✓ | ✓ | — | — | ✓ Issue | — |
| First In progress | ✓ | confirm | confirm | confirm | **✓** | — | ✓ | — |
| Open PR | — | — | — | — | — | — | — | ✓ `mention-pr` |
| Exit In review | ✓ | Notes | Notes | Notes | set | — | — | if PR |
| Exit Done | ✓ | Notes | Notes | Notes | set | **✓** | — | if PR |

**Start date:** UTC day work began. Set on first `in_progress` if empty — `claim`, `set-status --to in_progress`, or `handoff --to in_progress` (`conventions.set_start_date_on_claim`). Never on Ready/Backlog create.

**End date:** UTC day finished. Set on `done` if empty — `set-status --to done`, `handoff --to done`, merge sync, or `heal-cards --apply` (`conventions.set_end_date_on_done`). Never on create or In progress / In review.

### Field checklist

| Field | When | CLI |
|-------|------|-----|
| **Status** | Always | `claim` / `handoff` / `set-status` |
| **Priority** | Create / own | `create-from-template --priority p0\|p1\|p2` or `set-field` |
| **Size** | Create / own | `--size` / `set-field --field size --to xs\|s\|m\|l\|xl` |
| **Estimate** | Create / own | `--estimate` / `set-field --field estimate --to N` |
| **Start date** | First In progress | `claim` / `set-status` / `handoff` → `in_progress` |
| **End date** | Done | `set-status` / `handoff` / merge / `heal-cards` → `done` |
| **Assignee** | Create (Issue) | `create-from-template` (default `owner.github_user`); `claim` / `set-assignee` |
| **Linked PR** | PR exists | `mention-pr --pr N --last --agent <agent>` |

**Create as Issue** (`item_kind_default: issue`). Draft = scratch only (`--no-assignee` escape hatch). `promote-to-issue --last --agent <name>` when still Draft. `mention-pr` auto-promotes when `promote_to_issue_on_pr: true`.

```bash
python3 -m agent_colony project create-from-template \
  --template slice --title "[P1] …" --status ready \
  --priority p1 --size s --estimate 1 --agent implementer
python3 -m agent_colony project claim --last --agent implementer
python3 -m agent_colony project mention-pr --pr N --last --agent implementer
```

Plain `project create` needs follow-up `set-field` for Priority/Size/Estimate. Exit Notes: `[P0]…; [P1]…` and `Priority=p? · Size=? · Estimate=?`. Missing Tier-1 or Start on active statuses / End on Done = **incomplete Exit**.

## Collaboration

| Surface | Human | Agents |
|---------|-------|--------|
| Status / Priority / Size / cards | Yes | Yes (rights below) |
| Ready prioritization / roadmap | **Owner** | Consume Ready; create agreed work |
| Views, workflows, Insights, README | **Owner only** | **Never** (browser assist only if human asks) |
| PR gates, audits, secrets | Local | Local (`local_only`) |

**Issue vs board Status:** independent by default. Opt-in bridge: `conventions.close_linked_issue_on_cleanup` → `finalize.py` closes linked Issue after merge cleanup. CLI: `project close-linked-issue --pr N` (requires Status=Done first).

**Repair:** `project doctor` · `heal-cards --check|--apply [--fill-tier1]` · `validate-item` · `outbox flush` if QUEUED.

| WARN | Meaning | Action |
|------|---------|--------|
| Done + missing End date | Historical hygiene | `heal-cards --apply` (consent) |
| Ready / In progress missing Tier-1 | Active card incomplete | Fill on own card; `--fill-tier1` only if defaults OK |
| Empty Ready | No work queued | `create-from-template` → `set-section` → `claim` |

**Day-0 / Day-N:** Human owns views + Ready order. Agent: `entry` → one card → Exit Status+Notes. Fill Acceptance/Rollback before In review/Done. Canon: `project-board-collaboration.md` § Day-0 / Day-N.

**Rules:** one In progress per human assignee; Acceptance/Rollback/Notes on card body; no dual-mirror under `board_only` (DRIFT-009); read-only `export` never writes Status; post-merge Done via `merge.py`.

| Agent | Exit (must update board) |
|-------|--------------------------|
| implementer | In progress → In review (PR) → Done; fields on own card |
| test-runner / verifier | Stay on card; → In review or Done with Notes |
| drift-guard | Drift-pass → Done; cite board Status; hand remediation via Notes/Ready — **no** silent tracker edits |
| auditor | Audit card → In review/Done; Notes → artifact paths |

Status path: `Ready → In progress → In review → Done`

## Procedure (Pattern A)

Never paste placeholder `--id`. After create, use `--last`. `project guide --agent <name>`.

| Need | Template / action |
|------|-------------------|
| slice / feature / chore | `create-from-template --template slice` |
| bug / fix | `create-from-template --template bug` |
| research | `--template research` |
| audit pass | `--template slice` + `[AUDIT] …` then `claim --last` |
| test-runner / verifier | claim/continue only — **no** create |

**Recipes:**

1. `project doctor` · `project guide --agent implementer`
2. `project status` · `project list [--status ready|in_progress|in_review]`
3. **Create:** `create-from-template … --priority p1 --size s --estimate 1 --agent <agent>` (prefer `--acceptance` / `--rollback`)
4. **Claim:** `project claim --last --agent <this-agent>`
5. **Body:** `set-section --section acceptance|rollback --text '…' --last --agent <agent>`
6. **Handoff:** `handoff --last --agent <this-agent> --next <agent> [--to in_review|done]` — **EXIT_VALIDATION (5)** when Acceptance/Rollback are `(TBD)` (also on `set-status --to in_review|done`)
7. **Validate:** `validate-item --last`
8. **Atomics:** `set-status` · `set-field` · `set-section` · `promote-to-issue` · `mention-pr` · `append-notes --agent` · `get --last` · `export`

Exit codes: `0` ok · `2` usage/config · `3` gh · `4` not found · **`5` validation** · **`6` queued** (outbox; flush later).

Rate-limit: `project outbox status` / `project queue` / `project outbox flush` — see `project_ssot.outbox` in collaboration YAML.

## Dual-write ban

When `board_only`, do **not** mark the same slice `in_progress` in `work-tracker.md`. PR/audit artifacts stay local.

## Evidence contract

Cite CLI output or `gh project` JSON. Label **Unknown** when board unreachable → `fallback: local_trackers` only.

## Exit criteria

- [ ] Entry read board (or explicit offline fallback)
- [ ] Exit updated Status or Notes + next agent
- [ ] If EXIT_QUEUED: `outbox status`; no API hammering
- [ ] Handoff line with real `item_id`
- [ ] No dual-write; no unprompted Project view/workflow edits

## Anti-patterns

Chat-only completion · hardcoded field ids · dual-write under `board_only` · multi-step claim without `project claim` · bare Notes without `--agent` · reshuffling Ready without human ask · pasting Project UI into terminal
