# `.ai_infra/` — MAS Workflow Kit product tree

Versioned workflow kit assets live here. **`.cursor/` and `.agents/` stay at repo root** (Cursor IDE contract).

## Layout

| Path | Role |
|------|------|
| `.ai_infra/scripts/pr/` | PR spine — **`prepare.py` owns `GATES`** |
| `.ai_infra/scripts/architecture/` | Governance + debrand scanners |
| `.ai_infra/scripts/install/` | `scaffold.py` — consumer install |
| `.ai_infra/scripts/release/` | `sync_plugin_bundle.py` — marketplace payload |
| `.ai_infra/mcp_servers/workflow_mcp/` | Optional MCP server (wraps scripts) |
| `.ai_infra/docs/` | governance, operations, roadmap, handoff, architecture |
| `.ai_infra/templates/` | AGENTS stub, local-workspace exemplars, plugin skills |
| `.ai_infra/install/cursor_workflow/` | `cursor-workflow` CLI (install, gates, health, mcp) |

## Path resolution

Use `.ai_infra/paths.py` (`kit_root`, `scripts_dir`, `ui_local_workspace`, `mcp_package_dir`).

## Verification

```bash
make gates
make install-dry-run
make check-plugin
python -m cursor_workflow health
python -m workflow_mcp   # optional; see .cursor/mcp.json.kit.example
```
