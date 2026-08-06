---
name: mcp-connect
description: Connect external MCP servers to Agent Colony agents via mcp.user.json and mcp.registry.yaml.
---

# MCP connect

## When

User wants kit agents to use **external** MCP tools (Slack, DB, GitHub, custom APIs) alongside built-in `agent-colony-mcp`.

## Intents

### 1. Enable DeepWiki (default zero-auth)

Consumer activate already seeds DeepWiki when `mcp.user.json` / registry keys are missing. On an existing workspace:

```bash
python3 -m cursor_workflow mcp seed --deepwiki
python3 -m cursor_workflow mcp validate
python3 -m cursor_workflow mcp smoke --server deepwiki
```

Optional: `--force-registry-agents` to reset `deepwiki.agents` to the seven Pattern A agents.

### 2. Link custom (auth or private)

```bash
python3 -m cursor_workflow mcp link --name my-api --file .cursor/mcp.d/my-api.json
# edit .cursor/mcp.registry.yaml — map agents
python3 -m cursor_workflow mcp auth --server my-api --token-env MY_TOKEN   # if needed
python3 -m cursor_workflow mcp validate
```

### 3. Doctor / smoke

```bash
python3 -m cursor_workflow mcp doctor
python3 -m cursor_workflow mcp smoke --server agent-colony-mcp
python3 -m cursor_workflow mcp smoke --server deepwiki
```

## Steps (<5 min) — first-time worksheets

1. Copy `.cursor/mcp.registry.yaml.example` → `.cursor/mcp.registry.yaml` (if live missing and you did not activate)
2. Copy `.cursor/mcp.user.example.json` → `.cursor/mcp.user.json` (gitignored) — or prefer `mcp seed --deepwiki`
3. Or link a fragment:

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
python3 -m cursor_workflow mcp list-tools --server agent-colony-mcp
python3 -m cursor_workflow mcp call --server agent-colony-mcp --tool workflow_gate_count
python3 -m cursor_workflow mcp auth --server my-api --token-env MY_TOKEN
python3 -m cursor_workflow mcp smoke --server agent-colony-mcp
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
