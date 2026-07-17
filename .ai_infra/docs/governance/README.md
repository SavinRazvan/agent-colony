<!--
File: README.md
Path: .ai_infra/docs/governance/README.md
Role: Index for documentation governance, IA charters, and workflow source-of-truth map.
Used By:
 - .ai_infra/docs/operations/README.md
 - Maintainer onboarding
Depends On:
 - .ai_infra/docs/governance/folder-charter.md
Notes:
 - Last reviewed: 2026-07-08
-->

# Governance documentation

**Status:** active  
**Owner:** Savin Ionuț Răzvan

This folder defines **where kit docs live**, **who owns workflow truth** (scripts vs prose), and **how to prevent drift** between rules, skills, and operations runbooks.

## Reading order

| Order | Document | When to use |
|---|---|---|
| 1 | [folder-charter.md](folder-charter.md) | Three-plane layout; what ships to consumers |
| 2 | [workflow-source-owners.md](workflow-source-owners.md) | PR gates, artifact paths, commit trailers |
| 3 | [drift-prevention.md](drift-prevention.md) | After changing gates, layout, or policy |
| 4 | [module-boundaries.md](module-boundaries.md) | Cross-plane import and responsibility rules |
| 5 | [rules-overlap-matrix.md](rules-overlap-matrix.md) | Editing `.cursor/rules/*.mdc` |

## Document index

| File | Role |
|---|---|
| [folder-charter.md](folder-charter.md) | `.ai_infra/` subtrees vs `.local/` operating workspace |
| [workflow-source-owners.md](workflow-source-owners.md) | Canonical owners: `prepare.py`, `local_workflow_paths.py`, rules, skills |
| [drift-prevention.md](drift-prevention.md) | Checklists after gate, lifecycle, or trailer changes |
| [module-boundaries.md](module-boundaries.md) | Plane boundaries and forbidden cross-plane leakage |
| [rules-overlap-matrix.md](rules-overlap-matrix.md) | Cursor rules inventory (6 universal rules) |
| [rollout-phases.md](rollout-phases.md) | REFACTOR phase history stub |

## Related (outside this folder)

| Area | Entry |
|---|---|
| Maintainer PR checklist | [workflow-complete.md](../operations/workflow-complete.md) |
| `.local/` layout contract | [local-workspace-layout.md](../operations/local-workspace-layout.md) |
| Doc maintenance | [documentation-maintenance-checklist.md](../operations/documentation-maintenance-checklist.md) |
| Alignment audit schema | [alignment-audit-schema.md](../roadmap/alignment-audit-schema.md) |
| Architecture-impacting audits | `enterprise-auditor` + [enterprise-architecture-audit/SKILL.md](../../../.cursor/skills/enterprise-architecture-audit/SKILL.md) |
| ADR index | [decisions/README.md](../decisions/README.md) |

## Quick commands

```bash
python .ai_infra/scripts/architecture/check_governance_consistency.py
python .ai_infra/scripts/pr/prepare.py --help
```
