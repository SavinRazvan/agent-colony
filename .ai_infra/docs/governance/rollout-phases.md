<!--
File: rollout-phases.md
Path: .ai_infra/docs/governance/rollout-phases.md
Role: REFACTOR phase history for the MAS Workflow Kit.
Used By:
 - .ai_infra/docs/governance/README.md
Depends On:
 - .local/index-and-planning/current/plan.md
Notes:
 - Phases 0–6 shipped; Phase 7 ongoing hygiene. Maintainer detail: kit repo IMPLEMENTATION-STATUS.md.
-->

# REFACTOR rollout phases (MAS Workflow Kit)

> **Historical program record.** Phases 0–6 are **complete** (plugin bundle, activate CLI, three-plane install). Ongoing work is Phase 7 hygiene — see `.local/index-and-planning/current/plan.md` on the kit repo.

| Phase | Focus | Status |
|-------|-------|--------|
| 0 | Architecture truth, ADRs, doc decontamination | **complete** |
| 1 | Path resolver, MCP fix, drift scanner | **complete** |
| 2 | Install contract, manifest docs extension | **complete** |
| 3 | Agent/rules/skills prose alignment | **complete** |
| 4 | README, workflow-architecture.md, maintainer megadocs | **complete** |
| 5 | Kit MCP + user MCP registry | **complete** |
| 6 | Cursor Marketplace plugin bundle + `cursor_workflow activate` | **complete** |
| 7 | CI, health CLI, doc automation, marketplace prep | **in progress** |

**Consumer onboarding:** use [PLUGIN-USER-GUIDE.md](../operations/PLUGIN-USER-GUIDE.md) — not this phase table.

**Historical layout migrations:** see [local-anchoring-patterns.md](../maintainer/local-anchoring-patterns.md) (kit maintainer only).
