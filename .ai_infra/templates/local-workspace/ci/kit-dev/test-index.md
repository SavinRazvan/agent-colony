# Test Index

## Format

- Module: `<source module or area>`
- Owned tests: `<tests/... paths>`
- Coverage status: `healthy | partial | gap`
- Notes: cleanup tasks, migration notes

## Current index

- Module: `pr_workflow`
  - Owned tests: `tests/modules/pr_workflow/test_pr_workflow_scripts.py`, `tests/modules/pr_workflow/test_user_settings.py`, `tests/modules/pr_workflow/test_user_settings_schemas.py`
  - Coverage status: `healthy`
  - Notes: PR script attribution + verify_publish smoke

- Module: `architecture_scripts`
  - Owned tests: `tests/modules/architecture_scripts/test_check_governance_consistency.py`, `tests/modules/architecture_scripts/test_check_debrand.py`, `tests/modules/architecture_scripts/test_path_drift_ban.py`, `tests/modules/architecture_scripts/test_check_doc_facts.py`
  - Coverage status: `healthy`
  - Notes: governance, debrand, path-drift, doc-facts scanners

- Module: `agent_colony_mcp`
  - Owned tests: `tests/modules/agent_colony_mcp/test_agent_colony_mcp.py`
  - Coverage status: `healthy`
  - Notes: MCP tools and tracker read

- Module: `install`
  - Owned tests: `tests/modules/install/test_scaffold.py`, `tests/modules/install/test_install_contract.py`, `tests/modules/install/test_agent_colony.py`, `tests/modules/install/test_plane_status.py`
  - Coverage status: `healthy`
  - Notes: scaffold, install contract, CLI, three-plane activate

- Module: `ai_infra`
  - Owned tests: `tests/modules/ai_infra/test_paths.py`
  - Coverage status: `healthy`
  - Notes: paths resolver

- Module: `release`
  - Owned tests: `tests/modules/release/test_sync_plugin_bundle.py`
  - Coverage status: `healthy`
  - Notes: agents/rules/skills + payload sync (committed bundle)

- Module: `mcp_registry`
  - Owned tests: `tests/modules/mcp_registry/test_*.py`
  - Coverage status: `healthy`
  - Notes: schema, merge, validate CLI

- Module: `integration`
  - Owned tests: `tests/modules/integration/test_integrate_validate.py`
  - Coverage status: `healthy`
  - Notes: integrate validate P0 checks

- Module: `workflow_drift`
  - Owned tests: `tests/modules/workflow_drift/test_drift_checks.py`, `tests/modules/workflow_drift/test_drift_cli.py`
  - Coverage status: `healthy`
  - Notes: DRIFT-001-008 and CLI wiring

- Module: `ci`
  - Owned tests: `tests/modules/ci/test_seed_kit_workspace.py`
  - Coverage status: `healthy`
  - Notes: CI workspace seed
