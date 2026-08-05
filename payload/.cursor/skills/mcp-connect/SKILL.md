---
name: mcp-connect
description: Connect external MCP servers to MAS Workflow Kit agents via mcp.user.json and mcp.registry.yaml.
---

# MCP connect

## When

User wants kit agents to use **external** MCP tools (Slack, DB, GitHub, custom APIs) alongside built-in `workflow-kit`.

## Steps (<5 min)

1. Copy `.cursor/mcp.registry.yaml.example` → `.cursor/mcp.registry.yaml`
2. Copy `.cursor/mcp.user.example.json` → `.cursor/mcp.user.json` (gitignored)
3. Add server entry to `mcp.user.json` **or** run:

```bash
python3 -m cursor_workflow mcp link --name my-api --file .cursor/mcp.d/my-api.json
```

4. Map the server to agents in `mcp.registry.yaml`
5. Merge and validate:

```bash
python3 -m cursor_workflow mcp validate
python3 -m cursor_workflow mcp doctor
```

6. Optional: enable MCP in Cursor settings for the workspace (`CallMcpTool` convenience).

**Pattern A (canonical):** agents call MCP via CLI — not Cursor host loading:

```bash
python3 -m cursor_workflow mcp list-tools --server workflow-kit
python3 -m cursor_workflow mcp call --server workflow-kit --tool workflow_gate_count
python3 -m cursor_workflow mcp auth --server my-api --token-env MY_TOKEN
python3 -m cursor_workflow mcp smoke --server workflow-kit
```

**Fastest external smoke:** DeepWiki (zero-auth) — copy examples, validate, then:

```bash
python3 -m cursor_workflow mcp smoke --server deepwiki
```

Full walkthrough: `.ai_infra/docs/operations/connect-external-mcp.md` § Worked example: DeepWiki. Canon: ADR-009.

## Success

- `python3 -m cursor_workflow mcp validate` exits 0
- `python3 -m cursor_workflow mcp doctor` shows configured vs host-loaded
- `mcp list-tools` / `mcp call` work for allowlisted servers
- Target agent markdown includes the server under **MCP integration**

## Reference

- `.ai_infra/docs/operations/connect-external-mcp.md`
- `.ai_infra/docs/decisions/ADR-004-user-mcp-registry.md`
- `.ai_infra/docs/decisions/ADR-009-mcp-pattern-a-cli.md`
