# User settings (complete me)

Gitignored folder: **`.local/user_settings/`**

Fill in the YAML files below once after install. They stay on your machine — not committed.

## Files

| File | What to complete |
|------|------------------|
| [`github.collaboration.yaml`](github.collaboration.yaml) | Your name, GitHub handle, AI disclosure policy, PR templates, agent pipelines |
| [`mcp.agents.yaml`](mcp.agents.yaml) | External MCP servers, which agents use them, env/secrets checklist |

## GitHub flow (after you edit `github.collaboration.yaml`)

1. **Validate:** `python3 -m cursor_workflow contributors validate`
2. **Commits** — append rendered block: `python3 -m cursor_workflow contributors commit-trailers`
3. **PR scripts** — use pipeline from YAML:  
   `python .ai_infra/scripts/pr/prepare.py --pr <id> --pipeline default`  
   (`--actor` / `--agents` optional when YAML is complete)
4. **PR body** — `python3 -m cursor_workflow contributors pr-body --summary "your bullet" --pipeline default`

Kit rule: **`Author:` / `GitHub-User:`** on commits; **`Action-By:` / `Agent/s:`** on PR artifacts — do not mix the two.

## MCP flow (after you edit `mcp.agents.yaml`)

1. Copy fragments into `.cursor/mcp.user.json` (or use `cursor-workflow mcp link`).
2. Sync agent ↔ server rows into `.cursor/mcp.registry.yaml`.
3. Run `python3 -m cursor_workflow mcp validate` and reload Cursor MCP.

Guide: [connect-external-mcp.md](../../../docs/operations/connect-external-mcp.md)
