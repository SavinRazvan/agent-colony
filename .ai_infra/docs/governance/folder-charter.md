<!--
File: folder-charter.md
Path: .ai_infra/docs/governance/folder-charter.md
Role: Charter for three-plane layout (Cursor contract, infrastructure, runtime) vs kit-dev-only paths.
Used By:
 - .ai_infra/docs/governance/README.md
 - Onboarding, maintainers, agent orientation
Depends On:
 - .ai_infra/docs/operations/local-workspace-layout.md
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
Notes:
 - `.local/` is gitignored; this file is the versioned contract for what belongs where.
 - Last reviewed: 2026-06-14
-->

# Folder charter: three planes + kit dev

## Planes (consumer project)

| Plane | Path | Git? | Purpose |
|-------|------|------|---------|
| Cursor contract | `.cursor/`, `.agents/` | Yes | Agents, skills, rules, MCP wiring |
| Infrastructure | `.ai_infra/` | Yes (slim subset) | Scripts, docs, templates, kit MCP |
| Runtime | `.local/` | No (gitignored) | Trackers, PR artifacts, audits, generated data |
| Overlay | `overlays/rules/` | Yes | Per-project rules merged at install |

## `.ai_infra/` subtrees (consumer copy via manifest)

| Subtree | Purpose |
|---------|---------|
| `docs/operations/` | Runbooks, quickstart, local-workspace layout |
| `docs/governance/` | Charters, drift prevention, module boundaries |
| `docs/roadmap/` | Alignment audit schema |
| `docs/architecture/` | Consumer architecture (`workflow-architecture.md`) |
| `docs/decisions/` | ADR index and decision records |
| `.ai_infra/scripts/pr/` | PR workflow scripts (`prepare.py` GATES) |
| `scripts/architecture/` | Governance and layer checks |
| `templates/local-workspace/` | Stubs copied into `.local/` at scaffold |
| `templates/user-settings/` | Exemplars → `.local/user_settings/` |
| `templates/agent-integration/` | Agent/skill templates for integrator |
| `workflows/` | Workflow definitions referenced by agents |
| `mcp_servers/workflow_mcp/` | Optional kit MCP server (`with_mcp` profile) |

**Kit dev only (not copied to consumer by default):**

| Path | Purpose |
|------|---------|
| `tests/` | Kit test suite |
| `.ai_infra/docs/handoff/` | Maintainer implementation status |
| `.ai_infra/docs/maintainer/` | Heavy megadocs, migration references |
| Root maintainer docs | Kit dev reference until relocated |

## `.local/` (local operating workspace)

| Subtree | Purpose |
|---------|---------|
| `index-and-planning/current/` | Live trackers: `plan.md`, `work-tracker.md`, `test-plan.md`, `test-index.md`, `coverage-index.md`, `session-pointer.md`, `change-index.md` |
| `index-and-planning/history/` | Chronological logs (e.g. `updates-log.md`) |
| `index-and-planning/audits/` | Local governance audit snapshots |
| `agents-control-center/` | Dashboard config and optional HTML exports |
| `user_settings/` | GitHub + MCP worksheets (gitignored) |
| `workflow-artifacts/pr/` | `review.md`, `prep.md`, `merge.md` (PR phase headers) |
| `workflow-artifacts/alignment/` | `alignment-audit.md`, `alignment-todos.md` |
| `workflow-artifacts/drift/` | `drift-audit.md`, `drift-todos.md` |
| `workflow-artifacts/enterprise-architecture-audit/` | Full enterprise audit report + actions |
| `workflow-artifacts/release/` | Optional RC sign-off |
| `workflow-artifacts/audit/` | Preflight JSON from verify-all / doc validate |
| `generated-data/` | Coverage JSON and similar machine output |

Full layout: [local-workspace-layout.md](../operations/local-workspace-layout.md).

## Protected local artifacts

Per [local-artifact-protection.mdc](../../../.cursor/rules/local-artifact-protection.mdc): do not delete `.env` secrets or `.coverage` without explicit approval.

## What does not belong in consumer install

- **Tier 2 runtime content** — filled under `.local/workflow-artifacts/*` during slices (PR, alignment, drift, enterprise audit, release, audit preflight).
- Live slice trackers — **`.local/index-and-planning/current/`** (summarize in `updates-log.md`).
- Generated coverage/CI JSON — **`.local/generated-data/`**.
- Product application code — out of scope for **mas-workflow-kit**; use consumer `overlays/rules/` when needed.
