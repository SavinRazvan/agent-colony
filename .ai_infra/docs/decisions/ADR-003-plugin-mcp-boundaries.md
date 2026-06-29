# ADR-003: Plugin vs MCP boundaries

**Status:** accepted  
**Date:** 2026-06-14

## Context

Cursor Plugins load agents/skills/rules. MCP servers expose tools. These are distinct distribution channels.

## Decision

- **Plugin** = Cursor contract plane (`.cursor/`, `.agents/` skills/rules) + optional payload `.ai_infra/`
- **MCP** = optional `workflow-kit` server wrapping `.ai_infra/scripts/` — not a substitute for install
- Install flag: `--with-mcp-json` / `with_mcp` manifest profile

## Consequences

- `mcp.json` references `workflow_mcp` package under `.ai_infra/mcp_servers/`
- User external MCP servers are ADR-004 (registry), not plugin core
