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
- `mcp-connect` skill and ops doc
- Secrets in `.cursor/mcp.user.json` (gitignored)

## Reference implementation

DeepWiki (`https://mcp.deepwiki.com/mcp`) is wired as the live worked example of the User tier —
zero-auth, remote (URL-based `mcpServers` entry, no `command`/`args`), proving the registry +
`mcp.user.json` flow works for non-command transports as well as command-based ones. See
`.ai_infra/docs/operations/connect-external-mcp.md` § Worked example: DeepWiki, and the shipped
`deepwiki` rows in `.cursor/mcp.registry.yaml.example`, `.cursor/mcp.user.example.json`, and
`.ai_infra/templates/user-settings/exemplars/mcp.agents.yaml`.
