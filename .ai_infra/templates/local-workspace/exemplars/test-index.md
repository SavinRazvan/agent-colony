<!--
File: test-index.md
Path: .ai_infra/templates/local-workspace/exemplars/test-index.md
Role: Exemplar for install → .local/index-and-planning/current/test-index.md
Used By:
 - test-runner agent
 - scripts/pr/check_testing_artifacts.py
Depends On:
 - tests/ tree (project-specific)
Notes:
 - Update when tests are added, moved, renamed, or removed.
 - Neutral consumer template; maintainer test inventory is seeded in the kit repo CI only.
-->

# Test Index

## Format

- Module: `<source module or area>`
- Owned tests: `<tests/... paths>`
- Coverage status: `healthy | partial | gap`
- Notes: cleanup tasks, migration notes

## Current index

- Module: `_project_`
  - Owned tests: `tests/modules/smoke/`
  - Coverage status: `gap`
  - Notes: rename module; add paths as you add product tests

## Template row (copy per module)

- Module: `<name>`
  - Owned tests: `tests/modules/<name>/`
  - Coverage status: `healthy`
  - Notes:
