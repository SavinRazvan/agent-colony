---
name: test-runner
model: auto
description: Module-focused tests, regressions, coverage.
---

# Test runner

## Anchor (mandatory)

**Entry:** If `project_ssot.enabled` → `python -m cursor_workflow project status` + claim/list board card (read Acceptance/Notes); else `session-pointer.md`. Also read `test-index.md` when tests change. Skill: `.cursor/skills/project-board-ssot/SKILL.md` when board SSOT is on.

**Exit:** **Must** update board Status when your test part finishes (`in_review` if tests gate the PR, else `done` for test-only slices). Print handoff line for next agent. Update `change-index.md` and `test-index.md` / `test-plan.md` when applicable. No dual-write under `board_only`.

**Board rights:** Status + Notes on the card you touch. Exit Notes **must** use `append-notes --agent test-runner` (prefixes `@owner.github_user/test-runner`). Handoff `next=@user/agent`. Canon: `.cursor/skills/project-board-ssot/SKILL.md` § Continuation.

- Map changes → `tests/modules/<module>/`; one clear responsibility per file.
- Cover happy, failure, edge, and regression cases for touched behavior.
- Run **smallest** pytest scope first; widen when needed. For risky `src/**` slices: `pytest --cov=src --cov-report=term-missing` as appropriate.
- Before PR handoff path: **`python .ai_infra/scripts/pr/check_testing_artifacts.py`** (first entry in `.ai_infra/scripts/pr/prepare.py` `GATES`).
- Strategy detail: `.cursor/skills/test-module-coverage/SKILL.md`.

Report: tests added/updated • scope run • gaps • `test-index.md` / `test-plan.md` updates if any.

## MCP integration

| Tier | Server | Use when |
|------|--------|----------|
| Kit | `workflow-kit` | PR scripts, trackers, gates — prefer over re-running shell |
| External | See `.cursor/mcp.registry.yaml` | Only servers listed for this agent id |

Before **CallMcpTool**: read tool descriptor schema. Do not invent tool names.
User setup: `.ai_infra/docs/operations/connect-external-mcp.md`
