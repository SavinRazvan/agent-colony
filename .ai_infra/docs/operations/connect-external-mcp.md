# Connect external MCP (<5 min)

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)


Link **any** MCP server to kit agents without forking agent prompts.

## Prerequisites

- Agent Colony installed (`with_mcp` profile or `--with-mcp-json`)
- Cursor MCP enabled for the workspace

## Quick path

**Consumer activate** (`with_mcp` / `--with-mcp-json`) already seeds DeepWiki into
`mcp.user.json` + live `mcp.registry.yaml` when those keys are missing (does not seed
`my-custom-server`). Kit-dev repos skip that seed so CI `health` stays kit-tier only.

Re-run without full activate:

```bash
python3 -m agent_colony mcp seed --deepwiki
python3 -m agent_colony mcp validate
```

1. **Registry** — copy example only if live registry is missing and you did not activate:

```bash
cp .cursor/mcp.registry.yaml.example .cursor/mcp.registry.yaml
```

2. **User servers** — secrets stay gitignored:

```bash
# preferred for DeepWiki only:
python3 -m agent_colony mcp seed --deepwiki
# or full worksheet (includes my-custom-server stub):
cp .cursor/mcp.user.example.json .cursor/mcp.user.json
# edit mcpServers in mcp.user.json
```

Or link a fragment:

```bash
agent-colony mcp link --name my-api --file .cursor/mcp.d/my-api.json
```

3. **Merge + validate:**

```bash
agent-colony mcp validate
```

4. Reload Cursor MCP; agents read `.cursor/mcp.registry.yaml` for which servers apply to their role.

**Worksheet:** complete **`.local/user_settings/mcp.agents.yaml`** (copied at install) — human-friendly server list and agent mapping — then apply to `.cursor/mcp.user.json` and the registry.

## Two-tier model

| Tier | Config | Purpose |
|------|--------|---------|
| Kit | `mcp.json.kit.example` → merged into `mcp.json` | `agent-colony-mcp` tools (PR, board Pattern A, trackers, gates) — ADR-012 |
| User | `mcp.user.json` + registry YAML | External servers per agent |

See [ADR-004](../decisions/ADR-004-user-mcp-registry.md), [ADR-009](../decisions/ADR-009-mcp-pattern-a-cli.md) (Pattern A CLI), and [ADR-012](../decisions/ADR-012-mcp-pattern-a-board-tools.md) (board MCP wrappers).

## Pattern A CLI (canonical agent transport)

```bash
python3 -m agent_colony mcp doctor
python3 -m agent_colony mcp validate [--strict]
python3 -m agent_colony mcp seed --deepwiki
python3 -m agent_colony mcp list-tools --server agent-colony-mcp
python3 -m agent_colony mcp call --server agent-colony-mcp --tool workflow_gate_count
python3 -m agent_colony mcp auth --server my-api --token-env MY_TOKEN
python3 -m agent_colony mcp smoke --server agent-colony-mcp
```

Cursor IDE MCP loading is optional. Registry YAML is the allowlist for `call` / `list-tools`.

## Worked example: DeepWiki (zero auth)

[DeepWiki](https://deepwiki.com) hosts a free, remote MCP server with no authentication — the
fastest way to validate the two-tier flow end-to-end (also the kit's live demo script).

**Preferred:** consumer activate or `mcp seed --deepwiki` writes the user fragment + registry
entry (seven Pattern A agents). Manual worksheet:

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
    agents: [implementer, test-runner, verifier, auditor, researcher, integrator, drift-guard, board]
    tools_hint: [read_wiki_structure, read_wiki_contents, ask_question]
```

4. **Pattern A smoke (preferred — no Cursor host required):**

```bash
python3 -m agent_colony mcp doctor
python3 -m agent_colony mcp smoke --server deepwiki
python3 -m agent_colony mcp call --server deepwiki --tool ask_question \
  --args-json '{"repoName":"karpathy/nanochat","question":"What is nanochat in one sentence?"}'
```

Tool args use **`repoName`** (not `repo`). The target GitHub repo must already be indexed on
[deepwiki.com](https://deepwiki.com) or the call returns “Repository not found.”

**Two URLs, one slug:** for nanochat, GitHub is
[github.com/karpathy/nanochat](https://github.com/karpathy/nanochat) (clone / `research fetch`);
DeepWiki is [deepwiki.com/karpathy/nanochat](https://deepwiki.com/karpathy/nanochat) (wiki index).
MCP still takes `"repoName":"karpathy/nanochat"` — not either full URL. Use any indexed wiki for
a first smoke; index your own product repo on DeepWiki before querying it.

Optional: reload Cursor MCP so `CallMcpTool` also works when the IDE host loads the server.

5. **Try it in chat** — ask an agent (e.g. `researcher`) to use Pattern A CLI or CallMcpTool;
   no secrets, no local process, no `secrets_checklist` entry needed in
   `.local/user_settings/mcp.agents.yaml` for DeepWiki. Use **`/mcp-connect`** intents:
   enable DeepWiki | link custom | doctor/smoke.

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png" alt="Agent chat: ask DeepWiki MCP about karpathy/nanochat repository" width="800" />
  </a>
</p>
<p align="center"><sub><strong>16</strong> — DeepWiki in chat · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png" alt="Terminal: python3 -m agent_colony mcp call deepwiki ask_question success output" width="800" />
  </a>
</p>
<p align="center"><sub><strong>17</strong> — CLI <code>mcp call</code> PASS · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png">Full size</a></sub></p>

Both example files (`.cursor/mcp.registry.yaml.example`, `.cursor/mcp.user.example.json`) already
ship this entry alongside the command-based `my-custom-server` example, so you can see the
URL-based and command-based transport shapes side by side.

### Auth (Pattern A)

```bash
python3 -m agent_colony mcp auth --server my-api --token-env MY_API_TOKEN
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
- DeepWiki `ask_question` / `read_wiki_*`: use **`repoName`** (not `repo`). “Repository not found” means the repo is not indexed on [deepwiki.com](https://deepwiki.com) yet — open/index it there, or smoke with an already-indexed repo (e.g. `karpathy/nanochat`)
- Secrets: never commit `mcp.user.json` or `.local/user_settings/mcp.secrets.yaml` — `mcp link` / `mcp auth` update `.gitignore`
- **Kit-dev:** committed `.cursor/mcp.registry.yaml` and on-disk `.cursor/mcp.json` stay **kit-tier only** (`agent-colony-mcp`). Put DeepWiki (and other externals) in gitignored `mcp.user.json`; do **not** add `tier: external` to the live registry (`mcp validate` rejects that). Pattern A `mcp smoke` / `mcp call` / `mcp list-tools` use an **in-memory effective registry**: live kit entries plus matching servers from `mcp.registry.yaml.example` that exist in merged kit+user `mcpServers`. Consumers still get DeepWiki written into the live registry on activate / `mcp seed`.
