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

**Last updated:** 2026-06-30 (local artifact tiers scaffold)  
**Product:** MAS Workflow Kit (`mas-workflow-kit`) · CLI: `cursor-workflow` 0.3.0 · **Tests:** 116

## Shipped (confirmed in repo)

| Area | Status | Location |
|------|--------|----------|
| Universal rules | 6 `.mdc` | `.cursor/rules/` |
| Agents | 7 core; `model: auto`; audit agents write `.local/` artifacts only (no `readonly`) | `.cursor/agents/` |
| Canonical skills | 10 folders | `.cursor/skills/` |
| Maintainer skills | 5 folders (additive plugin merge) | `.agents/skills/` |
| Cursor skill merge | Canonical wins in plugin sync | `sync_plugin_bundle.py` |
| workflow-activate skill | Kit dev + plugin | `.cursor/skills/workflow-activate/` |
| PR scripts + prepare gates | Pattern A — **2** universal; **4** on kit-dev (drift + doc facts) | `.ai_infra/scripts/pr/prepare.py` |
| Governance + debrand scanners | CI-ready | `.ai_infra/scripts/architecture/` |
| Workflow drift validate | ADR-007 | `.ai_infra/scripts/workflow/check_drift.py` |
| Doc facts validate | DOC-001…005 | `.ai_infra/scripts/architecture/check_doc_facts.py` |
| Verify-all matrix | Maintainer preflight | `.ai_infra/scripts/architecture/verify_all.py` |
| Anchoring | session-pointer, change-index | `.local/.../current/` |
| MCP tools + resources | 19 tools + 6 resources | `.ai_infra/mcp_servers/workflow_mcp/` |
| Install scaffold + contract | `install-contract.json`; idempotent trackers/`AGENTS.md`/`pages.json` on re-activate | `.ai_infra/scripts/install/scaffold.py` |
| Local artifact tiers | Tier 1 scaffold: all `workflow-artifacts/*` buckets + README stubs; SSOT `local_workflow_paths.py` | `.ai_infra/templates/local-workspace/`, `pages.json` |
| Install CLI | install, **activate**, gates, health, mcp, drift, verify | `.ai_infra/install/cursor_workflow/cli.py` |
| Editable install | `pyproject.toml` — `pip install -e ".[dev,mcp]"` | repo root |
| Three-plane activate | Idempotent plugin consumer setup | `.ai_infra/install/cursor_workflow/activate_cli.py`, `plane_status.py` |
| User MCP registry | ADR-004 | `.cursor/mcp.registry.yaml.example`, `mcp_manage.py` |
| Marketplace plugin | ADR-001 Option B | `.cursor-plugin/`, `sync_plugin_bundle.py` |
| Kit version on install | `kit_version` 0.3.0 | `.ai_infra/manifest.yaml`, `.ai_infra/.kit-version` |
| Tests | 116 | `tests/modules/` |

## Verification commands

```bash
pip install -e ".[dev,mcp]"
make gates
make drift-validate
make doc-validate
make verify-all
make install-dry-run
make check-plugin
cursor-workflow activate --directory .
cursor-workflow health
cursor-workflow mcp validate
cursor-workflow drift validate
```

## Not yet shipped

| Item | Target |
|------|--------|
| PyPI publish (`cursor-workflow` on PyPI) | out of scope — editable install via `pyproject.toml` is shipped |

## Maintainer doc sync

When this file changes, skim-update related maintainer docs under `.ai_infra/docs/maintainer/` — do not full-rewrite megadocs per slice.
