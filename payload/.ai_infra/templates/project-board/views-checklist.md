# Project board views checklist

Kit **default** = full Playground shell (not “two views only”). Schema: `board-shell.schema.yaml`.

## Default minimum (required)

### Views

- [ ] **Status board** (Board, group by Status)
- [ ] **Prioritized backlog** (Table)
- [ ] **Roadmap**
- [ ] **Bugs** (filter: title contains `[BUG]` — must not list non-bug cards)
- [ ] **In review** (filter: Status = In review)
- [ ] **My items** (filter: Assignees = `@me`)
- [ ] No leftover blank names (`View 1` / `View N`) as primary views

### Tier-1 columns on Status board **and** Prioritized backlog

- [ ] **Priority** (p0 / p1 / p2) — required on Prioritized backlog
- [ ] **Size** (xs–xl)
- [ ] **Estimate** (points)
- [ ] **Start date**
- [ ] Title, Assignees, Status, Linked pull requests present

### README + verify

- [ ] Paste **contents** of `project-readme.md` into Project README (edit placeholders)
- [ ] `python3 -m cursor_workflow project board-bootstrap --check` — no FAIL; no Priority/Size/Estimate/Start date WARNs
- [ ] WARN vs FAIL: missing **default** view = FAIL; missing Tier-1 column = WARN (still fix before “ready”)

## Customize later (optional)

- [ ] Iteration / End date / Labels / Reviewers columns (cosmetic)
- [ ] Insights / extra filters

## Policy

- [ ] Confirm agents still do not mutate views, workflows, Insights, or README (ADR-008) except opt-in `--apply-readme` / `--ensure-fields`
