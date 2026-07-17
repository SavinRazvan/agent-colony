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
| `workflow_integrate_validate` | `.ai_infra/scripts/integration/validate.py` (INT-001…014) |
| `workflow_drift_validate` | `.ai_infra/scripts/workflow/check_drift.py` (DRIFT-001…008) |
| `workflow_activate` | `.ai_infra/install/cursor_workflow/activate_cli.py` (three-plane install) |
| `workflow_doc_facts_validate` | `.ai_infra/scripts/architecture/check_doc_facts.py` (DOC-001…006) |
| `workflow_verify_all` | `.ai_infra/scripts/architecture/verify_all.py` (maintainer matrix) |

## P1 resources

| URI | Content |
|-----|---------|
| `workflow://inventory` | Agent ids, skill ids, gate count (JSON) |
| `workflow://agents/{agent_id}` | Agent prompt markdown |
| `workflow://skills/{skill_id}` | Skill body from `.cursor/skills` or `.agents/skills` |
| `workflow://artifacts/pr/{phase}` | PR artifact (`review` \| `prep` \| `prepare` \| `merge`) |
| `workflow://trackers/{name}` | Tracker markdown from `.local/.../current/` |
| `workflow://mcp/registry` | Merged MCP registry JSON |
