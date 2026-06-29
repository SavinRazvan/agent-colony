<!--
File: plan.md
Path: .local/index-and-planning/current/plan.md
Role: Living implementation plan for the active slice and next slices.
Used By:
 - implementer agent
 - agents-control-center UI
Depends On:
 - .local/index-and-planning/current/work-tracker.md
Notes:
 - Keep concise; update before changing execution scope.
-->

# Implementation Plan

## Mission

- Deliver incremental, reversible slices with clear acceptance criteria.
- Track architecture, work progress, and governance in `.local/` trackers.

## Current focus

- **STARTER-001** (sole `in_progress`) — Phase 1: universal core extraction (see `work-tracker.md`).
- Align kit with [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](../../../.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md).

## Active slice

### Scope

Refactor staging into installable **MAS Workflow Kit**: README, overlays, 2-gate `prepare.py`, decontaminated agents, `.local/` exemplars.

### Acceptance criteria

- [ ] Six universal rules in `.cursor/rules/`; product rules in `overlays/rules/`
- [ ] `prepare.py` `GATES` = 2 universal defaults
- [ ] Generic `AGENTS.md` and agent prompts (no product first-reads in core)
- [ ] `.local/` structure kept; runtime noise removed per [local-anchoring-patterns.md](../../../.ai_infra/docs/maintainer/local-anchoring-patterns.md)

### Implementer slice closure

Before handoff: update `work-tracker.md`, `history/updates-log.md`, and test trackers if tests changed.

## Next queued

- Phase 2: skill dedupe, minimal `tests/`, governance CI path optional
- Phase 3: consumer overlay validation
- Phase 4: MCP server wrapping PR scripts
