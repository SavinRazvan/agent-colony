<!--
File: README.md
Path: .ai_infra/templates/local-workspace/README.md
Role: Versioned templates copied into gitignored `.local/` at consumer install.
Used By:
 - .ai_infra/docs/operations/local-workspace-layout.md
Depends On:
 - .ai_infra/scripts/install/scaffold.py
Notes:
 - Exemplars → `.local/index-and-planning/current/`; pages.json → agents-control-center config.
-->

# Local workspace templates

**Canonical path:** `.ai_infra/templates/local-workspace/`

Scaffold copies exemplars into `.local/index-and-planning/current/` and `pages.json` into `.local/agents-control-center/config/`.

| Template | Target |
|----------|--------|
| `exemplars/*.md` | `.local/index-and-planning/current/` |
| `pages.json` | `.local/agents-control-center/config/pages.json` |
| `index.html` | optional dashboard (maintainer refresh) |

Maintainer migrate helper: `.ai_infra/scripts/dev/migrate_local_workspace_layout.py`
