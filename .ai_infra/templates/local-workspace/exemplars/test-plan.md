<!--
File: test-plan.md
Path: .local/index-and-planning/current/test-plan.md
Role: Living modular testing plan.
Used By:
 - test-runner agent
 - .cursor/skills/test-module-coverage/SKILL.md
Depends On:
 - .local/index-and-planning/current/test-index.md
Notes:
 - Synchronize with module changes and risk posture.
-->

# Testing Plan

## Objective

- Keep tests modular, high-signal, and aligned with source boundaries.
- Track coverage gaps and obsolete-test cleanup continuously.

## Coverage policy

- Default gate: `pytest -q` (via `scripts/pr/prepare.py` `GATES`)
- Module-level first: `pytest -q tests/modules/<module>` when applicable
- Coverage runs when changes are medium/high-risk:
  - `pytest --cov=<package> --cov-report=term-missing -q`
- Refresh `coverage-index.md` after meaningful coverage runs (project-specific script or manual)

## Active priorities

- [ ] Keep `test-index.md` current when tests move or modules rename
- [ ] High-risk flows: retry/timeout/replay where state-changing

## Cleanup rule

If a module is removed/renamed, update/remove tests in the same slice; note in `updates-log.md`.

## Evidence per slice

- Test scope executed
- Coverage deltas (when run)
- Remaining gaps and next actions
