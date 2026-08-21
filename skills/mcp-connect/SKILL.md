---
name: mcp-connect
description: Connect external MCP servers to Agent Colony agents via mcp.user.json and mcp.registry.yaml.
---

# MCP connect

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

User wants kit agents to use **external** MCP tools (Slack, DB, GitHub, custom APIs) alongside built-in `agent-colony-mcp`.

## Intents

### 1. Enable DeepWiki (default zero-auth)

```bash
python3 -m agent_colony mcp seed --deepwiki
python3 -m agent_colony mcp validate
python3 -m agent_colony mcp smoke --server deepwiki
```

Optional: `--force-registry-agents` to reset `deepwiki.agents` to seven Pattern A agents.

### 2. Link custom (auth or private)

```bash
python3 -m agent_colony mcp link --name my-api --file .cursor/mcp.d/my-api.json
# edit .cursor/mcp.registry.yaml — map agents
python3 -m agent_colony mcp auth --server my-api --token-env MY_TOKEN
python3 -m agent_colony mcp validate
```

### 3. Doctor / smoke

```bash
python3 -m agent_colony mcp doctor
python3 -m agent_colony mcp smoke --server agent-colony-mcp
python3 -m agent_colony mcp smoke --server deepwiki
python3 -m agent_colony mcp call --server deepwiki --tool ask_question \
  --args-json '{"repoName":"karpathy/nanochat","question":"What is nanochat in one sentence?"}'
```

### DeepWiki agent contract

| Do | Do not |
|----|--------|
| `list-tools --server deepwiki` before inventing args | Guess `repo` — tool wants **`repoName`** |
| Pass `owner/repo` as `repoName` | Pass deepwiki.com URL as MCP arg |
| Prefer indexed smoke targets (e.g. `karpathy/nanochat`) | Treat “Repository not found” as kit bug |
| Use GitHub URL / `github:` for `research init\|fetch` | Use DeepWiki as substitute for cloning corpus |

## First-time setup (<5 min)

1. Copy `.cursor/mcp.registry.yaml.example` → `.cursor/mcp.registry.yaml` (if missing)
2. Copy `.cursor/mcp.user.example.json` → `.cursor/mcp.user.json` — or `mcp seed --deepwiki`
3. Map server to agents in `mcp.registry.yaml`
4. Validate:

```bash
python3 -m agent_colony mcp validate
python3 -m agent_colony mcp doctor
```

5. Optional: enable MCP in Cursor settings (`CallMcpTool` convenience).

**Pattern A (canonical):** agents call MCP via CLI:

```bash
python3 -m agent_colony mcp list-tools --server agent-colony-mcp
python3 -m agent_colony mcp call --server agent-colony-mcp --tool workflow_gate_count
python3 -m agent_colony mcp auth --server my-api --token-env MY_TOKEN
python3 -m agent_colony mcp smoke --server agent-colony-mcp
```

Walkthrough: [connect-external-mcp.md](../../.ai_infra/docs/operations/connect-external-mcp.md) § Worked example: DeepWiki. Canon: ADR-009.

## Success

- `mcp validate` exits 0
- `mcp doctor` shows configured vs host-loaded
- `mcp list-tools` / `mcp call` work for allowlisted servers
- Target agent markdown includes server under **MCP integration**

## Reference

- [connect-external-mcp.md](../../.ai_infra/docs/operations/connect-external-mcp.md)
- [ADR-004](../../.ai_infra/docs/decisions/ADR-004-user-mcp-registry.md)
- [ADR-009](../../.ai_infra/docs/decisions/ADR-009-mcp-pattern-a-cli.md)
