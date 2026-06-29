<!--
File: IMPLEMENTATION-STATUS.md
Path: .ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md
Role: Shipped vs spec — single source when maintainer megadocs lag the repo.
Used By:
 - README.md
 - enterprise-auditor alignment passes
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/mcp_servers/workflow_mcp/
 - .ai_infra/scripts/install/scaffold.py
Notes:
 - Update this file each material slice; do not rewrite full maintainer megadocs for every change.
-->

# Implementation status (MAS Workflow Kit)

**Last updated:** 2026-06-29 (doc-facts automation slice)  
**Product:** MAS Workflow Kit (`mas-workflow-kit`) · CLI: `cursor-workflow` 0.3.0 · **Tests:** 85

## Shipped (confirmed in repo)

| Area | Status | Location |
|------|--------|----------|
| Universal rules | 6 `.mdc` | `.cursor/rules/` |
| Agents | 7 core (incl. workflow-drift-guard) | `.cursor/agents/` |
| PR scripts + 2 default gates | Pattern A | `.ai_infra/scripts/pr/prepare.py` |
| Governance + debrand scanners | CI-ready | `.ai_infra/scripts/architecture/` |
| Workflow drift validate | ADR-007 | `.ai_infra/scripts/workflow/check_drift.py` |
| Doc facts validate | DOC-001…005 | `.ai_infra/scripts/architecture/check_doc_facts.py` |
| Verify-all matrix | Maintainer preflight | `.ai_infra/scripts/architecture/verify_all.py` |
| Anchoring | session-pointer, change-index | `.local/.../current/` |
| MCP tools + resources | P0 + P1 | `.ai_infra/mcp_servers/workflow_mcp/` |
| Install scaffold + contract | `install-contract.json` | `.ai_infra/scripts/install/scaffold.py` |
| Install CLI | install, gates, health, mcp, drift | `.ai_infra/install/cursor_workflow/cli.py` |
| User MCP registry | ADR-004 | `.cursor/mcp.registry.yaml.example`, `mcp_manage.py` |
| Marketplace plugin | ADR-001 Option B | `.cursor-plugin/`, `sync_plugin_bundle.py` |
| Kit version on install | `kit_version` 0.3.0 | `.ai_infra/manifest.yaml`, `.ai_infra/.kit-version` |
| Tests | 85 | `tests/modules/` |

## Verification commands

```bash
make gates
make drift-validate
make doc-validate
make verify-all
make install-dry-run
make check-plugin
cursor-workflow health
cursor-workflow mcp validate
cursor-workflow drift validate
```

## Not yet shipped

| Item | Target |
|------|--------|
| PyPI `cursor-workflow` package | out of scope |

## Maintainer doc sync

When this file changes, skim-update related maintainer docs under `.ai_infra/docs/maintainer/` — do not full-rewrite megadocs per slice.
