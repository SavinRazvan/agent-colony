<!--
File: plan.md
Path: .ai_infra/templates/local-workspace/exemplars/plan.md
Role: Exemplar for install → .local/index-and-planning/current/plan.md
Used By:
 - .ai_infra/templates/local-workspace/README.md
Depends On:
 - work-tracker.md exemplar
Notes:
 - Neutral consumer stub; maintainer CI fixtures are not copied to consumer installs.
-->

# Implementation Plan

## Current focus

- **SLICE-ID** — describe the active slice (see `work-tracker.md`)

## Policy

PR-first workflow; update trackers before changing execution scope.

## Active slice

### Scope

(brief scope statement)

### Acceptance criteria

- [ ] criterion 1
- [ ] criterion 2

### Implementer slice closure

Before handoff: update `work-tracker.md`, `history/updates-log.md`, test trackers if tests changed, and run `make drift-validate` when the kit provides it.

## Next queued

- (optional follow-on slices)
