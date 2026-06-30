# AGENTS.md

## Project intent

**Cursor Agent Infrastructure** — multi-agent workflow installed via plugin. Agents call **one script command** per maintainer action; `GATES` live in `.ai_infra/scripts/pr/prepare.py`.

## First reads

1. [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md)
2. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — **Artifact tiers** (base scaffold vs runtime `workflow-artifacts/`)
3. [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md)
4. `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`

## Rules

Six universal rules under `.cursor/rules/`. Product overlays: `overlays/rules/` at install time.

## Quality gates

`GATES` in `.ai_infra/scripts/pr/prepare.py` — say *prepare gates green* in chat; do not paste full gate lists.
