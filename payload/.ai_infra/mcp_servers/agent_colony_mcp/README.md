# Workflow MCP server

**Canonical path:** `.ai_infra/mcp_servers/agent_colony_mcp/`

Stdio MCP server that **wraps existing scripts/CLI** — it does not duplicate `resolve_gates()` or Project GraphQL (ADR-012).

## Run locally

```bash
.venv/bin/python -m agent_colony_mcp
AGENT_COLONY_ROOT=/path/to/project .venv/bin/python -m agent_colony_mcp
```

## Cursor wiring

Install with `--with-mcp-json` merges [`.cursor/mcp.json.kit.example`](../../../.cursor/mcp.json.kit.example) into `.cursor/mcp.json`.

External servers: [connect-external-mcp.md](../../docs/operations/connect-external-mcp.md).

## Pattern A board tools (kit 0.7.2+)

JSON envelope: `exit_code`, `summary`, `next_recommended_tool`, `detail`. EXIT_QUEUED (6) → `workflow_project_outbox_status` — never retry.

| Tool | Wraps |
|------|--------|
| `workflow_session_entry` | entry digest + last item + change-index tail |
| `workflow_project_entry` | `project entry` (`digest=True` default) |
| `workflow_project_claim` | `project claim --last --agent` |
| `workflow_project_handoff` | `project handoff --last --agent --next [--to]` |
| `workflow_project_outbox_status` | `project outbox status` |
| `workflow_doc_skill_section` | `doc skill-section` |

## Other P0 tools

| Tool | Wraps |
|------|--------|
| `workflow_run_prepare` | `.ai_infra/scripts/pr/prepare.py` — pass `summary=True` for one-line gate result |
| `workflow_run_review` | `.ai_infra/scripts/pr/review.py` |
| `workflow_run_merge_check` | `.ai_infra/scripts/pr/merge.py` |
| `workflow_run_gate` | single gate — **verifier only** (registry policy) |
| `workflow_check_governance` | `check_governance_consistency.py` |
| `workflow_list_agents` | `.cursor/agents/*.md` |
| `workflow_get_tracker` | `.local/.../current/{name}.md` |
| `workflow_gate_count` | `len(load_gates())` |
| `workflow_get_project_config` | `project.config.yaml` or example |
| `workflow_list_mcp_registry` | `.cursor/mcp.registry.yaml` |
| `workflow_agent_colony_mcp_connection_guide` | connect-external-mcp.md |
| `workflow_render_commit_trailers` | `.local/user_settings/github.collaboration.yaml` |
| `workflow_render_pr_body` | PR body for named pipeline |
| `workflow_contributors_validate` | validate user settings YAML |
| `workflow_list_session_agents` | change-index + session-pointer → merged Agent/s |
| `workflow_integrate_validate` | `.ai_infra/scripts/integration/validate.py` |
| `workflow_drift_validate` | `check_drift.py` — `summary=True` default |
| `workflow_activate` | `activate_cli.py` |
| `workflow_doc_facts_validate` | `check_doc_facts.py` |
| `workflow_verify_all` | `verify_all.py` |

## P1 resources

| URI | Content |
|-----|---------|
| `workflow://inventory` | Agent ids, skill ids, gate count (JSON) |
| `workflow://agents/{agent_id}` | Agent prompt markdown |
| `workflow://skills/{skill_id}` | Full skill body from `.cursor/skills` or `.agents/skills` |
| `workflow://skills/{skill_id}/{section_slug}` | One H2 section only (token-efficient; slug from heading) |
| `workflow://artifacts/pr/{phase}` | PR artifact (`review` \| `prep` \| `prepare` \| `merge`) |
| `workflow://trackers/{name}` | Tracker markdown from `.local/.../current/` |
| `workflow://mcp/registry` | Merged MCP registry JSON |
