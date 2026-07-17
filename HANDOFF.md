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
Notes:
 - This repo starts empty of kit code; first setup step is mirror kit main (see §7).
-->

# HANDOFF — GitHub Project as agent SSOT (experiment)

**Read this file first** when opening `mas-workflow-kit-project-ssot` in Cursor.

| Field | Value |
|-------|--------|
| **Experiment repo** | https://github.com/SavinRazvan/mas-workflow-kit-project-ssot |
| **Production kit (DO NOT break)** | https://github.com/SavinRazvan/mas-workflow-kit |
| **Production tip at handoff** | `8a779fa` · tag **`v0.4.0`** (2026-07-15 retag on current main) |
| **GitHub Project board** | https://github.com/users/SavinRazvan/projects/3 — **AI Project Playground** |
| **Project number / owner** | `#3` / `SavinRazvan` (user project) |
| **Project node id** | `PVT_kwHOBl46-84A9KZx` |
| **Handoff date** | 2026-07-17 |
| **Prior session agents** | Composer (explorer) · verifier · enterprise-auditor (consumer gates review earlier) |
| **Human owner** | Savin Ionuț Răzvan · `@SavinRazvan` |

---

## 1. Goal (what we are trying to prove)

**Hypothesis:** Maintainers (and agents) can treat a **GitHub Project board** as the primary backlog / status UI instead of (or ahead of) local markdown trackers under `.local/index-and-planning/current/` (`plan.md`, `work-tracker.md`, `session-pointer.md`).

**Why:** Human-facing board UI is easier for one person and for multiple maintainers than chasing markdown files. Agents would **anchor** on board Status / Priority / Size, then implement and move cards.

**Non-goal (this experiment):** Do **not** rewrite production `mas-workflow-kit` `main` until the sibling experiment proves the model. Marketplace `v0.4.0` consumers stay on markdown SSOT.

**Success looks like:**

1. Agent reads board → picks next Ready/P1 item → works in a repo → moves card In progress → Done.
2. Humans only need the Project UI to follow progress (optional thin local mirror OK).
3. Clear auth/settings story for maintainers who opt in (`project` scopes / MCP).
4. Rollback = abandon this sibling repo; production kit unchanged.

**Failure / abort if:**

- Board API too fragile for agent loops, or auth story too heavy for consumers.
- Dual SSOT (board + markdown) causes worse drift than today.
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

## 3. What we already discussed (design)

### 3.1 Current kit agent model (production)

Agents live under `.cursor/agents/` (7): `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `workflow-drift-guard`, `integrator-mas-agent`, `researcher`.

They are **session Task agents**, not always-on GitHub bots. They read **local** `.local/index-and-planning/current/*` first (`session-pointer.md` → `plan.md` → `work-tracker.md`).

PR lifecycle stays Pattern A: scripts in `.ai_infra/scripts/pr/` (`review` / `prepare` / `merge`); `prepare.py` GATES are SSOT for merge prep.

### 3.2 Proposed experiment model

```text
GitHub Project #3  →  triage / status (human + agent)
                   →  optional: open Issue / link PR
                   →  implementer (code in experiment kit or linked app)
                   →  PR skills (still Pattern A)
                   →  move card Status / Priority

.local/*.md        →  thin cache OR deprecate gradually (decide after spike)
```

**Board fields already on project #3 (useful for agents):**

| Field | Type | Options / notes |
|-------|------|-----------------|
| Status | single select | Backlog, Ready, In progress, In review, Done |
| Priority | single select | P0, P1, P2 |
| Size | single select | XS, S, M, L, XL |
| Estimate, Iteration, Start/End date | present | unused in smoke |
| Title, Assignees, Labels, Linked PRs, Repo, … | standard | |

**Suggested agent boundaries:**

| Do | Do not |
|----|--------|
| List/filter board; create drafts; set Status/Priority/Size | Bypass `prepare.py` gates |
| Sync “next slice” from Ready + P0/P1 | Force-push / rewrite production kit history |
| Hand off to implementer / PR skills | Require every consumer to use Projects |

### 3.3 Settings / config placement (discussed, not implemented)

`.local/user_settings/github.collaboration.yaml` today = **identity + commit trailers + PR pipelines only**. Schema allows extra keys (`additionalProperties: true`) but **nothing reads a Project block yet**.

**Recommendation from design talk:**

1. Keep collab YAML for Author / GitHub-User / PR pipelines.
2. Prefer new worksheet: `.local/user_settings/github.projects.yaml` (exemplar + schema later) for board URL, owner, number, field ids, sync policy.
3. Optional committed pointer in `project.config.yaml` for “canonical board”.
4. Tools via `mcp.agents.yaml` → GitHub MCP **or** document `gh project …`.

Hypothetical shape (not live):

```yaml
# .local/user_settings/github.projects.yaml (proposed)
version: 1
projects:
  playground:
    owner: SavinRazvan
    number: 3
    url: https://github.com/users/SavinRazvan/projects/3
    project_id: PVT_kwHOBl46-84A9KZx
    status_field_id: PVTSSF_lAHOBl46-84A9KZxzgw8mco
    priority_field_id: PVTSSF_lAHOBl46-84A9KZxzgw8mrI
    size_field_id: PVTSSF_lAHOBl46-84A9KZxzgw8mrM
    sync_policy: board_first   # board_first | tracker_first | dual_mirror
```

### 3.4 Auth (every maintainer who manages boards)

One-time (or MCP equivalent), **not** required for normal kit consumers who only use local markdown + PR scripts:

```bash
gh auth refresh --hostname github.com -s read:project,project
# Device URL: https://github.com/login/device
```

Required scopes for Projects API: `read:project` (read), `project` (write).  
Existing `repo` / `workflow` are enough for PR workflow without Projects.

**Product options later:** per-dev `gh auth` · GitHub MCP + PAT/OAuth in Cursor secrets · GitHub App / Actions bot (org-level, users don’t refresh).

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

Auth refreshed with `project` scope. Board was empty; agent created **3 DraftIssue** items:

| Title | Item id | Status | Priority | Size |
|-------|---------|--------|----------|------|
| `[Explorer] Hello from Cursor agent` | `PVTI_lAHOBl46-84A9KZxzgzNYB4` | **Ready** | — | — |
| `[Explorer] Triage: document board fields` | `PVTI_lAHOBl46-84A9KZxzgzNYCY` | **In progress** | — | — |
| `[Explorer] Priority P1 sample` | `PVTI_lAHOBl46-84A9KZxzgzNYCw` | **Backlog** | **P1** | **S** |

Human confirmed visibility on [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) (Status board / backlog views).

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

Example create + edit:

```bash
gh project item-create 3 --owner SavinRazvan --title "…" --body "…" --format json
gh project item-edit --project-id PVT_kwHOBl46-84A9KZx --id PVTI_… \
  --field-id PVTSSF_lAHOBl46-84A9KZxzgw8mco --single-select-option-id 47fc9ee4
gh project item-list 3 --owner SavinRazvan --format json
```

Explorer drafts are **safe to delete** when cleaning the board.

---

## 5. Conversation intent summary

1. Verify consumer CLI / gates behavior vs kit 0.4.0 → install current; header failures are app compliance.
2. Recreate clean `v0.4.0` tag + release after manual tag cleanup.
3. Explore whether a Cursor agent can drive GitHub Projects → **yes**, with scopes.
4. Design user_settings extension for Projects → prefer dedicated YAML + MCP/`gh`.
5. Pivot idea: **anchor agents on Project instead of markdown** for maintainer UX.
6. Isolate in **sibling repo** (this one) before changing production kit.

---

## 6. Recommended agent roster for next work (this repo)

| Agent / skill | Use for |
|---------------|---------|
| **integrator-mas-agent** + `mas-infrastructure-integration` | Add `project-board` agent card, skill, settings exemplar, optional CLI |
| **implementer** | Code/docs slices inside this experiment tree once kit is mirrored |
| **enterprise-auditor** | Focused alignment before any port back to production kit |
| **verifier** | Prove board-first claims with `gh project` evidence |
| **workflow-drift-guard** | Only after trackers exist; may need new DRIFT rules for board sync |

Do **not** run production marketplace publish from this repo.

---

## 7. First actions for the next agent (ordered)

### A. Workspace setup (human may already be cloning)

```bash
# If kit code not yet present in this repo:
cd ~/Projects/mas-workflow-kit-project-ssot
git remote add kit https://github.com/SavinRazvan/mas-workflow-kit.git
git fetch kit
git merge kit/main --allow-unrelated-histories
# Resolve README conflict favoring: keep experiment README blurb + link to this HANDOFF
# Or: orphan replace — ask human; prefer merge so HANDOFF history stays

# Auth check
gh auth status   # must include 'project'
gh project view 3 --owner SavinRazvan
```

### B. Minimal spike (explorer mode — prefer small live diffs)

1. Document board ids in `.local/user_settings/github.projects.yaml` (create exemplar; gitignore path already kit-standard after merge).
2. Add agent `.cursor/agents/project-board.md` (independent-governed per ADR-006) + skill that:
   - Lists Ready items
   - Moves Status
   - Prints handoff line for implementer
3. One vertical demo: pick `[Explorer] Hello…` → In progress → Done, with human watching the board.
4. Write short ADR draft under `.ai_infra/docs/decisions/` **only in this repo**: board-first vs tracker-first.

### C. Explicitly defer

- Porting to `mas-workflow-kit` main / marketplace bump
- Deleting production `.local` tracker contract for consumers
- Always-on GitHub Actions bot (optional later)

---

## 8. Risks & open questions

| Question | Notes |
|----------|-------|
| Board-first vs dual mirror? | Dual without sync rules = drift. Prefer board-first + optional export. |
| DraftIssue vs real Issues? | Drafts good for smoke; Issues better for PR linking. |
| Consumer installs? | Projects optional; markdown remains default until proven. |
| Offline / no `gh`? | Agents must degrade gracefully to local trackers. |
| Which repo’s code when card has no Repository field? | Need convention: project item → linked repo path. |

---

## 9. Key links

- Board: https://github.com/users/SavinRazvan/projects/3  
- Experiment repo: https://github.com/SavinRazvan/mas-workflow-kit-project-ssot  
- Production kit: https://github.com/SavinRazvan/mas-workflow-kit  
- Release: https://github.com/SavinRazvan/mas-workflow-kit/releases/tag/v0.4.0  
- Kit docs (after mirror): `.ai_infra/docs/operations/connect-external-mcp.md`, `consumer-quickstart.md`, ADR-004 (MCP), ADR-006 (agent integration)

---

## 10. Handoff checklist for receiving agent

- [ ] Read this `HANDOFF.md` entirely  
- [ ] Confirm `gh` has `project` scope  
- [ ] Open board URL; see or recreate explorer items  
- [ ] Mirror / merge production kit into this repo if tree is still scaffold-only  
- [ ] Agree with human: next spike = settings + `project-board` agent (no production port)  
- [ ] Update this file’s “Last agent / Last updated” when you finish a slice  

**Last agent (writer):** Composer (Cursor) · **Last updated:** 2026-07-17  
**Next agent:** whoever opens this workspace — start at §7.
