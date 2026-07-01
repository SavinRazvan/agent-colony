---
name: implementation-execution-loop
description: Disciplined implementation slices with tracker updates and handoff.
---

# Implementation execution loop

## When

New or continued `feature/` | `fix/` | `chore/` work; recovery from blocked slices.

## Inputs

- `.local/index-and-planning/current/plan.md` (**Implementer slice closure**)
- `.local/index-and-planning/current/work-tracker.md`
- Optional: project planning docs when the slice tracks product goals
- Project `docs/architecture/` (stub under `.local/.../current/` if present)
- Test trackers when tests change: `test-plan.md`, `test-index.md`
- Closure detail: `.ai_infra/docs/operations/workflow-complete.md` §F
- Boundaries: project overlay rules in `overlays/rules/*.mdc` when installed; universal rules in `.cursor/rules/`.

## Steps

1. Read plan + tracker; one task `in_progress`.
2. Document acceptance + rollback in `plan.md` if missing.
3. Implement: contracts → code → tests. **New Python/sources:** module header per `.cursor/rules/file-docstring-header-relations.mdc` (`File:`, `Path:`, `Role:`, `Used By:`, `Depends On:`).
4. **Gates:** run commands in `.ai_infra/scripts/pr/prepare.py` `GATES` (plus `python .ai_infra/scripts/architecture/check_governance_consistency.py` when governance/workflows/policy docs change). Prefer scoped `pytest` only with a short reason.
5. **Commits:** trailers per `.cursor/rules/commit-trailer-format.mdc` (`Author`, `GitHub-User`; add `Assisted-by:` when applicable; no `Made-with:`). Human remains accountable; no automated human certification lines.
6. **Close:** `work-tracker.md`, `history/updates-log.md` (no long gate dumps — `.ai_infra/docs/operations/agent-workflow-procedures.md`), test/coverage trackers and `pages.json` when paths changed; do not touch `module-audit.html` unless regenerating an audit export. Run **`make drift-validate`**; invoke **`workflow-drift-guard`** when P0/P1 findings need artifacts.

## Output

Slice • modules/files • gates outcome • trackers updated • blockers • next step
