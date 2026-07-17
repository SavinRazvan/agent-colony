<!--
File: HANDOFF.md
Path: HANDOFF.md
Role: Full experiment handoff for agents continuing Project-SSOT work in this sibling repo.
Used By:
 - Cursor agents opening this workspace
 - Maintainer onboarding the experiment
Depends On:
 - Production kit: https://github.com/SavinRazvan/mas-workflow-kit (do not mutate for this experiment)
 - GitHub Project: https://github.com/users/SavinRazvan/projects/3
 - Local settings: .local/user_settings/github.collaboration.yaml (identity + project_ssot)
Notes:
 - Kit mirrored 2026-07-17 (merge commit 1cb6dd7 · tip 8a779fa / v0.4.0).
 - North star: GitHub Project replaces local tracker markdown as SSOT for collaborators + agents.
-->

# HANDOFF — GitHub Project as agent SSOT (experiment)

**Read this file first** when opening `mas-workflow-kit-project-ssot` in Cursor.

| Field | Value |
|-------|--------|
| **Experiment repo** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot |
| **Production kit (DO NOT break)** | https://github.com/SavinRazvan/mas-workflow-kit |
| **Production tip at handoff** | `8a779fa` · tag **`v0.4.0`** (mirrored here as merge `1cb6dd7`) |
| **GitHub Project board** | https://github.com/users/SavinRazvan/projects/3 — **AI Project Playground** |
| **Project number / owner** | `#3` / `SavinRazvan` (user project) |
| **Project node id** | `PVT_kwHOBl46-84A9KZx` |
| **Handoff date** | 2026-07-17 |
| **Prior session agents** | Composer (explorer) · implementer (kit mirror) · design alignment |
| **Human owner** | Savin Ionuț Răzvan · `@SavinRazvan` |

---

## 1. Goal (north star)

**Hypothesis (clarified):** Collaborators and agents treat the configured **GitHub Project** as the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only`. Every agent **reads the board on Entry** and **updates Status and Notes on Exit**; card body indexes handoffs — not chat alone. Local trackers are **offline fallback only**; PR gates, audits, secrets stay local. Optional **read-only** exports may cache snapshots but must never compete with board Status.

**Why:**

- One shared UI for humans (easier than per-machine `.local/` files).
- Multiple collaborators and **multiple agents** create, claim, and complete the same tasks.
- Board Status / Priority / Size become the coordination bus (Ready → In progress → In review → Done).

**Settings story (same habit as identity):** Project config lives in **`.local/user_settings/github.collaboration.yaml`** next to `owner.display_name` / `owner.github_user` — one worksheet agents always read. Do **not** invent a second settings file as the primary habit (a separate `github.projects.yaml` was an earlier idea; **superseded**).

**What still stays local / in-repo (not “moved to the board”):**

| Keep | Why |
|------|-----|
| PR Pattern A (`prepare.py` GATES, review/prep/merge scripts) | Merge readiness is code-side; post-merge card → Done is Pattern A (`merge.py`) |
| Commit/PR attribution (`owner`, trailers, pipelines) | Already in collab YAML |
| `.venv`, secrets, coverage dumps | Machine-local |
| Offline fallback trackers | If no `project` scope / no `gh` — **resume-only** local trackers; never a second writer under `board_only` |
| Read-only board export (optional) | Snapshot cache for audits/ICC later — never writes Status |

**Non-goal (this experiment):** Do **not** rewrite production `mas-workflow-kit` `main` until this sibling proves the model. Marketplace `v0.4.0` consumers stay on markdown SSOT until an explicit port. Do **not** dual-mirror local trackers + board “for safety.”

**Success looks like:**

1. Agents **create** and **load** tasks from the configured Project (not from `work-tracker.md`).
2. Agent Anchors read `project_ssot` from collab YAML → board; Exit updates card Status and Notes (continuation contract).
3. Humans follow progress **only** on the Project UI; local tracker markdown is **offline fallback only** (not a writable SSOT under `board_only`).
4. Clear auth (`project` scopes) + settings onboarding for every collaborator who opts in.
5. Rollback = abandon this sibling repo; production kit unchanged.

**Failure / abort if:**

- Board API too fragile for agent loops, or auth story too heavy for consumers.
- Dual SSOT (board + markdown) causes worse drift than today — **board must win**; do not leave two writers.
- Gates / Pattern A cannot coexist with board-first workflow.

---

## 2. Safety model (why this repo exists)

GitHub does **not** allow forking your own repo to yourself. Isolation = **sibling public repo**:

| Repo | Role |
|------|------|
| `mas-workflow-kit` | Production / marketplace source of truth |
| `mas-workflow-kit-project-ssot` | **This** experiment sandbox |

Also related (unrelated experiment): `mas-workflow-kit-trae` — ignore unless asked.

**Rule for agents:** Never push experiment-only SSOT changes to `mas-workflow-kit` unless the human explicitly asks to port a proven design.

---

## 3. Design

### 3.1 Current kit agent model (production baseline)

Agents live under `.cursor/agents/` (7): `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `workflow-drift-guard`, `integrator-mas-agent`, `researcher`.

They are **session Task agents**, not always-on GitHub bots. Today they read **local** `.local/index-and-planning/current/*` first (`session-pointer.md` → `plan.md` → `work-tracker.md`).

PR lifecycle stays Pattern A: scripts in `.ai_infra/scripts/pr/` (`review` / `prepare` / `merge`); `prepare.py` GATES are SSOT for merge prep.

### 3.2 Target experiment model (board replaces trackers)

```text
.local/user_settings/github.collaboration.yaml
  owner + project_ssot  →  every agent reads this once

GitHub Project #3       →  create / list / claim / status (human + all agents)
                        →  optional: Issue / linked PR
                        →  implementer / test-runner / … (code + gates)
                        →  PR skills (still Pattern A)
                        →  card → In review → Done

.local/index-and-planning/*.md
                        →  DEPRECATED as SSOT (offline fallback only, then remove writes)
```

**Multi-agent / multi-collaborator conventions:**

| Rule | Detail |
|------|--------|
| One claim | Prefer one primary **In progress** card per agent/assignee |
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
| Anchor every agent procedure on `project_ssot` | Force-push / rewrite production kit history |
| Hand off via card Status + Assignees | Require marketplace consumers to use Projects before port |
| Fall back to local trackers only when board unavailable | Leave dual SSOT without a winner |

### 3.3 Settings — `project_ssot` in collaboration YAML (canonical)

Extend **`.local/user_settings/github.collaboration.yaml`** (exemplar under `.ai_infra/templates/user-settings/`). Schema already allows `additionalProperties: true`; tighten later in this experiment.

Target shape (not fully live until BOARD-SPIKE / wiring slices):

```yaml
# .local/user_settings/github.collaboration.yaml
version: 1
owner:
  display_name: "Savin Ionuț Răzvan"
  github_user: "@SavinRazvan"

# NEW — agents always read this (same file as identity)
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

**Tools:** Pattern A via `gh project …` first; optional GitHub MCP later (`/connect-external-mcp`). Optional committed pointer in `project.config.yaml` for “canonical board” — deferred.

### 3.4 Auth (every collaborator who manages the board)

```bash
gh auth refresh --hostname github.com -s read:project,project
# Device URL: https://github.com/login/device
```

Required scopes: `read:project` (read), `project` (write).  
Existing `repo` / `workflow` suffice for PR workflow without Projects.

**Later product options:** per-dev `gh auth` · GitHub MCP + PAT/OAuth · GitHub App / Actions bot (org-level).

---

## 4. Experiments already run (live evidence)

### 4.1 Consumer kit verification (Smart-Notes, earlier session)

On `~/Projects/Smart-Notes` with kit **0.4.0**:

- `python3 -m cursor_workflow` → usage error without subcommand (**expected**)
- `health` → `kit_version: 0.4.0`, **PASS**
- `gates` → pytest green; **governance FAIL** on 8 app unit tests missing file headers under `tests/modules/core|notes/` — **legitimate project gap**, not outdated kit
- Distinction: consumer **`prepare.py`** = 2 gates; **`cursor_workflow gates`** = 4 substantive (+ doc-facts skip)

### 4.2 Tag / release (production kit)

Human deleted old tags/releases; agent recreated **only** `v0.4.0` on `8a779fa` + GitHub Release (Latest).  
Release: https://github.com/SavinRazvan/mas-workflow-kit/releases/tag/v0.4.0

### 4.3 Project board smoke (2026-07-17) — confirmed in UI

Auth refreshed with `project` scope. Board had **3 DraftIssue** items (explorer):

| Title | Item id | Status | Priority | Size |
|-------|---------|--------|----------|------|
| `[Explorer] Hello from Cursor agent` | `PVTI_lAHOBl46-84A9KZxzgzNYB4` | **Ready** | — | — |
| `[Explorer] Triage: document board fields` | `PVTI_lAHOBl46-84A9KZxzgzNYCY` | **In progress** | — | — |
| `[Explorer] Priority P1 sample` | `PVTI_lAHOBl46-84A9KZxzgzNYCw` | **Backlog** | **P1** | **S** |

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
gh project item-create 3 --owner SavinRazvan --title "…" --body "…" --format json
gh project item-edit --project-id PVT_kwHOBl46-84A9KZx --id PVTI_… \
  --field-id PVTSSF_lAHOBl46-84A9KZxzgw8mco --single-select-option-id 47fc9ee4
gh project item-list 3 --owner SavinRazvan --format json
```

Explorer drafts are **safe to delete** when cleaning the board.

### 4.4 Kit mirror into this repo (2026-07-17)

- Merge `kit/main` → experiment `main`: commit **`1cb6dd7`** (pushed).
- `health` / `contributors validate` PASS; `integrate validate` P0 PASS (P1 INT-013 = experiment README intentionally omits full kit agent roster — accepted divergence).

---

## 5. Conversation intent summary

1. Verify consumer CLI / gates vs kit 0.4.0; recreate clean `v0.4.0` release.
2. Prove Cursor agent can drive GitHub Projects with `project` scope → **yes**.
3. Isolate experiment in **sibling repo**; mirror full kit (done).
4. **North star (human, 2026-07-17):** replace local tracker artifacts with Project SSOT; configure board in **`github.collaboration.yaml`** like display name / GitHub user; **all agent procedures** create/load/update tasks on that Project for multi-collaborator / multi-agent work.
5. Port to production kit only after this experiment proves the model.

---

## 6. Recommended agent roster

| Agent / skill | Use for |
|---------------|---------|
| **integrator-mas-agent** + `mas-infrastructure-integration` | Wire `project_ssot` settings + shared board skill/CLI + first agent surfaces (independent-governed → then MAS Anchors) |
| **implementer** | First agent Anchor rewrite to board-first; product/code slices |
| **enterprise-auditor** | Alignment before claiming trackers deleted / before production port |
| **verifier** | Prove board-SSOT claims with `gh project` evidence |
| **workflow-drift-guard** | New rules: board vs leftover markdown drift |

Do **not** run production marketplace publish from this repo.

---

## 7. Phased plan (ordered)

### A. Done — workspace

- [x] Mirror / merge production kit (`1cb6dd7`)
- [x] `gh` has `project` scope; board reachable
- [x] Collab identity filled (`contributors validate` PASS)

### B. BOARD-SPIKE-001 (P0) — done

- [x] Add **`project_ssot`** block to local + **exemplar** `github.collaboration.yaml` (field ids from §4.3).
- [x] Shared skill/CLI: list Ready, create item, set Status/Priority/Size (`cursor_workflow project` / `gh project` Pattern A).
- [x] Thin `.cursor/agents/project-board.md` (**independent-governed**, ADR-006).
- [x] Vertical demo: `[Explorer] Hello…` → In progress → Done on the board.
- [x] ADR-008 **only in this repo**: board-only SSOT vs offline fallback.

### C. BOARD-ANCHOR-002 (P1) — done

- [x] Rewrite agent **Entry/Exit Anchors** starting with `implementer`: read `project_ssot` → board; stop writing trackers as SSOT (fallback only).

### D. BOARD-ROLL-003 (P2) — done

- [x] Remaining agents board-first; DRIFT-009 dual-write guard; AGENTS/experiment overlay.

### E. Explicitly defer (until human PORT-GATE)

- Porting to `mas-workflow-kit` main / marketplace bump
- Deleting production `.local` tracker contract for consumers
- Always-on GitHub Actions bot
- Requiring GitHub MCP before `gh` path works
- ICC Control Center board tab (see §8)

---

## 8. Risks & open questions

| Question | Notes |
|----------|-------|
| Board-only vs dual mirror? | **Board wins — only writable SSOT.** Offline fallback only; no dual writers “for safety.” |
| DraftIssue vs real Issues? | Drafts OK for smoke; Issues better for PR linking. |
| Consumer installs? | Projects opt-in until production port. |
| Offline / no `gh`? | `fallback: local_trackers` then resume board sync. |
| Card → which repo? | Convention: Repository field or body path; default = this experiment repo. |
| Control Center dashboards? | **Deferred (EA-010).** Read-only `project export` may land first; ICC panel that *reads* the export is future — never a second writer. Humans follow Project #3 UI for backlog/status. |
| Who updates the Project? | **Every agent** Entry=read board; Exit=update Status/Notes. Post-merge Done = Pattern A (`merge.py`). Rights: `project-board-ssot` skill § Continuation; ops `project-board-collaboration.md`. **You:** views, workflows, Insights, README, status updates, Ready prioritization. |

---

## 9. Key links

- Board: https://github.com/users/SavinRazvan/projects/3  
- Experiment repo: https://github.com/SavinRazvan/mas-workflow-kit-project-ssot  
- Production kit: https://github.com/SavinRazvan/mas-workflow-kit  
- Release: https://github.com/SavinRazvan/mas-workflow-kit/releases/tag/v0.4.0  
- Settings (local): `.local/user_settings/github.collaboration.yaml`  
- Kit docs: `.ai_infra/docs/operations/connect-external-mcp.md`, `consumer-quickstart.md`, ADR-004 (MCP), ADR-006 (agent integration)

---

## 10. Handoff checklist for receiving agent

- [x] Read this `HANDOFF.md` entirely (north star = board replaces tracker SSOT)  
- [x] Confirm `gh` has `project` scope  
- [x] Open board URL; explorer items present (or recreate)  
- [x] Mirror / merge production kit into this repo  
- [x] Agree with human: Project in **collab YAML**; all agents use Project; phased P0→P2  
- [x] Run **BOARD-SPIKE-001** / ANCHOR / ROLL — no production port without human sign-off  
- [x] Update this file’s “Last agent / Last updated” when you finish a slice  

**Last agent (writer):** implementer (Cursor) · **Last updated:** 2026-07-17  
**Next agent:** maintainer (@SavinRazvan) — **PORT-GATE** approve or defer production port (board card `PVTI_lAHOBl46-84A9KZxzgzOZuE`).

**Implemented (2026-07-17):** `cursor_workflow project` CLI, `project-board` agent/skill, ADR-008, Ready→Done demo, all agent Anchors board-first, DRIFT-009, payload sync, experiment overlay installed, board seeded, doc-facts hygiene.

### PORT-GATE decision (human)

| Field | Value |
|-------|--------|
| **Status** | **Deferred** until explicit approve (safe default per ADR-008 §7) |
| **Board card** | `[PORT-GATE] …` · `PVTI_lAHOBl46-84A9KZxzgzOZuE` · In progress / P0 |
| **Approve** | Record date + “PORT approved” here; then open port PR to `mas-workflow-kit` |
| **Defer** | Leave marketplace on markdown SSOT; keep iterating in this sibling |
