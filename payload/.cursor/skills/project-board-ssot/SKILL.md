---
name: project-board-ssot
description: Drive GitHub Project SSOT via project_ssot YAML and cursor_workflow project CLI.
---

<!--
File: SKILL.md
Path: .cursor/skills/project-board-ssot/SKILL.md
Role: Procedural skill for board-first backlog/status using project_ssot settings.
Used By:
 - .cursor/agents/project-board.md
 - implementer and other agents when project_ssot.enabled
Depends On:
 - .local/user_settings/github.collaboration.yaml (project_ssot)
 - .ai_infra/install/cursor_workflow/project_cli.py
 - ADR-008-project-board-ssot.md
Notes:
 - Pattern A: one CLI command per action; no dual-write of work-tracker when board_only.
-->

# Project board SSOT

## Goal

Use the GitHub Project configured in **`project_ssot`** (`.local/user_settings/github.collaboration.yaml`) as backlog/status SSOT. Prefer CLI over inventing `gh` flags.

**Agent:** `.cursor/agents/project-board.md`  
**ADR:** `.ai_infra/docs/decisions/ADR-008-project-board-ssot.md`

## When to use

- Triage Ready / P0–P1 work from the shared board
- Create DraftIssue cards with Acceptance / Rollback / Notes
- Move Status (Ready → In progress → In review → Done)
- Set Priority or Size from YAML option ids

## Evidence contract

- Cite CLI output or `gh project` JSON for claims.
- Label **Unknown** when board unreachable.

## Procedure

1. **Status:** `python -m cursor_workflow project status --directory .`
   - Exit 2 / disabled → use local trackers only (`fallback: local_trackers`); do not invent board ids.
2. **List queue:** `python -m cursor_workflow project list --status ready --directory .`
3. **Claim:** `python -m cursor_workflow project set-status --id PVTI_… --to in_progress --directory .`
   - Respect `conventions.one_in_progress_per_assignee` (do not steal others' In progress).
4. **Create:** `python -m cursor_workflow project create --title "…" [--body "…"] --directory .`
5. **Priority/Size:** `python -m cursor_workflow project set-field --id PVTI_… --field priority --to p1 --directory .`
6. **Close:** `python -m cursor_workflow project set-status --id PVTI_… --to done --directory .` (or `in_review` when PR open)
7. **Verify:** re-run `project list` or `gh project item-list` — Status matches intent.

## Dual-write ban

When `sync_policy: board_only`, do **not** also mark the same slice `in_progress` in `work-tracker.md` as competing SSOT. PR artifacts / audits stay local (`local_only`).

## Exit criteria

- [ ] `project status` shows `operational: True` (or explicit fallback)
- [ ] Status change confirmed on the board
- [ ] No dual-write of tracker SSOT

## Anti-patterns

- Hardcoding field/option ids instead of reading YAML
- Bypassing `prepare.py` gates
- Adding this flow to production `mas-workflow-kit` without port gate
