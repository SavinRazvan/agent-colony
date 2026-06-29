# Workflow MCP server

**Canonical path:** `.ai_infra/mcp_servers/workflow_mcp/`

Stdio MCP server that **wraps existing scripts** — it does not duplicate `GATES` from `.ai_infra/scripts/pr/prepare.py`.

## Run locally

```bash
.venv/bin/python -m workflow_mcp
WORKFLOW_KIT_ROOT=/path/to/project .venv/bin/python -m workflow_mcp
```

## Cursor wiring

Install with `--with-mcp-json` merges [`.cursor/mcp.json.kit.example`](../../../.cursor/mcp.json.kit.example) into `.cursor/mcp.json`.

External servers: [connect-external-mcp.md](../../docs/operations/connect-external-mcp.md).

## P0 tools

| Tool | Wraps |
|------|--------|
| `workflow_run_prepare` | `.ai_infra/scripts/pr/prepare.py` |
| `workflow_run_review` | `.ai_infra/scripts/pr/review.py` |
| `workflow_run_merge_check` | `.ai_infra/scripts/pr/merge.py` |
| `workflow_run_gate` | single gate from `GATES` |
| `workflow_check_governance` | `check_governance_consistency.py` |
| `workflow_list_agents` | `.cursor/agents/*.md` |
| `workflow_get_tracker` | `.local/.../current/{name}.md` |
| `workflow_gate_count` | `len(GATES)` |
| `workflow_get_project_config` | `project.config.yaml` or example |
| `workflow_list_mcp_registry` | `.cursor/mcp.registry.yaml` |
| `workflow_mcp_connection_guide` | connect-external-mcp.md |
| `workflow_render_commit_trailers` | `.local/user_settings/github.collaboration.yaml` |
| `workflow_render_pr_body` | PR body for named pipeline |
| `workflow_contributors_validate` | validate user settings YAML |
| `workflow_list_session_agents` | change-index + session-pointer → merged Agent/s |

## P1 resources

`workflow://inventory`, `workflow://agents/{id}`, `workflow://skills/{id}`, `workflow://trackers/{name}`, `workflow://mcp/registry`
