<!--
File: local-anchoring-patterns.md
Path: .ai_infra/docs/maintainer/local-anchoring-patterns.md
Role: Short neutral guide for `.local/` structure and agent read order.
Used By:
 - install-dry-run.md
 - plan.md exemplar
 - implementer onboarding
Depends On:
 - .ai_infra/docs/operations/local-workspace-layout.md
Notes:
 - Maintainer reference; not copied to consumers by default.
-->

# Local anchoring patterns (`.local/`)

The `.local/` directory is **gitignored**. It holds live execution state — not durable workflow doctrine (that lives under `.ai_infra/docs/operations/`).

## Session entry (every agent slice)

1. `.local/index-and-planning/current/session-pointer.md` — what to read next
2. `plan.md` — active slice scope and acceptance criteria
3. `work-tracker.md` — exactly one primary `in_progress` task

## Tracker buckets

| Path | Purpose |
|------|---------|
| `index-and-planning/current/` | Live trackers: plan, work-tracker, test-plan, test-index, coverage-index, session-pointer, change-index |
| `index-and-planning/history/` | Chronological logs (`updates-log.md`) |
| `index-and-planning/audits/` | Local governance audit snapshots |
| `workflow-artifacts/pr/` | PR phase files: review.md, prep.md, merge.md |
| `workflow-artifacts/alignment/` | alignment-audit.md, alignment-todos.md |
| `agents-control-center/` | Dashboard config and optional HTML exports |
| `generated-data/` | Coverage JSON and machine output — skip unless tasked |

## Agent efficiency

**Usually read:** session-pointer, plan, work-tracker; PR artifacts when merging.

**Usually skip:** `generated-data/**`, long `history/` unless investigating regressions.

## Scaffold source

Copy exemplars from `.ai_infra/templates/local-workspace/exemplars/` into `.local/index-and-planning/current/` at install.

Full contract: [local-workspace-layout.md](../operations/local-workspace-layout.md).

## Anti-patterns

- Do not commit `.local/` paths to git
- Do not paste full gate command lists into `updates-log.md` — say *prepare gates green* or paste failing stderr only
- Do not store durable runbooks only in `.local/` — version them under `.ai_infra/docs/operations/`
