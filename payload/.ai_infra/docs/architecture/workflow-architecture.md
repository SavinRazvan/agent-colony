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

# Workflow architecture (Agent Colony)

**Use ASD-STE100:** [../operations/asd-ste100-prose.md](../operations/asd-ste100-prose.md) · [token-efficiency.md](../operations/token-efficiency.md)


## Three planes

| Plane | Path | Purpose |
|-------|------|---------|
| Cursor contract | `.cursor/`, `.agents/` | Agents, skills, rules |
| Infrastructure | `.ai_infra/` | Scripts, docs, templates, MCP |
| Runtime | `.local/` | Trackers, PR artifacts, audits (see [Artifact tiers](../operations/local-workspace-layout.md#artifact-tiers)) |

**Install** scaffolds Tier 1 base paths (trackers, `workflow-artifacts/*` buckets, README stubs). Agents and PR scripts write Tier 2 runtime content during work. Path SSOT: `.ai_infra/scripts/pr/local_workflow_paths.py`.

## Activation

Enabling the **plugin** loads agents/skills/rules in the IDE only — it does **not** write files to your project. Run activate to install all three planes on disk:

1. **Plugin from GitHub (recommended):** Agent chat → `/add-plugin https://github.com/SavinRazvan/agent-colony` → open your app → **`/workflow-activate`** (or `python -m agent_colony activate --directory .`)
2. **Marketplace (when listed):** same flow after **Cursor → Marketplace** install
3. **Kit clone / advanced:** `python -m agent_colony install --target . --verify`

See [PLUGIN-USER-GUIDE.md](../operations/PLUGIN-USER-GUIDE.md) §1 for the plugin-vs-disk diagram and file tree.

## Pattern A (maintainer PR)

Hub: `.agents/skills/pr-workflow/SKILL.md` → `review-pr` → `prepare-pr` (`prepare.py` `resolve_gates()`) → `merge-pr` (staged).
Optional cleanup: `full-pr-workflow` → `finalize.py`.

Gate order: read `.ai_infra/scripts/pr/prepare.py` only — do not duplicate here.

## Anchoring

**When `project_ssot.enabled`** (see `github.collaboration.yaml`, [ADR-008](../decisions/ADR-008-project-board-ssot.md)): session backlog/status is the **GitHub Project** via `python -m agent_colony project …` and `.cursor/skills/board-ssot/SKILL.md`. **Day-0:** `/board` + `board-shell` until `board-bootstrap --check` matches `board-shell.schema.yaml` (Playground six-view default) — before `/implementer`; audit is not day-0. Local `session-pointer.md` / `plan.md` / `work-tracker.md` are **offline fallback only** under `sync_policy: board_only` (no dual-write; DRIFT-009).

**Otherwise:** every session → `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`.

## Core agents (kit)

| Agent | Role |
|-------|------|
| `implementer` | Slices, code; board Status when `project_ssot.enabled` |
| `test-runner` | Module tests, coverage; board Exit Status |
| `verifier` | Evidence checks; board Done / In review |
| `auditor` | Architecture audits; audit card Status + Notes |
| `researcher` | **Shipped/proven** adaptive Brief multi-round packs under `_research_results/` (opt-in after init); chat/agent/card intake; research card Done + `AGENT_BRIEF` paths |
| `integrator` | Add agents/skills/MCP; integration card Status |
| `drift-guard` | Drift + DRIFT-009; **reads board**, closes drift card |
| `board` | Board triage + **first-run shell coach** (`board-shell`; ADR-006); not in default PR pipelines |

Continuation: every agent Entry reads the Project; Exit updates Status/Notes — [project-board-collaboration.md](../operations/project-board-collaboration.md).

Integration procedure: [mas-infrastructure-integration.md](../operations/mas-infrastructure-integration.md).  
Drift validation: `make drift-validate` — see [gate-matrix.md](../operations/gate-matrix.md).

## Skills layout

| Root | Contents |
|------|----------|
| `.cursor/skills/` | Canonical protocols (**14**): `workflow-activate`, `update-agent-colony`, `board-ssot`, `board-shell`, `canvas-artifacts`, `implementer-loop`, `auditor-protocol`, `drift-audit`, … — full list in [repository-map.md](../handoff/repository-map.md) |
| `.agents/skills/` | Maintainer slash skills: `review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `full-pr-workflow`, `audit-alignment` (redirect) |

Plugin bundle copies `.cursor/skills/` first; maintainer skills are **additive only** (no overwrite).

Canvas/plan local artifacts: [ADR-010](../decisions/ADR-010-canvas-plan-local-artifacts.md) · skill `canvas-artifacts`.

## Multi-consumer isolation

One universal Marketplace **payload**; each activated app gets its own gitignored `.local/` and **team-committed** kit copy. Private settings never land on GitHub when DRIFT-013 passes. Full contract: [multi-consumer-isolation.md](../operations/multi-consumer-isolation.md).

See [folder-charter.md](../governance/folder-charter.md) and [decisions/README.md](../decisions/README.md).
