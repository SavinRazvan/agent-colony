# Project board views setup

Human paste guide for GitHub Project settings UI (ADR-008). There is **no official API** to create/rename views or set column visibility. Agents **coach** by default; **browser MCP** only when the human explicitly asks (see **Browser assist map**). Opt-in CLI: `--ensure-fields` / `--apply-readme` only.

**CLI asymmetry:** `board-bootstrap --check` **reads** view/column metadata via GraphQL and **detects** gaps; it **cannot fix** views or column visibility — only `--ensure-fields` / `--apply-readme` mutate field defs / README.

**Desired state (kit default):** `.ai_infra/templates/project-board/board-shell.schema.yaml` — **full Playground parity**, not a bare “two views” board.  
Optional overlay: `.local/user_settings/board-shell.schema.yaml`.  
First-run coach: `/project-board` + `.cursor/skills/board-shell/SKILL.md`.

**Product rule:** apply this **default shell** so the board matches Playground (Status board, Prioritized backlog, Roadmap, Bugs, In review, My items) with Tier-1 columns. Customize cosmetics later. Verify with:

```bash
python3 -m cursor_workflow project board-bootstrap --check
```

---

## 0. What “default” means

| Tier | What | When |
|------|------|------|
| **Default minimum (required)** | **Six Playground views** (kit default schema) **or two views** with minimal overlay — plus Tier-1 columns on Status board and Prioritized backlog + Project README | Right after activate + `project doctor` |
| **Customize later** | Iteration / End date / Labels / Reviewers columns, Insights, extra filters | Anytime after bootstrap is clean |

GitHub may create a blank Project with names like `View 1`. That is **not** the kit default — rename/create until the board matches the table below.

### Minimal 2-view overlay (optional)

Use this when you want a **lean board** matching kit-dev [AI Project Playground #3](https://github.com/users/SavinRazvan/projects/3): **Prioritized backlog** + **Status board** only. Agent CLI/API behavior is unchanged — views are human UI only.

1. Copy the exemplar:

```bash
cp .ai_infra/templates/user-settings/exemplars/board-shell.schema.minimal.yaml \
   .local/user_settings/board-shell.schema.yaml
```

2. In GitHub UI, mirror Playground #3:

| View | Layout |
|------|--------|
| **Prioritized backlog** | Table |
| **Status board** | Board · group by **Status** |

3. On **both** views: show **Priority**, **Size**, **Estimate**, **Start date** (Tier-1 contract unchanged).
4. Paste README (`project-readme.md` or `--apply-readme`).
5. `board-bootstrap --check` until exit **0** — schema path should show `.local/user_settings/board-shell.schema.yaml`.

Kit **default** remains six Playground views ([`board-shell.schema.yaml`](board-shell.schema.yaml)). The overlay only changes what `--check` requires.

### Fast path (GitHub UI — Playground default)

1. Open the Project in the browser.
2. Click the **View 1** tab → ⋯ / rename → **Status board** → layout **Board** → group by **Status**.
3. **+ New view** five more times (or until you have six tabs):

| New view name | Layout | Filter / group |
|---------------|--------|----------------|
| **Prioritized backlog** | Table | (none required) |
| **Roadmap** | Roadmap | — |
| **Bugs** | Table | title contains `[BUG]` |
| **In review** | Table | Status = In review |
| **My items** | Table | Assignees = `@me` |

4. On **Status board** and **Prioritized backlog**: **+** → show **Priority**, **Size**, **Estimate**, **Start date**.
5. README: `--apply-readme` or paste `project-readme.md`.
6. `python3 -m cursor_workflow project board-bootstrap --check` until green.

Agents coach this as **TURN PROTOCOL** in `board-shell` (one view per chat turn). **Default:** human clicks. **If the user asks** for browser help, agents may use browser MCP and follow **Browser assist map** below.

---

## Browser assist map (opt-in — universal sections)

No consumer-specific URLs. Open the Project from `project status`. Use when the human asks the agent to drive the browser (or as a click cheat-sheet).

| Goal | UI section | Target |
|------|------------|--------|
| Active view | Top **view tabs** | Exact kit name (`Status board`, `Prioritized backlog`, …) |
| Rename | Tab **⋯** / View menu → **Rename** | Kit view name |
| New view | **+ New view** | Layout + name from turn |
| Layout | View menu → **Layout** | Board / Table / Roadmap |
| Group by | View menu / toolbar **Group by** | **Status** on Status board; optional **Priority** on Prioritized backlog (polish only) |
| Tier-1 columns | **+** / **Fields** / View settings → Fields | Priority, Size, Estimate, Start date |
| Undo bad Slice | View menu → **Slice by** → clear | Groups without slice chips |
| Persist | **Save** on view if shown | Survives reload |
| README | Settings → README **or** `--apply-readme` | Non-empty README |

**Minimal fast path:** Status board (Board + Group by Status + Tier-1) → Prioritized backlog (Table + Tier-1) → README → re-check. **Group by Priority** on the backlog is optional and **not** required for `--check` exit 0.

Verify after each change: `python3 -m cursor_workflow project board-bootstrap --check`.

---

## 1. Default views (Playground)

Create or rename until you have these six:

| View name | Layout | Purpose |
|-----------|--------|---------|
| **Status board** | Board, group by **Status** | Kanban by Status |
| **Prioritized backlog** | Table | Working backlog (must show **Priority**) |
| **Roadmap** | Roadmap | Timeline / Status overview |
| **Bugs** | Table | **Filter required:** title contains `[BUG]` (or only bug-template cards) |
| **In review** | Table | Filter: Status = In review |
| **My items** | Table | Filter: Assignees = `@me` |

Emoji suffixes (e.g. `Bugs 🐛`) are fine — `board-bootstrap --check` matches on the name stem.

---

## 2. Tier-1 columns (required on Status board + Prioritized backlog)

These are the columns agents and humans need for Pattern A. **Prioritized backlog without Priority is incomplete.**

| Column | Status board | Prioritized backlog | Notes |
|--------|:------------:|:-------------------:|-------|
| Title | yes | yes | Usually present |
| Assignees | yes | yes | Human owner |
| Status | yes (group) | yes | Kit Status options |
| **Priority** | **yes** | **yes** | p0 / p1 / p2 — **do not omit** |
| **Size** | **yes** | **yes** | xs–xl |
| **Estimate** | **yes** | **yes** | Points (not hours) |
| **Start date** | **yes** | **yes** | Set on first In progress |
| Linked pull requests | yes | yes | Via Issue↔PR / `mention-pr` |

**Optional / cosmetic (not required for bootstrap Tier-1 check):** Iteration, End date, Labels, Reviewers, Repository, Sub-issues.

### How to add a missing column (GitHub UI)

1. Open the view (e.g. **Prioritized backlog**).
2. **+** / field picker → show **Priority** (and Size, Estimate, Start date if missing).
3. Drag columns into a sensible order: Title → Assignees → Status → Priority → Size → Estimate → Start date → Linked pull requests.
4. Re-run `board-bootstrap --check` until exit **0** (no view FAIL and no Tier-1 column FAILs; leftover `View N` WARNs are OK).

Other views (Roadmap, Bugs, In review, My items) should show Status / Priority / Size where useful; bootstrap enforces Tier-1 column checks on the two primary board/table shells.

---

## 3. Project README

1. Open Project settings → **README**.
2. Paste the **contents** of `.ai_infra/templates/project-board/project-readme.md`.
3. Edit the HTML comment placeholders (`PROJECT_TITLE`, `DEFAULT_REPO`, links) for your repo.
4. Do **not** paste `views-setup.md` into the README — only **follow** this file in the UI.  
   Or opt-in: `python3 -m cursor_workflow project board-bootstrap --check --apply-readme`.

---

## 4. Verify

```bash
python3 -m cursor_workflow project board-bootstrap --check
```

| Outcome | Meaning |
|---------|---------|
| **FAIL (exit 5)** | Missing a **default** view, empty README, or missing Tier-1 **columns** on Status board / Prioritized backlog |
| **WARN (exit 0)** | Leftover `View N` names; layout mismatch; recommended view missing — fix before relying on agents |
| **ok (exit 0)** | Default shell ready → `project status` → `/implementer` |

Then: `python3 -m cursor_workflow project status`.

---

## 5. Keep views API-free (browser opt-in)

Agents write card fields and Notes via `cursor_workflow project`. They do not use undocumented GraphQL for views. Default shell setup is human UI + coach; **if asked**, browser MCP follows the **Browser assist map**. Opt-in CLI: `--apply-readme` / `--ensure-fields`.
