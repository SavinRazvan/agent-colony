<!--
File: test-index.md
Path: .local/index-and-planning/current/test-index.md
Role: Module-to-test ownership index (required by check_testing_artifacts.py).
Used By:
 - test-runner agent
 - scripts/pr/check_testing_artifacts.py
Depends On:
 - tests/ tree (project-specific)
Notes:
 - Update when tests are added, moved, renamed, or removed.
-->

# Test Index

## Format

- Module: `<source module or area>`
- Owned tests: `<tests/... paths>`
- Coverage status: `healthy | partial | gap`
- Notes: cleanup tasks, migration notes

## Current index (MAS Workflow Kit — exemplar)

- Module: `pr_workflow`
  - Owned tests: `tests/modules/pr_workflow/` (Phase 2 — not yet created)
  - Coverage status: `gap`
  - Notes: minimal tests for `scripts/pr/*` helpers planned in STARTER-003

- Module: `architecture_scripts`
  - Owned tests: `tests/modules/architecture_scripts/` (Phase 2)
  - Coverage status: `gap`
  - Notes: `check_governance_consistency.py` smoke tests when CI paths optional

## Template row (copy per module)

- Module: `<name>`
  - Owned tests: `tests/modules/<name>/`
  - Coverage status: `healthy`
  - Notes:
