---
name: workflow-activate
description: Install MAS Workflow Kit infrastructure into the current workspace from the plugin payload (ADR-001 Option B).
---

# Workflow activate

## When

First use after enabling the **MAS Workflow Kit** plugin in a project workspace.

## Command

From the **distribution root** (directory containing `payload/` and `.cursor-plugin/`):

```bash
python payload/cursor_workflow install \
  --target /path/to/your-project \
  --source payload \
  --profile with_mcp \
  --with-mcp-json \
  --verify
```

`--source payload` resolves against the distribution root even when the CLI shim lives under `payload/`.

Use the open workspace path for `--target` when activating in place.

## Post-install (required before first PR)

1. **Personalize** `.local/user_settings/`:
   - `github.collaboration.yaml` — owner, pipelines, commit provenance
   - `mcp.agents.yaml` — optional MCP worksheet
2. **Validate settings:**
   ```bash
   python payload/cursor_workflow contributors validate --directory /path/to/your-project
   python payload/cursor_workflow integrate validate --directory /path/to/your-project
   ```
3. **Gates:**
   ```bash
   python payload/cursor_workflow gates --directory /path/to/your-project
   ```

## Adding agents, skills, or MCP later

Invoke **`integrator-mas-agent`** with skill **`mas-infrastructure-integration`**.

- ADR: `.ai_infra/docs/decisions/ADR-006-agent-integration-model.md`
- Ops: `.ai_infra/docs/operations/mas-infrastructure-integration.md`
- Checklist: `.ai_infra/templates/agent-integration/INTEGRATION-CHECKLIST.md`

## Success

- `.ai_infra/scripts/pr/prepare.py` exists in the target workspace
- `.local/index-and-planning/current/session-pointer.md` scaffolded
- `contributors validate` and `integrate validate` exit 0
- `python payload/cursor_workflow gates --directory /path/to/your-project` exits 0

## Reference

- `.ai_infra/docs/decisions/ADR-001-distribution-activation.md` (after install)
- `.ai_infra/docs/operations/consumer-quickstart.md`
