<!--
File: workflow-architecture.md
Path: .ai_infra/docs/architecture/workflow-architecture.md
Role: Consumer-facing architecture overview (stub; expanded in REFACTOR Phase 4).
Used By:
 - README.md
 - Onboarding
Depends On:
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
 - .ai_infra/docs/decisions/README.md
-->

# Workflow architecture (MAS Workflow Kit)

## Three planes

| Plane | Path | Purpose |
|-------|------|---------|
| Cursor contract | `.cursor/`, `.agents/` | Agents, skills, rules |
| Infrastructure | `.ai_infra/` | Scripts, docs, templates, MCP |
| Runtime | `.local/` | Trackers, PR artifacts, audits |

## Activation

1. **CLI:** `python -m cursor_workflow install --target . --verify`
2. **Marketplace (ADR-001):** Enable plugin → run `workflow-activate` skill → verify gates

## Pattern A (maintainer PR)

`review-pr` → `prepare-pr` (`prepare.py` GATES) → `merge-pr` → `finalize.py`

Gate order: read `.ai_infra/scripts/pr/prepare.py` only — do not duplicate here.

## Anchoring

Every session: `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`.

## Core agents (kit)

| Agent | Role |
|-------|------|
| `implementer` | Slices, code, trackers |
| `test-runner` | Module tests, coverage |
| `verifier` | Evidence checks |
| `enterprise-auditor` | Architecture audits |
| `researcher` | Research corpus (local) |
| `integrator-mas-agent` | Add agents/skills/MCP to infrastructure |

Integration procedure: [mas-infrastructure-integration.md](../operations/mas-infrastructure-integration.md).

See [folder-charter.md](../governance/folder-charter.md) and [decisions/README.md](../decisions/README.md).
