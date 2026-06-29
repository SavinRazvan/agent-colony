# MCP config files

| File | Role |
|------|------|
| **`mcp.json.kit.example`** | Canonical kit-only fragment (`workflow-kit` server) |
| **`mcp.user.example.json`** | Template for external servers (copy to `mcp.user.json`, gitignored) |
| **`mcp.registry.yaml.example`** | Agent ↔ server mapping template |

Install with `--with-mcp-json` merges kit + user fragments via `mcp_manage.py` → `.cursor/mcp.json`.

See [`.ai_infra/docs/operations/connect-external-mcp.md`](../.ai_infra/docs/operations/connect-external-mcp.md).
