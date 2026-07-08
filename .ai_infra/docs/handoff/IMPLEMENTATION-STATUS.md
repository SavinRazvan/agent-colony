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

**Last updated:** 2026-07-08 (DRIFT-005 consumer skip + coverage branch test)  
**Product:** MAS Workflow Kit (`mas-workflow-kit`) · CLI: `cursor-workflow` 0.4.0 · **Tests:** 633

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
| Doc facts validate | DOC-001…006 | `.ai_infra/scripts/architecture/check_doc_facts.py` |
| Verify-all matrix | Maintainer preflight | `.ai_infra/scripts/architecture/verify_all.py` |
| Anchoring | session-pointer, change-index | `.local/.../current/` |
| MCP tools + resources | 20 tools + 6 resources | `.ai_infra/mcp_servers/workflow_mcp/` |
| Install scaffold + contract | `install-contract.json`; idempotent trackers/`AGENTS.md`/`pages.json` on re-activate | `.ai_infra/scripts/install/scaffold.py` |
| Local artifact tiers | Tier 1 scaffold: all `workflow-artifacts/*` buckets + README stubs; SSOT `local_workflow_paths.py` | `.ai_infra/templates/local-workspace/`, `pages.json` |
| Integrate validate | INT-001…014; INT-009/011 plugin parity **kit-dev only** | `.ai_infra/scripts/integration/validate.py` |
| Install CLI | install, **activate**, gates, health, mcp, contributors, integrate, drift, doc, verify | `.ai_infra/install/cursor_workflow/cli.py` |
| Editable install | `pyproject.toml` — `pip install -e ".[dev,mcp]"` | repo root |
| Three-plane activate | Idempotent plugin consumer setup | `.ai_infra/install/cursor_workflow/activate_cli.py`, `plane_status.py` |
| User MCP registry | ADR-004 | `.cursor/mcp.registry.yaml.example`, `mcp_manage.py` |
| Marketplace plugin | ADR-001 Option B | `.cursor-plugin/`, `sync_plugin_bundle.py` |
| Kit version on install | `kit_version` 0.4.0 | `.ai_infra/manifest.yaml`, `.ai_infra/.kit-version` |
| Tests | 633 | `tests/modules/` |

## Coverage scope (shipped source)

`pytest --cov=.ai_infra --cov=cursor_workflow` measures the **import surface** of the
installable kit (CLI, scripts invoked in-process, MCP server). As of 2026-07-08: **44 files,
3588 statements, 100%** when the full suite passes (`generate_coverage_index.py` and
`migrate_local_workspace_layout.py` are maintainer tooling — omitted from `--cov` per
`pyproject.toml`). Subprocess-only maintainer scanners
(`check_governance_consistency.py`, `check_debrand.py`, `check_consumer_purity.py`,
`check_file_headers.py`) have dedicated module tests but are excluded from this metric by
design — they are launched via `subprocess` / `make gates`, not imported by the coverage
run. Running `--cov=.` (tests included) reports ~99% because of order-dependent branches in
test-helper cleanup code; scope shipped source for marketplace readiness claims.

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
pytest -m live tests/modules/workflow_mcp/test_workflow_mcp.py::test_workflow_mcp_stdio_initialize_smoke
cursor-workflow drift validate
```

## Not yet shipped

| Item | Target |
|------|--------|
| PyPI publish (`cursor-workflow` on PyPI) | out of scope — editable install via `pyproject.toml` is shipped |

## Maintainer doc sync

When this file changes, skim-update related maintainer docs under `.ai_infra/docs/maintainer/` — do not full-rewrite megadocs per slice.
