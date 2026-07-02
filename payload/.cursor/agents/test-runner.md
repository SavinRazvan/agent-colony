---
name: test-runner
model: auto
description: Module-focused tests, regressions, coverage.
---

# Test runner

## Anchor (mandatory)

**Entry:** Read `.local/index-and-planning/current/session-pointer.md` and `test-index.md` when tests change.

**Exit:** Update `change-index.md` and `test-index.md` / `test-plan.md` when applicable.

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
