# Upgrade Agent Colony

Re-run install from a **newer kit source** (git tag, plugin payload, or local clone) into the same consumer project.

## Breaking change (0.6.0)

Kit **0.6.0** renames the Python CLI module and console script:


| Before (removed)            | After                             |
| --------------------------- | --------------------------------- |
| `python -m cursor_workflow` | `python -m agent_colony`          |
| Console script `cursor-workflow` | `agent-colony`               |
| Root package dir `cursor_workflow/` | `agent_colony/`             |
| Install package `.ai_infra/install/cursor_workflow/` | `.ai_infra/install/agent_colony/` |


**Cold cut** — old names are not aliased. After upgrading:

1. Re-run `/workflow-activate` or `python -m agent_colony activate --directory .`
2. Reinstall editable tooling: `pip install -e ".[dev,mcp]"` (kit-dev) so the `agent-colony` console script is on PATH
3. Update any local scripts/CI that still call the old module or console script



## Breaking change (0.6.1)

Kit **0.6.1** renames the MCP Python package (Cursor server id unchanged):


| Before (removed)            | After                                     |
| --------------------------- | ----------------------------------------- |
| `python -m workflow_mcp`    | `python -m agent_colony_mcp`              |
| Package dir `.ai_infra/mcp_servers/workflow_mcp/` | `.ai_infra/mcp_servers/agent_colony_mcp/` |
| Cursor server id            | `agent-colony-mcp` (**unchanged**)        |


Update `.cursor/mcp.json` `args` to `["-m", "agent_colony_mcp"]` (or re-run activate / `mcp seed`). MCP **tool** names such as `workflow_`* are unchanged.

## Before upgrade

1. Note current version: `cat .ai_infra/.kit-version`
2. Commit or stash local changes (especially `.cursor/`, `.ai_infra/`, `.local/`)
3. Back up custom overlays under `overlays/rules/` and any `mcp.user.json` secrets



## Upgrade command

**Light refresh (dashboards + activate scripts, keeps trackers):**

```bash
cd ~/Projects/my-app    # your activated project
source .venv/bin/activate
python3 -m agent_colony activate --directory .
```

Same as `/workflow-activate` in Agent chat when planes are already ready. Refreshes kit-managed dashboard HTML, `pages.json`, and install scripts from the plugin payload.

**Full reinstall (scripts, agents, rules — review** `.local/` **merge):**

```bash
python3 -m agent_colony activate --directory . --force
```

**Kit clone / advanced** — from kit repo:

```bash
export TARGET=~/Projects/my-app
.venv/bin/python -m agent_colony install \
  --target "$TARGET" \
  --source . \
  --profile with_mcp \
  --with-mcp-json \
  --verify
```

Use `--source payload` when running from the distribution root (see `workflow-activate` skill).

## What install updates


| Area                            | Behavior                                                                           |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| `.ai_infra/scripts/`            | Overwritten from manifest profile                                                  |
| `.cursor/agents`, rules, skills | Overwritten from kit                                                               |
| `.local/` exemplars             | Re-copied on `--force` only; light re-activate refreshes dashboards + `pages.json` |
| Dashboard HTML / `pages.json`   | Refreshed on every `activate` (idempotent)                                         |
| `AGENTS.md`                     | **Not** overwritten if present — delete to refresh from stub, or merge manually    |
| `mcp.user.json`                 | **Not** overwritten — merge via `python3 -m agent_colony mcp validate`             |
| `.kit-version`                  | Updated to manifest `kit_version`                                                  |




## After upgrade

```bash
cd ~/Projects/my-app
python3 -m agent_colony gates
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```



## Rollback

1. Restore project from git to pre-upgrade commit
2. Or reinstall from previous kit tag/payload matching old `.kit-version`

Document intentional divergences in `.local/index-and-planning/current/updates-log.md`.