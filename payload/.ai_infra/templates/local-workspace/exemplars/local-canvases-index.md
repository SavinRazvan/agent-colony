<!--
File: local-canvases-index.md
Path: .ai_infra/templates/local-workspace/exemplars/local-canvases-index.md
Role: Index for ephemeral session canvases under .local/canvases/
Used By:
 - scaffold.py → .local/canvases/index.md
Notes:
 - ADR-010. Product canvases stay in repo canvases/; this dir is gitignored evidence.
-->

# Local canvases index

Ephemeral agent canvases (billing reviews, one-off analyses). **Not** git SSOT — use `canvases/` for product docs.

| Slug | Saved (UTC) | Agent | Notes |
|------|-------------|-------|-------|

Sync to IDE preview: `python3 -m cursor_workflow canvas sync --from local --name <slug>`
