# ADR-004: User MCP registry

**Status:** accepted  
**Date:** 2026-06-14

## Context

Consumers need to attach external MCP servers (Slack, GitHub, custom APIs) to kit agents without forking agent prompts.

## Decision

**Two-tier MCP model:**

| Tier | Server | Configuration |
|------|--------|---------------|
| Kit | `workflow-kit` | Install / `mcp.json.kit.example` |
| User | Any `mcpServers` key | `mcp.user.json` + `mcp.registry.yaml` |

Registry maps agent ids → server keys → tool hints. Agents read registry before `CallMcpTool`. Implementation detail in Phase 5b.

## Consequences

- `cursor_workflow mcp link` / `mcp validate` CLI (Phase 5b)
- `connect-external-mcp` skill and ops doc
- Secrets in `.cursor/mcp.user.json` (gitignored)
