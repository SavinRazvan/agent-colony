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

See [ADR-004](../decisions/ADR-004-user-mcp-registry.md) and [ADR-009](../decisions/ADR-009-mcp-pattern-a-cli.md) (Pattern A CLI).

## Pattern A CLI (canonical agent transport)

```bash
python3 -m cursor_workflow mcp doctor
python3 -m cursor_workflow mcp validate [--strict]
python3 -m cursor_workflow mcp list-tools --server workflow-kit
python3 -m cursor_workflow mcp call --server workflow-kit --tool workflow_gate_count
python3 -m cursor_workflow mcp auth --server my-api --token-env MY_TOKEN
python3 -m cursor_workflow mcp smoke --server workflow-kit
```

Cursor IDE MCP loading is optional. Registry YAML is the allowlist for `call` / `list-tools`.

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

4. **Pattern A smoke (preferred — no Cursor host required):**

```bash
python3 -m cursor_workflow mcp doctor
python3 -m cursor_workflow mcp smoke --server deepwiki
python3 -m cursor_workflow mcp call --server deepwiki --tool ask_question \
  --args-json '{"repo":"cloudflare/workers-sdk","question":"What are Workers KV limits?"}'
```

Optional: reload Cursor MCP so `CallMcpTool` also works when the IDE host loads the server.

5. **Try it in chat** — ask an agent (e.g. `researcher`) to use Pattern A CLI or CallMcpTool;
   no secrets, no local process, no `secrets_checklist` entry needed in
   `.local/user_settings/mcp.agents.yaml` for DeepWiki.

Both example files (`.cursor/mcp.registry.yaml.example`, `.cursor/mcp.user.example.json`) already
ship this entry alongside the command-based `my-custom-server` example, so you can see the
URL-based and command-based transport shapes side by side.

### Auth (Pattern A)

```bash
python3 -m cursor_workflow mcp auth --server my-api --token-env MY_API_TOKEN
# stores under .local/user_settings/mcp.secrets.yaml (gitignored)
```

See [ADR-009](../decisions/ADR-009-mcp-pattern-a-cli.md).

### Stretch: GitHub official remote MCP

GitHub's official remote MCP server (`https://api.githubcopilot.com/mcp/`) is documented as a
secondary/stretch example in `.local/user_settings/mcp.agents.yaml` (commented `github-remote`
block). It is **not** zero-auth: it requires either a Copilot seat (OAuth) or a personal access
token sent as a `Bearer` header — use `mcp auth --server github-remote --token-env GITHUB_TOKEN`.

## Troubleshooting

- `mcp validate` fails: ensure every registry `servers` key exists in merged `mcp.json` `mcpServers`
- `mcp validate --strict` fails without a live `.cursor/mcp.registry.yaml` — copy the example when enforcing user tier
- `mcp doctor` shows configured but NOT host-loaded: expected until Cursor enables project `mcp.json`; use Pattern A CLI anyway
- Secrets: never commit `mcp.user.json` or `.local/user_settings/mcp.secrets.yaml` — `mcp link` / `mcp auth` update `.gitignore`
