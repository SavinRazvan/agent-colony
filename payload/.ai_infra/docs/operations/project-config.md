<!--
File: project-config.md
Path: .ai_infra/docs/operations/project-config.md
Role: Documents optional project.config.yaml — metadata only, not agent runtime.
Used By:
 - README.md
 - .ai_infra/scripts/install/scaffold.py
Depends On:
 - .ai_infra/scripts/pr/prepare.py
Notes:
 - Pattern A: GATES stay hardcoded in prepare.py.
-->

# Optional `project.config.yaml`

The **MAS Workflow Kit** ships **`.ai_infra/project.config.yaml.example`**. After install, copy it to `project.config.yaml` in the project root and fill in metadata.

## What it is for

| Use | Required? |
|-----|-----------|
| Agents running slices / PR workflow | **No** — they call `.ai_infra/scripts/pr/*` |
| Human onboarding / README | **Nice to have** — author, GitHub handle, protected paths |
| MCP `workflow_get_project_config` | **Nice to have** — manifest of customizations + `mcp:` section |

## What it is not

- **Not** runtime gate configuration — `GATES` in `.ai_infra/scripts/pr/prepare.py` is the single source of truth.
- **Not** read by `prepare.py` or agent prompts by default.

When you add gates to `prepare.py`, update the informational `gates.labels` block in `project.config.yaml` so humans stay aligned.

## Install

Scaffold copies the example automatically:

```bash
python -m cursor_workflow install --target /path/to/project --dry-run
# → COPY …/.ai_infra/project.config.yaml.example
```

Copy to `project.config.yaml` and edit `git.author`, `git.github_user`, `mcp.registry_path`, etc.

## Related

- [`.ai_infra/scripts/install/README.md`](../../scripts/install/README.md)
- [`connect-external-mcp.md`](connect-external-mcp.md)
- [`overlays/README.md`](../../../overlays/README.md)
