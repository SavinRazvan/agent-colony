<!--
File: local-workspace-layout.md
Path: .ai_infra/docs/operations/local-workspace-layout.md
Role: Versioned map of the gitignored `.local/` operating workspace.
Used By:
 - AGENTS.md, maintainer onboarding
Depends On:
 - .ai_infra/scripts/pr/local_workflow_paths.py
 - .ai_infra/templates/local-workspace/
Notes:
 - Canonical workflow text lives under `.ai_infra/docs/operations/`.
-->

# Local workspace layout (`.local/`)

The `.local/` directory is **gitignored**. This document is the **versioned contract** for how it should be organized.

## Version control (must stay out of git)

- **Never commit** paths under `.local/`.
- Canonical workflow text: **`.ai_infra/docs/operations/agent-workflow-procedures.md`**, **`workflow-complete.md`**.
- **Sanity check:** `git ls-files .local/` should print **nothing**.

## Agent efficiency (read order)

**Usually read:** `index-and-planning/current/session-pointer.md`, `plan.md`, `work-tracker.md`; PR artifacts under `workflow-artifacts/pr/` when merging.

**Usually skip:** `generated-data/**`, long `history/` unless investigating regressions.

## Artifact tiers

| Tier | Location | Who writes | Examples |
|------|----------|------------|----------|
| **0 — Product** | `docs/`, `src/`, overlays | Humans + merged PRs | `docs/architecture/`, ADRs |
| **1 — Base** | `.local/` at install | `scaffold.py` / `activate` | Neutral trackers, empty `workflow-artifacts/*` buckets, README stubs |
| **2 — Runtime** | `.local/` during work | Agents + PR scripts | Filled trackers, `review.md`, drift/alignment/EA artifacts |

**Rule:** Tier 1 paths are stable across projects. Tier 2 content is project-unique. Do not store product truth only in `.local` when it belongs in `docs/`.

**Bucket SSOT:** `.ai_infra/scripts/pr/local_workflow_paths.py` (`WORKFLOW_ARTIFACT_BUCKETS`, `ensure_workflow_artifacts_tree`).

## Top-level buckets

| Path | Purpose |
|------|---------|
| `index-and-planning/current/` | Live trackers: `plan.md`, `work-tracker.md`, `session-pointer.md`, `change-index.md`, tests, `architecture.md` |
| `index-and-planning/history/` | `updates-log.md` (UTC-prefixed lines), `continuity-index.md` (rolling ≥3-day board↔artifact index) |
| `index-and-planning/audits/` | Local governance audit snapshots |
| `agents-control-center/` | **Deprecated** HTML dashboards + `config/pages.json` (offline tracker browser; prefer board SSOT) |
| `workflow-artifacts/pr/` | `review.md`, `prep.md`, `merge.md` |
| `workflow-artifacts/alignment/` | `alignment-audit.md`, `alignment-todos.md` |
| `workflow-artifacts/enterprise-architecture-audit/` | Full audit report + actions |
| `workflow-artifacts/drift/` | `drift-audit.md`, `drift-todos.md` (drift-guard) |
| `workflow-artifacts/release/` | Optional RC sign-off (`rc-signoff.md`) |
| `workflow-artifacts/audit/` | `preflight.json`, `doc-facts-preflight.json` (verify-all / doc validate) |
| `user_settings/` | Gitignored YAML worksheets: GitHub collaboration + MCP agent wiring (from kit exemplars) |
| `generated-data/` | Coverage JSON, `project-board-snapshot.json` (read-only board export for ICC), and similar machine output |
| `canvases/` | Ephemeral session canvases (gitignored); index at `index.md`; sync via `agent_colony canvas` |
| `plans/` | Dated plan-mode snapshots only (not live SSOT under `board_only`); index at `index.md` |
| `workflow-artifacts/canvas/` | Optional `canvas doctor` reports (ADR-010) |

## Git commits vs `.local` markdown

- **Git trailers** (`Author`, `GitHub-User`, optional `Assisted-by`) — commit messages only.
- **PR artifacts** use `Action-By` / `Prepared-By` / `Agent/s` — see **agent-workflow-procedures.md** §3b.

## Durable documentation (not in `.local`)

- `.ai_infra/docs/operations/workflow-complete.md`
- `.ai_infra/docs/operations/agent-workflow-procedures.md`
- `.ai_infra/docs/architecture/workflow-architecture.md`
- `.ai_infra/docs/governance/folder-charter.md`

## Script alignment

| Script | Behavior |
|--------|----------|
| `.ai_infra/scripts/pr/check_testing_artifacts.py` | Default `--planning-dir`: `.local/index-and-planning/current` |
| `.ai_infra/scripts/pr/review.py`, `prepare.py`, `merge.py` | Artifacts via `local_workflow_paths.py` |
| `.ai_infra/scripts/install/scaffold.py` | Tier 1: exemplar trackers (if missing), artifact buckets, README stubs, `AGENTS.md` (if missing); kit-managed **deprecated** dashboards + `pages.json` **always refreshed** on scaffold/activate |
| `.ai_infra/scripts/ci/seed_kit_workspace.py` | CI fixture seed; same bucket set as scaffold |

## Templates (versioned in git)

Copy from **`.ai_infra/templates/local-workspace/`** into `.local/` at scaffold (`exemplars/`, `artifact-stubs/`). Dashboard HTML, assets, `module-audit.html`, and `pages.json` refresh from templates on every scaffold/activate (idempotent re-activate included).

**Implementation Control Center (deprecated HTML):** manifest tab **Project Board** (`format: project-board-snapshot`) renders `.local/generated-data/project-board-snapshot.json` via `local-board-snapshot.js`. Refresh snapshot with `python3 -m agent_colony project export`. The panel is **read-only** — it never writes GitHub Project Status. Prefer the live Project board when `project_ssot.enabled`.

**User settings:** copy from **`.ai_infra/templates/user-settings/exemplars/`** into **`.local/user_settings/`** (`github.collaboration.yaml`, `mcp.agents.yaml`). See [RENDERED-EXAMPLES.md](../../templates/user-settings/RENDERED-EXAMPLES.md).

Path canon for kit layout: [ADR-002-path-canon.md](../decisions/ADR-002-path-canon.md).
