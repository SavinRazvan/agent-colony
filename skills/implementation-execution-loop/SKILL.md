---
name: implementation-execution-loop
description: Disciplined implementation slices with tracker updates and handoff.
---

# Implementation execution loop

## When

New or continued `feature/` | `fix/` | `chore/` work; recovery from blocked slices.

## Inputs

- **When `project_ssot.enabled`:** `.local/user_settings/github.collaboration.yaml` + `.cursor/skills/project-board-ssot/SKILL.md` + board card (Acceptance/Rollback in body)
- **Fallback:** `.local/index-and-planning/current/plan.md`, `work-tracker.md`, `session-pointer.md`
- Project `docs/architecture/` (stub under `.local/.../current/` if present)
- Test trackers when tests change: `test-plan.md`, `test-index.md`
- Closure detail: `.ai_infra/docs/operations/workflow-complete.md` §F
- Boundaries: `overlays/rules/*.mdc` when installed; universal rules in `.cursor/rules/`; ADR-008

## Steps

1. **SSOT select:** `python -m cursor_workflow project status`. If operational → list/claim board card (`set-status --to in_progress`). Else read plan + tracker; one task `in_progress` locally.
2. Document acceptance + rollback on **card body** (or `plan.md` if fallback).
3. Implement: contracts → code → tests. **New Python/sources:** module header per `.cursor/rules/file-docstring-header-relations.mdc`.
4. **Gates:** run commands in `.ai_infra/scripts/pr/prepare.py` `GATES` (plus `check_governance_consistency.py` when governance changes). Prefer scoped `pytest` with a short reason.
5. **Commits:** trailers per `.cursor/rules/commit-trailer-format.mdc` (`Author`, `GitHub-User`; `Assisted-by:` when applicable; no `Made-with:`).
6. **Close:** board `set-status --to in_review|done` when SSOT enabled; do **not** dual-write `work-tracker.md` under `board_only`. Fallback: close tracker + `updates-log.md`. Run **`make drift-validate`**; invoke **`workflow-drift-guard`** when P0/P1 findings need artifacts.

## Output

Slice • item_id (if board) • modules/files • gates outcome • blockers • next step
