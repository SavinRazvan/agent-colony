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

## Top-level buckets

| Path | Purpose |
|------|---------|
| `index-and-planning/current/` | Live trackers: `plan.md`, `work-tracker.md`, `session-pointer.md`, `change-index.md`, tests, `architecture.md` |
| `index-and-planning/history/` | `updates-log.md` |
| `index-and-planning/audits/` | Local governance audit snapshots |
| `agents-control-center/` | Dashboard config (`config/pages.json`) and optional HTML |
| `workflow-artifacts/pr/` | `review.md`, `prep.md`, `merge.md` |
| `workflow-artifacts/alignment/` | `alignment-audit.md`, `alignment-todos.md` |
| `workflow-artifacts/enterprise-architecture-audit/` | Full audit report + actions |
| `user_settings/` | Gitignored YAML worksheets: GitHub collaboration + MCP agent wiring (from kit exemplars) |
| `generated-data/` | Coverage JSON and similar machine output |

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

## Templates (versioned in git)

Copy from **`.ai_infra/templates/local-workspace/`** into `.local/agents-control-center/` at scaffold.

**User settings:** copy from **`.ai_infra/templates/user-settings/exemplars/`** into **`.local/user_settings/`** (`github.collaboration.yaml`, `mcp.agents.yaml`). See [RENDERED-EXAMPLES.md](../../templates/user-settings/RENDERED-EXAMPLES.md).

Historical layout migrations: **`.ai_infra/docs/maintainer/eXo-path-migration-map.md`** (kit dev only).
