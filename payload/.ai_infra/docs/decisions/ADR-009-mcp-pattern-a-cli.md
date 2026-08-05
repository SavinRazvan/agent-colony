# ADR-009: MCP Pattern A CLI (universal agent transport)

**Status:** accepted  
**Date:** 2026-08-05

## Context

ADR-003/004 define kit + user MCP tiers and a registry. Cursor agent sessions often load only plugin MCPs, not project `.cursor/mcp.json` servers (`workflow-kit`, DeepWiki). Agents need a transport that works in shell, CI, and chat without depending on Cursor host loading.

## Decision

1. **CLI is canonical:** `python3 -m cursor_workflow mcp doctor|list-tools|call|auth|smoke` (plus existing `validate` / `link`).
2. **Registry allowlist:** `mcp call` / `list-tools` only target servers present in `.cursor/mcp.registry.yaml` (when that file exists); `--agent` filters to servers that list the agent.
3. **Secrets:** `.local/user_settings/mcp.secrets.yaml` (gitignored); `mcp.user.json` stays transport-only.
4. **Cursor `CallMcpTool` is optional** when the IDE host loads the same server; docs/skills must not require it.
5. **Kit `workflow-kit` stdio server unchanged** — still wraps `.ai_infra/scripts/`; CLI client talks to it over MCP stdio.
6. **Exit codes:** align with project CLI (`0/2/3/4/5`); remote outbox / `EXIT_QUEUED=6` deferred.

## Consequences

- Modules: `mcp_cli.py`, `mcp_client.py`, `mcp_secrets.py` beside `mcp_manage.py`
- Evidence under `.local/workflow-artifacts/mcp/`
- Agent MCP sections prefer CLI recipes
- Extends ADR-004; does not replace ADR-003 boundaries

## References

- [ADR-003](ADR-003-plugin-mcp-boundaries.md), [ADR-004](ADR-004-user-mcp-registry.md)
- Ops: `.ai_infra/docs/operations/connect-external-mcp.md`
- Skill: `.cursor/skills/mcp-connect/SKILL.md`
