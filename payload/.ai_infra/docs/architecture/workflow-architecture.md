<!--
File: workflow-architecture.md
Path: .ai_infra/docs/architecture/workflow-architecture.md
Role: Canonical consumer-facing architecture overview (three planes, agents, Pattern A gates).
Used By:
 - README.md
 - Onboarding
Depends On:
 - .ai_infra/docs/decisions/README.md
Notes:
 - Consumer-facing; maintainer deep-dive: `.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md` (kit-dev only).
-->

# Workflow architecture (MAS Workflow Kit)

## Three planes

| Plane | Path | Purpose |
|-------|------|---------|
| Cursor contract | `.cursor/`, `.agents/` | Agents, skills, rules |
| Infrastructure | `.ai_infra/` | Scripts, docs, templates, MCP |
| Runtime | `.local/` | Trackers, PR artifacts, audits (see [Artifact tiers](../operations/local-workspace-layout.md#artifact-tiers)) |

**Install** scaffolds Tier 1 base paths (trackers, `workflow-artifacts/*` buckets, README stubs). Agents and PR scripts write Tier 2 runtime content during work. Path SSOT: `.ai_infra/scripts/pr/local_workflow_paths.py`.

## Activation

Enabling the **plugin** loads agents/skills/rules in the IDE only — it does **not** write files to your project. Run activate to install all three planes on disk:

1. **Plugin from GitHub (recommended):** Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` → open your app → **`/workflow-activate`** (or `python -m cursor_workflow activate --directory .`)
2. **Marketplace (when listed):** same flow after **Cursor → Marketplace** install
3. **Kit clone / advanced:** `python -m cursor_workflow install --target . --verify`

See [PLUGIN-USER-GUIDE.md](../operations/PLUGIN-USER-GUIDE.md) §1 for the plugin-vs-disk diagram and file tree.

## Pattern A (maintainer PR)

Hub: `.agents/skills/pr-workflow/SKILL.md` → `review-pr` → `prepare-pr` (`prepare.py` GATES) → `merge-pr` → `finalize.py`

Gate order: read `.ai_infra/scripts/pr/prepare.py` only — do not duplicate here.

## Anchoring

**When `project_ssot.enabled`** (see `github.collaboration.yaml`, [ADR-008](../decisions/ADR-008-project-board-ssot.md)): session backlog/status is the **GitHub Project** via `python -m cursor_workflow project …` and `.cursor/skills/project-board-ssot/SKILL.md`. Local `session-pointer.md` / `plan.md` / `work-tracker.md` are **offline fallback only** under `sync_policy: board_only` (no dual-write; DRIFT-009).

**Otherwise:** every session → `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`.

## Core agents (kit)

| Agent | Role |
|-------|------|
| `implementer` | Slices, code; board Status when `project_ssot.enabled` |
| `test-runner` | Module tests, coverage; board Exit Status |
| `verifier` | Evidence checks; board Done / In review |
| `enterprise-auditor` | Architecture audits; audit card Status + Notes |
| `researcher` | Adaptive Brief multi-round packs under `_research_results/`; chat/agent/card intake; research card Done + `AGENT_BRIEF` paths |
| `integrator-mas-agent` | Add agents/skills/MCP; integration card Status |
| `workflow-drift-guard` | Drift + DRIFT-009; **reads board**, closes drift card |
| `project-board` | Board triage helper (ADR-006); not in default PR pipelines |

Continuation: every agent Entry reads the Project; Exit updates Status/Notes — [project-board-collaboration.md](../operations/project-board-collaboration.md).

Integration procedure: [mas-infrastructure-integration.md](../operations/mas-infrastructure-integration.md).  
Drift validation: `make drift-validate` — see [gate-matrix.md](../operations/gate-matrix.md).

## Skills layout

| Root | Contents |
|------|----------|
| `.cursor/skills/` | Canonical protocols: `enterprise-architecture-audit`, `workflow-drift-audit`, `implementation-execution-loop`, `workflow-activate`, … |
| `.agents/skills/` | Maintainer slash skills: `review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `audit-alignment` (redirect) |

Plugin bundle copies `.cursor/skills/` first; maintainer skills are **additive only** (no overwrite).

See [folder-charter.md](../governance/folder-charter.md) and [decisions/README.md](../decisions/README.md).
