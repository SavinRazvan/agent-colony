# Project board views setup

Human-only paste guide for GitHub Project settings UI (ADR-008). Agents never mutate views, workflows, Insights, or README via undocumented APIs.

**CLI asymmetry:** `board-bootstrap --check` **reads** view/column metadata via GraphQL and **detects** gaps; it **cannot fix** views or column visibility — only `--ensure-fields` / `--apply-readme` mutate field defs / README.

**Desired state (kit default):** `.ai_infra/templates/project-board/board-shell.schema.yaml` — **full Playground parity**, not a bare “two views” board.  
Optional overlay: `.local/user_settings/board-shell.schema.yaml`.  
First-run coach: `/project-board` + `.cursor/skills/board-shell-onboard/SKILL.md`.

**Product rule:** apply this **default shell** so the board matches Playground (Status board, Prioritized backlog, Roadmap, Bugs, In review, My items) with Tier-1 columns. Customize cosmetics later. Verify with:

```bash
python3 -m cursor_workflow project board-bootstrap --check
```

---

## 0. What “default” means

| Tier | What | When |
|------|------|------|
| **Default minimum (required)** | All six Playground views + Tier-1 columns on Status board and Prioritized backlog + Project README | Right after activate + `project doctor` |
| **Customize later** | Iteration / End date / Labels / Reviewers columns, Insights, extra filters | Anytime after bootstrap is clean |

GitHub may create a blank Project with names like `View 1`. That is **not** the kit default — rename/create until the board matches the table below.

### Fast path (GitHub UI — do this now)

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

Agents coach this as **TURN PROTOCOL** in `board-shell-onboard` (one view per chat turn). They cannot click for you.

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
4. Re-run `board-bootstrap --check` until those WARNs are gone.

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
| **FAIL** | Missing a **default** view name, or empty README |
| **WARN** | Missing Tier-1 columns (e.g. Prioritized backlog without **Priority**); leftover `View N` names |
| **ok** + no column WARNs | Default shell ready → `project status` → day-to-day agents |

Then: `python3 -m cursor_workflow project status`.

---

## 5. Keep the board human-owned

Agents write card fields and Notes via `cursor_workflow project` only. They do not configure views, workflows, Insights, or README (except opt-in `--apply-readme` / `--ensure-fields`).
