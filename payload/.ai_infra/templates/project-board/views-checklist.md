# Project board views checklist

## Minimum (required)

- [ ] Rename `View 1` → **Status board**
- [ ] Rename `View 3` (or default table) → **Prioritized backlog**
- [ ] Add **Priority**, **Size**, **Estimate**, and **Start date** to Status board and Prioritized backlog
- [ ] Paste **contents** of `project-readme.md` into Project README (edit placeholders)
- [ ] Run `python3 -m cursor_workflow project board-bootstrap --check` (no empty-README fail; View N WARNs gone)

## Recommended (Playground parity — customize later OK)

- [ ] Add **Roadmap** view
- [ ] Add **Bugs** view with filter: title contains `[BUG]` (view must not list non-bug cards)
- [ ] Add **In review** view (Status = In review)
- [ ] Add **My items** view (Assignees = `@me`)

## Policy

- [ ] Confirm agents still do not mutate views, workflows, Insights, or README (ADR-008)
