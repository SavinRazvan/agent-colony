<!--
File: HANDOFF.md
Path: HANDOFF.md
Role: Product handoff for board+local SSOT kit in this repository.
Used By:
 - Cursor agents opening this workspace
 - Maintainer onboarding
Depends On:
 - Lineage (read-only): https://github.com/SavinRazvan/mas-workflow-kit
 - GitHub Project: https://github.com/users/SavinRazvan/projects/3
 - Local settings: .local/user_settings/github.collaboration.yaml (identity + project_ssot)
Notes:
 - Kit mirrored 2026-07-17 (merge commit 1cb6dd7 · tip 8a779fa / v0.4.0).
 - This repository is the product — permanently decoupled; STANDALONE 2026-07-18.
-->

# HANDOFF — GitHub Project as agent SSOT (product)

**Read this file first** when opening `mas-workflow-kit-project-ssot` in Cursor.

| Field | Value |
|-------|--------|
| **Product repo** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot |
| **Lineage (read-only)** | https://github.com/SavinRazvan/mas-workflow-kit — historical upstream; never merge doctrine back |
| **Upstream tip at mirror** | `8a779fa` · tag **`v0.4.0`** (mirrored here as merge `1cb6dd7`) |
| **GitHub Project board** | https://github.com/users/SavinRazvan/projects/3 — **AI Project Playground** |
| **Project number / owner** | `#3` / `SavinRazvan` (user project) |
| **Project node id** | `PVT_kwHOBl46-84A9KZx` |
| **Handoff date** | 2026-07-17 |
| **STANDALONE decided** | 2026-07-18 — this repo is the permanent product |
| **Human owner** | Savin Ionuț Răzvan · `@SavinRazvan` |

---

## 1. Goal (north star)

**This repository is the product** (`mas-workflow-kit-project-ssot`) — already separated from upstream; permanently decoupled. Separation is done; agents must not create a sibling, fork, or port doctrine back into `mas-workflow-kit`.

### Two surfaces (facts only)

| Surface | Writable? | Role |
|---------|-----------|------|
| **GitHub Project board** (`project_ssot` in `.local/user_settings/github.collaboration.yaml`) | **Only writable SSOT** for backlog, Status, Priority/Size, multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only` | Humans + agents track everything here. **Entry** reads the board; **Exit** updates Status and Notes. Card body indexes handoffs — not chat alone. |
| **Local artifacts** (`.local/…`, PR Pattern A, audits, gates, secrets, coverage) | Evidence / merge readiness / machine-local | Proves how work was verified and merged. **Never** a second Status writer under `board_only`. Offline fallback only when board disabled or `gh` unavailable. |

**Together:** board = structured coordination; local = evidence. No dual-mirror “for safety.”

**Why:**

- One shared UI for humans (easier than per-machine `.local/` files).
- Multiple collaborators and **multiple agents** create, claim, and complete the same tasks.
- Board Status / Priority / Size become the coordination bus (Ready → In progress → In review → Done).

**Settings story (same habit as identity):** Project config lives in **`.local/user_settings/github.collaboration.yaml`** next to `owner.display_name` / `owner.github_user` — one worksheet agents always read.

**What still stays local / in-repo (not “moved to the board”):**

| Keep | Why |
|------|-----|
| PR Pattern A (`prepare.py` GATES, review/prep/merge scripts) | Merge readiness is code-side; post-merge card → Done is Pattern A (`merge.py`) |
| Commit/PR attribution (`owner`, trailers, pipelines) | Already in collab YAML |
| `.venv`, secrets, coverage dumps | Machine-local |
| Offline fallback trackers | If no `project` scope / no `gh` — **resume-only** local trackers; never a second writer under `board_only` |
| Rate-limit outbox | `.local/generated-data/board-outbox.jsonl` via `project queue` / auto-enqueue; flush with `outbox flush` — buffer only, not SSOT |
| Read-only board export (optional) | Snapshot cache for audits/ICC later — never writes Status |

**Non-goals:** Do **not** dual-mirror local trackers + board “for safety.” Do **not** push this product’s doctrine into upstream `mas-workflow-kit`. Do **not** treat this repo as a temporary sandbox awaiting a port.

**Success looks like:**

1. Agents **create** and **load** tasks from the configured Project (not from `work-tracker.md`).
2. Agent Anchors read `project_ssot` from collab YAML → board; Exit updates card Status and Notes (continuation contract).
3. Humans follow progress **only** on the Project UI; local tracker markdown is **offline fallback only**.
4. Clear auth (`project` scopes) + settings onboarding for every collaborator who opts in.
5. Rollback = disable `project_ssot` / use `fallback: local_trackers` **in this repo** (not abandon the product).

**Failure / abort if:**

- Board API too fragile for agent loops, or auth story too heavy for consumers.
- Dual SSOT (board + markdown) causes worse drift — **board must win**; do not leave two writers.
- Gates / Pattern A cannot coexist with board-first workflow.

---

## 2. Safety model (already separated)

GitHub does **not** allow forking your own repo to yourself. Isolation was done via a **sibling public repo** — **this workspace is already that repo.**

| Repo | Role |
|------|------|
| `mas-workflow-kit` | Historical lineage / optional reference only |
| `mas-workflow-kit-project-ssot` | **This product** — board+local SSOT kit |

Also related (unrelated): `mas-workflow-kit-trae` — ignore unless asked.

**Rule for agents:** Never push board-SSOT or product doctrine to `mas-workflow-kit`. Do not instruct anyone to “create sibling / mirror kit” again — that work is done.

---

## 3. Design

### 3.1 Historical kit baseline (pre-board)

Agents live under `.cursor/agents/` (now 8 including `project-board`): `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `workflow-drift-guard`, `integrator-mas-agent`, `researcher`, `project-board`.

They are **session Task agents**, not always-on GitHub bots. **Before board SSOT**, they read **local** `.local/index-and-planning/current/*` first (`session-pointer.md` → `plan.md` → `work-tracker.md`). That Entry path is **historical** — see §3.2 for current product behavior.

PR lifecycle stays Pattern A: scripts in `.ai_infra/scripts/pr/` (`review` / `prepare` / `merge`); `prepare.py` GATES are SSOT for merge prep.

### 3.2 Shipped product model (board replaces trackers as Status SSOT)

```text
.local/user_settings/github.collaboration.yaml
  owner + project_ssot  →  every agent reads this once

GitHub Project #3       →  create / list / claim / status (human + all agents)
                        →  optional: Issue / linked PR
                        →  implementer / test-runner / … (code + gates)
                        →  PR skills (still Pattern A)
                        →  card → In review → Done

.local/index-and-planning/*.md
                        →  offline fallback only (not writable SSOT under board_only)
```

**Multi-agent / multi-collaborator conventions:**

| Rule | Detail |
|------|--------|
| One claim | Prefer one primary **In progress** card per **human** assignee |
| Attribution | Notes: `@owner.github_user/<agent> · <ISO-8601-UTC> · …` via `append-notes --agent` (CLI stamps UTC); `next=@user/agent`; local `history/continuity-index.md` rolls ≥3 days |
| Queue | **Ready** (+ Priority P0/P1) = next work |
| Review | **In review** when PR open; **Done** after merge/close |
| Create | Agents may create DraftIssue/Issue on the Project when scoping work |
| No dual write | Do not update board **and** `work-tracker.md` as competing truth |

**Board fields on project #3:**

| Field | Type | Options / notes |
|-------|------|-----------------|
| Status | single select | Backlog, Ready, In progress, In review, Done |
| Priority | single select | P0, P1, P2 |
| Size | single select | XS, S, M, L, XL |
| Estimate, Iteration, Start/End date | present | unused in smoke |
| Title, Assignees, Labels, Linked PRs, Repo, … | standard | |

**Boundaries:**

| Do | Do not |
|----|--------|
| List/filter board; create drafts/issues; set Status/Priority/Size | Bypass `prepare.py` gates |
| Anchor every agent procedure on `project_ssot` | Force-push / rewrite upstream kit history |
| Hand off via card Status + Notes | Push doctrine into `mas-workflow-kit` |
| Fall back to local trackers only when board unavailable | Leave dual SSOT without a winner |

### 3.3 Settings — `project_ssot` in collaboration YAML (canonical)

Extend **`.local/user_settings/github.collaboration.yaml`** (exemplar under `.ai_infra/templates/user-settings/`).

```yaml
# .local/user_settings/github.collaboration.yaml
version: 1
owner:
  display_name: "Savin Ionuț Răzvan"
  github_user: "@SavinRazvan"

project_ssot:
  enabled: true
  owner: SavinRazvan
  number: 3
  url: https://github.com/users/SavinRazvan/projects/3
  project_id: PVT_kwHOBl46-84A9KZx
  fields:
    status: PVTSSF_lAHOBl46-84A9KZxzgw8mco
    priority: PVTSSF_lAHOBl46-84A9KZxzgw8mrI
    size: PVTSSF_lAHOBl46-84A9KZxzgw8mrM
  sync_policy: board_only          # board_only | board_first | offline_fallback
  fallback: local_trackers         # only when enabled=false or no project scope

# existing: commit_provenance, pr_collaboration.pipelines, …
```

**Tools:** Pattern A via `gh project …` first; optional GitHub MCP later (`/connect-external-mcp`).

### 3.4 Auth (every collaborator who manages the board)

```bash
gh auth refresh --hostname github.com -s read:project,project
# Device URL: https://github.com/login/device
```

Required scopes: `read:project` (read), `project` (write).  
Existing `repo` / `workflow` suffice for PR workflow without Projects.

**Later product options:** per-dev `gh auth` · GitHub MCP + PAT/OAuth · GitHub App / Actions bot (org-level).

---

## 4. Evidence already run

### 4.1 Consumer kit verification (Smart-Notes, earlier session)

On `~/Projects/Smart-Notes` with kit **0.4.0**:

- `python3 -m cursor_workflow` → usage error without subcommand (**expected**)
- `health` → `kit_version: 0.4.0`, **PASS**
- `gates` → pytest green; **governance FAIL** on 8 app unit tests missing file headers under `tests/modules/core|notes/` — **legitimate project gap**, not outdated kit

### 4.2 Upstream kit tag at fork time (lineage)

Human deleted old tags/releases; agent recreated **only** `v0.4.0` on `8a779fa` + GitHub Release (Latest) on the **upstream** kit.  
Release: https://github.com/SavinRazvan/mas-workflow-kit/releases/tag/v0.4.0

### 4.3 Project board smoke (2026-07-17) — confirmed in UI

Auth refreshed with `project` scope. Field/option ids for Status / Priority / Size are in collab YAML and CLI.

**Status option ids (for `gh project item-edit`):**

| Status | option id |
|--------|-----------|
| Backlog | `f75ad846` |
| Ready | `08afe404` |
| In progress | `47fc9ee4` |
| In review | `4cc61d42` |
| Done | `98236657` |

**Priority option ids:** P0=`79628723` · P1=`0a877460` · P2=`da944a9c`  
**Size option ids:** XS=`eff732af` · S=`9592a5a3` · M=`9728cbdc` · L=`c53df028` · XL=`7b141a16`

```bash
python3 -m cursor_workflow project status
python3 -m cursor_workflow project list
python3 -m cursor_workflow project claim --last --agent implementer
# atomics (power use): project set-status --last --to in_progress
```

### 4.4 Kit mirror into this repo (2026-07-17)

- Merge `kit/main` → this `main`: commit **`1cb6dd7`** (pushed). Isolation complete.

---

## 5. Conversation intent summary

1. Verify consumer CLI / gates vs kit 0.4.0; recreate clean `v0.4.0` release (upstream).
2. Prove Cursor agent can drive GitHub Projects with `project` scope → **yes**.
3. Isolate in **sibling repo**; mirror full kit (**done** — this workspace).
4. **North star:** replace local tracker Status SSOT with Project board; configure board in **`github.collaboration.yaml`**; **all agent procedures** create/load/update tasks on that Project.
5. **STANDALONE 2026-07-18:** this repo is the permanent product — **no** port back to `mas-workflow-kit`.

---

## 6. Recommended agent roster

| Agent / skill | Use for |
|---------------|---------|
| **integrator-mas-agent** + `mas-infrastructure-integration` | Wire `project_ssot` settings + shared board skill/CLI |
| **implementer** | Product/code slices; board-first Anchors |
| **enterprise-auditor** | Alignment / scorecard |
| **verifier** | Prove board-SSOT claims with evidence |
| **workflow-drift-guard** | Board vs leftover markdown drift (DRIFT-009/010) |
| **project-board** | Triage / Status transitions (independent-governed) |

Do **not** run upstream marketplace publish from this repo against `mas-workflow-kit`.

---

## 7. Phased plan (ordered)

### A–D. Done — workspace + board SSOT

- [x] Mirror / merge upstream kit (`1cb6dd7`); `gh` has `project` scope
- [x] `project_ssot` + CLI + `project-board` + ADR-008
- [x] All agent Anchors board-first; DRIFT-009/010; A→B→C; FIX-NOTES-DI

### E. Explicitly defer (product backlog — not a port gate)

- ICC Control Center board tab (EA-010 Ready)
- Always-on GitHub Actions bot
- Requiring GitHub MCP before `gh` path works

---

## 8. Risks & open questions

| Question | Notes |
|----------|-------|
| Board-only vs dual mirror? | **Board wins — only writable SSOT.** Offline fallback only; no dual writers “for safety.” |
| DraftIssue vs real Issues? | Default Draft (`item_kind_default: draft`); promote via `python3 -m cursor_workflow project promote-to-issue --last --agent <name>` or `mention-pr` auto when `promote_to_issue_on_pr` (default true). Issue-at-create when `item_kind_default: issue`. Do not leave shippable work as Draft through merge. |
| Tier-1 board fields? | **Start date** may set on `claim` (UTC). **Estimate** (and Priority/Size) via `set-field` on triage/own cards. **PR URL** via `mention-pr`. Iteration / Labels / Reviewers / End date out of scope for agents by default. Humans own Ready prioritization. |
| Consumer installs? | Install plugin from **this** repo: `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` |
| Offline / no `gh`? | `fallback: local_trackers` then resume board sync. |
| GraphQL rate-limit? | `project_ssot.outbox` — EXIT_QUEUED (6); `outbox flush` after reset. Never hammer API; outbox ≠ Status SSOT. |
| Card → which repo? | Convention: Repository field or body path; default = this product repo. |
| Control Center dashboards? | **Deferred (EA-010).** Read-only `project export` may land first; ICC panel that *reads* the export is future — never a second writer. |
| Who updates the Project? | **Every agent** Entry=read board; Exit=update Status/Notes. Post-merge Done = Pattern A (`merge.py`). Rights: `project-board-ssot` skill § Continuation; ops `project-board-collaboration.md`. **You:** views, workflows, Insights, README, status updates, Ready prioritization / product roadmap. |

---

## 9. Key links

- Board: https://github.com/users/SavinRazvan/projects/3  
- **Product repo:** https://github.com/SavinRazvan/mas-workflow-kit-project-ssot  
- Lineage (read-only): https://github.com/SavinRazvan/mas-workflow-kit  
- Upstream release at mirror: https://github.com/SavinRazvan/mas-workflow-kit/releases/tag/v0.4.0  
- Settings (local): `.local/user_settings/github.collaboration.yaml`  
- Docs: `.ai_infra/docs/operations/connect-external-mcp.md`, `consumer-quickstart.md`, ADR-004 (MCP), ADR-006 (agent integration), ADR-008 (board SSOT)

---

## 10. Handoff checklist for receiving agent

- [x] Read this `HANDOFF.md` entirely (north star = board + local artifacts)  
- [x] Confirm `gh` has `project` scope  
- [x] Open board URL  
- [x] Mirror / merge upstream kit into this repo (done historically)  
- [x] BOARD-SPIKE / ANCHOR / ROLL / A→B→C / FIX-NOTES-DI / BOARD-TIER1 / BOARD-PROMOTE shipped  
- [x] **STANDALONE 2026-07-18** — no upstream port  
- [ ] Update this file’s “Last agent / Last updated” when you finish a slice  

**Last agent (writer):** implementer (Cursor) · **Last updated:** 2026-07-18  
**Next agent:** any agent — Entry=`project status`; Ready backlog includes EA-010.

**Implemented:** `cursor_workflow project` CLI, `project-board` agent/skill, ADR-008, all agent Anchors board-first, DRIFT-009/010, merge.py board sync, FIX-NOTES-DI, BOARD-TIER1 (claim Start date + Estimate `set-field` + `mention-pr`), BOARD-PROMOTE (`promote-to-issue` + `mention-pr` auto), payload sync, `project-ssot-precedence` overlay.

### STANDALONE decision (human)

| Field | Value |
|-------|--------|
| **Status** | **STANDALONE decided** 2026-07-18 |
| **Board card** | Was `[PORT-GATE] …` · `PVTI_lAHOBl46-84A9KZxzgzOZuE` → **Done** |
| **Decision** | This repo is the permanent product. **No** port to `mas-workflow-kit`. Board = only writable SSOT; local = evidence. |
| **Next** | Ready backlog (e.g. EA-010) / normal slices |
