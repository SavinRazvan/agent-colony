# Project board views setup

Human-only paste guide for GitHub Project settings UI (ADR-008). Agents never mutate views, workflows, Insights, or README.

**Product rule:** apply the **minimum** shell first so the board looks like a product (not `View 1` / `View 3`). Customize later. Verify with:

```bash
python3 -m cursor_workflow project board-bootstrap --check
```

---

## 0. Standard vs customize

| Tier | What | When |
|------|------|------|
| **Minimum (required)** | Rename the two default views, add Tier-1 columns, paste Project README | Right after activate + `project doctor` |
| **Recommended (Playground parity)** | Add Roadmap, Bugs, In review, My items | After minimum passes bootstrap |
| **Customize later** | Rename, delete unused views, add Insights / filters | Anytime after minimum is clean |

---

## 1. Minimum (required)

### 1a. Rename default views

- `View 1` → **Status board** (Board layout, group by Status)
- `View 3` (or the default table) → **Prioritized backlog** (Table layout)

### 1b. Visible columns (both minimum views)

Add these fields if missing:

- Priority
- Size
- Estimate
- Start date

Keep Title, Assignees, Status, Linked pull requests.

### 1c. Project README

1. Open Project settings → **README**.
2. Paste the **contents** of `.ai_infra/templates/project-board/project-readme.md`.
3. Edit the HTML comment placeholders (`PROJECT_TITLE`, `DEFAULT_REPO`, links) for your repo.
4. Do **not** paste `views-setup.md` into the README — only **follow** this file in the UI.

---

## 2. Recommended (Playground parity)

Create additional views (New view) after minimum is done:

| View name | Layout | Suggested filter / purpose |
|-----------|--------|----------------------------|
| **Roadmap** | Board or table | Status + Priority overview (optional Iteration later — human) |
| **Bugs** | Table or board | Title contains `[BUG]` / bug template work |
| **In review** | Board or table | Status = In review |
| **My items** | Table | Assignees = `@me` |

Column set: same Tier-1 fields as minimum where useful.

---

## 3. Verify

```bash
python3 -m cursor_workflow project board-bootstrap --check
```

- Empty README → fails until you paste `project-readme.md`.
- Names still matching `View 1` / `View N` → WARN (finish §1a).
- Missing Priority/Size/Estimate/Start date on board/table views → WARN (finish §1b).

Then: `python3 -m cursor_workflow project status`.

---

## 4. Keep the board human-owned

Agents write card fields and Notes via `cursor_workflow project` only. They do not configure views, workflows, Insights, or README.
