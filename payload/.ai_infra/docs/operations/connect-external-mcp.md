# Connect external MCP (<5 min)

Link **any** MCP server to kit agents without forking agent prompts.

## Prerequisites

- MAS Workflow Kit installed (`with_mcp` profile or `--with-mcp-json`)
- Cursor MCP enabled for the workspace

## Quick path

1. **Registry** — copy example and edit agent mappings:

```bash
cp .cursor/mcp.registry.yaml.example .cursor/mcp.registry.yaml
```

2. **User servers** — secrets stay gitignored:

```bash
cp .cursor/mcp.user.example.json .cursor/mcp.user.json
# edit mcpServers in mcp.user.json
```

Or link a fragment:

```bash
cursor-workflow mcp link --name my-api --file .cursor/mcp.d/my-api.json
```

3. **Merge + validate:**

```bash
cursor-workflow mcp validate
```

4. Reload Cursor MCP; agents read `.cursor/mcp.registry.yaml` for which servers apply to their role.

**Worksheet:** complete **`.local/user_settings/mcp.agents.yaml`** (copied at install) — human-friendly server list and agent mapping — then apply to `.cursor/mcp.user.json` and the registry.

## Two-tier model

| Tier | Config | Purpose |
|------|--------|---------|
| Kit | `mcp.json.kit.example` → merged into `mcp.json` | `workflow-kit` tools (PR, trackers, gates) |
| User | `mcp.user.json` + registry YAML | External servers per agent |

See [ADR-004](../decisions/ADR-004-user-mcp-registry.md).

## Troubleshooting

- `mcp validate` fails: ensure every registry `servers` key exists in merged `mcp.json` `mcpServers`
- Secrets: never commit `mcp.user.json` — scaffold adds it to `.gitignore`
