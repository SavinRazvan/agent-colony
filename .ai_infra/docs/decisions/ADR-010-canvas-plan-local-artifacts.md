# ADR-010: Canvas and plan local artifacts (Pattern A)

**Status:** accepted  
**Date:** 2026-08-05

## Context

Kit canvases live in git under `canvases/*.canvas.tsx`, but Cursor IDE only compiles canvases from `~/.cursor/projects/<workspace>/canvases/`. Plan-mode output lands in global `~/.cursor/plans/`, while live slice plans under `board_only` belong on the GitHub Project card (ADR-008). Agents need durable, project-scoped history for ephemeral canvases and plan snapshots without creating a second writable SSOT.

## Decision

1. **Three canvas tiers:** repo `canvases/` (git SSOT for product docs), Cursor managed path (render bridge only), `.local/canvases/` (session evidence, gitignored).
2. **Two plan tiers:** live plan on board card body (or `plan.md` offline fallback); `.local/plans/` holds dated **snapshots only** — never competing backlog/status.
3. **CLI is canonical:** `python3 -m cursor_workflow canvas doctor|list|sync|save` and `plan snapshot|list|open`.
4. **Explicit sync:** no silent overwrite of Cursor managed canvases on activate; `canvas sync --all` requires `--force`; `--missing` copies only absent managed files.
5. **Evidence:** optional doctor reports under `.local/workflow-artifacts/canvas/`.

## Consequences

- Modules: `cursor_host_paths.py`, `canvas_manage.py`, `canvas_cli.py`, `plan_manage.py`, `plan_cli.py`
- Skill: `.cursor/skills/canvas-artifacts/SKILL.md`
- **`plan open`** copies the latest `.local/plans/<date>-<slug>.plan.md` snapshot to `~/.cursor/plans/<slug>.plan.md` so humans get IDE Build; requires `--force` when the Cursor twin already exists (same safety model as `canvas sync --all`)
- **Agents build from `.local/plans/`** via `plan list` + read snapshot — never depend on Build or the global Cursor plan store
- Extends ADR-008 (no dual-write); complements Cursor global canvas/plan skills

## References

- [ADR-008](ADR-008-project-board-ssot.md)
- Ops: `.ai_infra/docs/operations/local-workspace-layout.md`, `PLUGIN-USER-GUIDE.md`
- Skill: `.cursor/skills/canvas-artifacts/SKILL.md`
