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

## Worked example: DeepWiki (zero auth)

[DeepWiki](https://deepwiki.com) hosts a free, remote MCP server with no authentication — the
fastest way to validate the two-tier flow end-to-end (also the kit's live demo script).

1. **User server** — add the URL-based entry to `.cursor/mcp.user.json` (no `command`/`args`,
   just a `url`):

```json
{
  "mcpServers": {
    "deepwiki": { "url": "https://mcp.deepwiki.com/mcp" }
  }
}
```

2. **Registry** — map it to the agents that should use it, in `.cursor/mcp.registry.yaml`:

```yaml
servers:
  deepwiki:
    tier: external
    description: Public GitHub repo docs/Q&A (no auth) — Cognition DeepWiki
    agents: [researcher, implementer, auditor]
    tools_hint: [read_wiki_structure, read_wiki_contents, ask_question]
```

3. **Merge + validate, then reload Cursor MCP:**

```bash
cursor-workflow mcp validate
```

4. **Try it** — ask an agent (e.g. `researcher`) to read the wiki structure or ask a question
   about any public GitHub repo; no secrets, no local process, no `secrets_checklist` entry
   needed in `.local/user_settings/mcp.agents.yaml`.

Both example files (`.cursor/mcp.registry.yaml.example`, `.cursor/mcp.user.example.json`) already
ship this entry alongside the command-based `my-custom-server` example, so you can see the
URL-based and command-based transport shapes side by side.

### Stretch: GitHub official remote MCP

GitHub's official remote MCP server (`https://api.githubcopilot.com/mcp/`) is documented as a
secondary/stretch example in `.local/user_settings/mcp.agents.yaml` (commented `github-remote`
block). It is **not** zero-auth: it requires either a Copilot seat (OAuth) or a personal access
token sent as a `Bearer` header, so it is not wired live in the kit demo to avoid auth friction —
uncomment and fill in a token to try it yourself.

## Troubleshooting

- `mcp validate` fails: ensure every registry `servers` key exists in merged `mcp.json` `mcpServers`
- Secrets: never commit `mcp.user.json` — scaffold adds it to `.gitignore`
