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

Scaffold copies exemplars into `.local/index-and-planning/current/`, `pages.json` into `.local/agents-control-center/config/`, README stubs into `workflow-artifacts/*`, and optional dashboards.

| Template | Target |
|----------|--------|
| `exemplars/*.md` | `.local/index-and-planning/current/` |
| `exemplars/updates-log.md` | `.local/index-and-planning/history/updates-log.md` |
| `artifact-stubs/<bucket>/README.md` | `.local/workflow-artifacts/<bucket>/README.md` (if missing) |
| `pages.json` | `.local/agents-control-center/config/pages.json` |
| `index.html`, `implementation-control-center.html` | `.local/agents-control-center/dashboards/` (refresh every activate) |
| `site-nav.js`, `local-shell.css`, `local-markdown.js` | `.local/agents-control-center/dashboards/` (refresh every activate) |
| `audits/module-audit.html` | `.local/agents-control-center/audits/` (refresh every activate) |

> **Maintainer-only:** layout migration helper (`.ai_infra/scripts/dev/migrate_local_workspace_layout.py`) exists in the kit development repo only — not shipped to consumer installs.
