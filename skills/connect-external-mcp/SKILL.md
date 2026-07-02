---
name: connect-external-mcp
description: Connect external MCP servers to MAS Workflow Kit agents via mcp.user.json and mcp.registry.yaml.
---

# Connect external MCP

## When

User wants kit agents to use **external** MCP tools (Slack, DB, GitHub, custom APIs) alongside built-in `workflow-kit`.

## Steps (<5 min)

1. Copy `.cursor/mcp.registry.yaml.example` → `.cursor/mcp.registry.yaml`
2. Copy `.cursor/mcp.user.example.json` → `.cursor/mcp.user.json` (gitignored)
3. Add server entry to `mcp.user.json` **or** run:

```bash
cursor-workflow mcp link --name my-api --file .cursor/mcp.d/my-api.json
```

4. Map the server to agents in `mcp.registry.yaml`
5. Merge and validate:

```bash
cursor-workflow mcp validate
```

6. Enable MCP in Cursor settings for the workspace.

## Success

- `cursor-workflow mcp validate` exits 0
- `workflow_list_mcp_registry` (workflow-kit MCP) lists external servers
- Target agent markdown includes the server under **MCP integration**

## Reference

- `.ai_infra/docs/operations/connect-external-mcp.md`
- `.ai_infra/docs/decisions/ADR-004-user-mcp-registry.md`
