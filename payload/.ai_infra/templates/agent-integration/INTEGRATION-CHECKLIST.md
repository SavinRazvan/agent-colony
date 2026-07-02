<!--
File: INTEGRATION-CHECKLIST.md
Path: .ai_infra/templates/agent-integration/INTEGRATION-CHECKLIST.md
Role: Slice checklist for integrator-mas-agent; copy row into work-tracker.md.
Used By:
 - .cursor/skills/mas-infrastructure-integration/SKILL.md
Depends On:
 - .ai_infra/templates/agent-integration/AGENT.template.md
Notes:
 - Facts only — tick with evidence path or command output.
-->

# Integration checklist — {{SLICE_ID}}

| Field | Value |
|-------|--------|
| **Type** | agent \| skill \| mcp \| script \| doc |
| **Mode** | MAS-integrated \| independent-governed |
| **Owner** | integrator-mas-agent |
| **Status** | planned \| in_progress \| done |

## Intake

- [ ] Classified integration type
- [ ] MAS-integrated vs independent decided
- [ ] Architecture-impacting? (→ enterprise-auditor if yes)

## Files

- [ ] Agent/skill from template (path: ___)
- [ ] File headers on new Python modules
- [ ] `mcp.registry.yaml` + `.example` updated (if MCP)
- [ ] `templates/user-settings/` exemplars updated (if attribution/MCP)
- [ ] `manifest.yaml` + `install-contract.json` (if consumer-visible)
- [ ] Plugin sync (`make sync-plugin`) if marketplace-facing

## Governance

- [ ] Anchor + MCP integration section on new agent
- [ ] No duplicated GATES in prose
- [ ] `change-index.md` Agent column updated

## Verify

- [ ] `python -m cursor_workflow contributors validate`
- [ ] `python .ai_infra/scripts/architecture/check_governance_consistency.py`
- [ ] `pytest -q tests/modules/___` (if applicable)
- [ ] `make install-dry-run` (if manifest/scaffold)
- [ ] `make check-plugin` (if agents/rules/skills/payload touched)

## Handoff

- [ ] `session-pointer.md` updated
- [ ] Next agent: ___
