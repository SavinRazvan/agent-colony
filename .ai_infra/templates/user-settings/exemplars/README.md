# User settings (complete me)

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

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

Optional **`project_ssot.outbox`**: local JSONL buffer for board writes when GraphQL is rate-limited. It is **not** a second Status SSOT — flush with `python3 -m agent_colony project outbox flush` after quota recovers. See `.ai_infra/templates/project-board/outbox-entry.schema.json`.

**Tier-1 board fields** (agent defaults): Status, Notes, Assignee (human from `owner.github_user`), Priority, Size, **Start date** on claim (`fields.start_date` + `conventions.set_start_date_on_claim`), **Estimate** via `project set-field --field estimate`. Linked PRs are derived on Issues + `mention-pr` Notes — not a writable Project field. Iteration / Labels / Reviewers / End date stay human or later slices.

Set `project_ssot.enabled: true` only after filling board `owner` / `number` / `project_id` / field option ids. Requires `gh` scopes `read:project` + `project`.

## GitHub flow (after you edit `github.collaboration.yaml`)

1. **Validate:** `python3 -m agent_colony contributors validate`
2. **Commits** — append rendered block: `python3 -m agent_colony contributors commit-trailers`
3. **PR scripts** — use pipeline from YAML:  
   `python .ai_infra/scripts/pr/prepare.py --pr <id> --pipeline default`  
   (`--actor` / `--agents` optional when YAML is complete)
4. **PR body** — `python3 -m agent_colony contributors pr-body --summary "your bullet" --pipeline default`
5. **Project board** — when `project_ssot.enabled`, agents use Pattern A CLI (`project entry` / `claim` / `handoff`) per field ids in YAML

Kit rule: **`Author:` / `GitHub-User:`** on commits; **`Action-By:` / `Agent/s:`** on PR artifacts — do not mix the two.  
Board rule: when SSOT is enabled, **do not dual-write** board + `work-tracker.md` (see `sync_policy` / `local_only` in YAML).  
Notes and handoffs: short attributed lines; say *prepare gates green*.

## MCP flow (after you edit `mcp.agents.yaml`)

1. Copy fragments into `.cursor/mcp.user.json` (or use `agent_colony mcp link`).
2. Sync agent ↔ server rows into `.cursor/mcp.registry.yaml`.
3. Run `python3 -m agent_colony mcp validate` and reload Cursor MCP.

Guide: [connect-external-mcp.md](../../../docs/operations/connect-external-mcp.md)
