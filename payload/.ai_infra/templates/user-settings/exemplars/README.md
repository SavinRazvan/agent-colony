# User settings (complete me)

Gitignored folder: **`.local/user_settings/`**

Fill in the YAML files below once after install. They stay on your machine — not committed.

## Files

| File | What to complete |
|------|------------------|
| [`github.collaboration.yaml`](github.collaboration.yaml) | **Identity** (`owner`), **Project SSOT** (`project_ssot`), AI disclosure, PR templates, agent pipelines |
| [`mcp.agents.yaml`](mcp.agents.yaml) | External MCP servers, which agents use them, env/secrets checklist |

## Three surfaces in `github.collaboration.yaml`

| Surface | Key | Purpose |
|---------|-----|---------|
| Commits | `owner` + `commit_provenance` | `Author:` / `GitHub-User:` / `Assisted-by:` |
| PR | `pr_collaboration` | Pipelines, `Action-By:`, PR body |
| **Project SSOT** | `project_ssot` | Shared GitHub Project backlog/status (board replaces local tracker markdown when `enabled: true`) |

Set `project_ssot.enabled: true` only after filling board `owner` / `number` / `project_id` / field option ids. Requires `gh` scopes `read:project` + `project`.

## GitHub flow (after you edit `github.collaboration.yaml`)

1. **Validate:** `python3 -m agent_colony contributors validate`
2. **Commits** — append rendered block: `python3 -m agent_colony contributors commit-trailers`
3. **PR scripts** — use pipeline from YAML:  
   `python .ai_infra/scripts/pr/prepare.py --pr <id> --pipeline default`  
   (`--actor` / `--agents` optional when YAML is complete)
4. **PR body** — `python3 -m agent_colony contributors pr-body --summary "your bullet" --pipeline default`
5. **Project board** — when `project_ssot.enabled`, agents use `gh project …` (or MCP later) per field ids in YAML

Kit rule: **`Author:` / `GitHub-User:`** on commits; **`Action-By:` / `Agent/s:`** on PR artifacts — do not mix the two.  
Board rule: when SSOT is enabled, **do not dual-write** board + `work-tracker.md` (see `sync_policy` / `local_only` in YAML).

## MCP flow (after you edit `mcp.agents.yaml`)

1. Copy fragments into `.cursor/mcp.user.json` (or use `agent-colony mcp link`).
2. Sync agent ↔ server rows into `.cursor/mcp.registry.yaml`.
3. Run `python3 -m agent_colony mcp validate` and reload Cursor MCP.

Guide: [connect-external-mcp.md](../../../docs/operations/connect-external-mcp.md)
