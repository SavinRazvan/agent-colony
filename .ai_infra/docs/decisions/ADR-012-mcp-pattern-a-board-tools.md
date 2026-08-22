# ADR-012: MCP Pattern A board tools

**Status:** accepted  
**Date:** 2026-08-22

## Context

Board Pattern A (`project entry` / `claim` / `handoff` / outbox) exists as CLI only. Agents invent raw `gh api graphql`, miss `--last`, retry EXIT_QUEUED (6), or load full skills. Kit MCP (`agent-colony-mcp`) already wraps PR/gates/validators but not board recipes. Accuracy needs typed tools; efficiency needs digest/summary response shapes.

Related: [ADR-003](ADR-003-plugin-mcp-boundaries.md), [ADR-008](ADR-008-project-board-ssot.md), [ADR-009](ADR-009-mcp-pattern-a-cli.md), [token-efficiency.md](../operations/token-efficiency.md).

## Decision

1. **Wrap only** — MCP board tools call existing `project_cli.cmd_*` / `doc_cli` / drift CLI. No second GraphQL client.
2. **Response envelope** on new tools: `exit_code`, `summary`, `next_recommended_tool`, `detail` (null unless failure). EXIT_QUEUED (6) → recommend `workflow_project_outbox_status`; never recommend retry.
3. **CLI remains canonical** when MCP host is unavailable (ADR-009 Pattern A CLI).
4. **Registry allowlist** — board/session/skill-section tools for Pattern A agents; `workflow_run_gate` restricted to **verifier** only.
5. Ship as kit **0.7.2** (0.7.1 already released).

## Tools

| Tool | Wraps |
|------|-------|
| `workflow_project_entry` | `project entry` (`digest=True` default) |
| `workflow_project_claim` | `project claim --last` |
| `workflow_project_handoff` | `project handoff --last` |
| `workflow_project_outbox_status` | `project outbox status` |
| `workflow_session_entry` | entry digest + last item + change-index row |
| `workflow_doc_skill_section` | `doc skill-section` |
| `workflow_drift_validate(summary=…)` | extend existing tool |

## Consequences

- Module: `.ai_infra/mcp_servers/agent_colony_mcp/project_tools.py`
- Agents prefer MCP/CLI Pattern A; ban raw Project GraphQL when tools exist
- Schema tax amortized by replacing multi-read / wrong-retry paths

## Alternatives rejected

| Alternative | Why rejected |
|-------------|--------------|
| Second MCP server for board | Extra schema tax every turn |
| Reimplement GraphQL in MCP | Drift from CLI SSOT |
| Replace always-on rules with MCP | Governance must stay always-applied |

## References

- [server.py](../../mcp_servers/agent_colony_mcp/server.py)
- [project_cli.py](../../install/agent_colony/project_cli.py)
- [ADR-009](ADR-009-mcp-pattern-a-cli.md)
