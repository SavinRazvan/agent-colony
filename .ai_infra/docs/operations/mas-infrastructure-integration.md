<!--
File: mas-infrastructure-integration.md
Path: .ai_infra/docs/operations/mas-infrastructure-integration.md
Role: Consumer-facing procedure for extending MAS Workflow Kit (agents, skills, MCP, scripts).
Used By:
 - .cursor/agents/integrator-mas-agent.md
 - .cursor/skills/mas-infrastructure-integration/SKILL.md
Depends On:
 - .ai_infra/docs/architecture/workflow-architecture.md
 - .ai_infra/docs/operations/agent-workflow-procedures.md
Notes:
 - Pattern A; scripts over prose; facts only.
-->

# MAS infrastructure integration

## Product model

1. **Plugin + activate** unpacks consumer infrastructure (agents, scripts, `.local/` skeleton, optional MCP).
2. **User completes** `.local/user_settings/` (GitHub collaboration + MCP worksheet).
3. **Integrator agent** extends the system when user adds agents, skills, or tools — without breaking planes or gates.

**Agent:** `.cursor/agents/integrator-mas-agent.md`  
**Skill:** `.cursor/skills/mas-infrastructure-integration/SKILL.md`

## Three planes (never mix)

| Plane | Path | Integration touch |
|-------|------|-------------------|
| Cursor contract | `.cursor/`, `.agents/` | Agents, skills, rules, MCP registry |
| Infrastructure | `.ai_infra/` | Scripts, manifest, templates, docs |
| Runtime | `.local/` | User settings, trackers, PR artifacts |

## Integration modes

See **ADR-006** (`.ai_infra/docs/decisions/ADR-006-agent-integration-model.md`) for the canonical MAS-integrated vs independent-governed decision.

### MAS-integrated

Agent participates in slice/PR workflow, trackers, and optionally MCP registry pipelines.

- Must use **Anchor** entry/exit (session-pointer, change-index).
- Log **Agent** column in `change-index.md` — feeds PR `--agents-from-session`.
- Prefer **kit MCP** tools over re-running shell.

### Independent (governed)

Standalone agent for a narrow domain; not in default PR pipelines.

- Still obeys universal `.cursor/rules/*`.
- Still uses script commands for any maintainer action it performs.
- Document explicit handoff when work touches kit infrastructure.

## Quick checklist (new agent)

1. Copy `.ai_infra/templates/agent-integration/AGENT.template.md` → `.cursor/agents/<id>.md`
2. Add skill if steps are repeatable → `.cursor/skills/<name>/SKILL.md`
3. Update `.cursor/mcp.registry.yaml` (+ `.example`)
4. Update exemplars: `templates/user-settings/mcp.agents.yaml`, `github.collaboration.yaml` if pipeline-related
5. If shipped to consumers: `manifest.yaml`, `install-contract.json`, `make sync-plugin`
6. Verify: `python -m cursor_workflow integrate validate`, `contributors validate`, `check_governance_consistency.py`, targeted `pytest`

Full checklist: `.ai_infra/templates/agent-integration/INTEGRATION-CHECKLIST.md`

## Verification (deterministic)

| Change | Minimum commands |
|--------|------------------|
| Agent/skill only | `integrate validate`, `check_governance_consistency.py` |
| User settings / pipelines | `python -m cursor_workflow contributors validate` |
| Manifest / scaffold | `make install-dry-run` |
| Plugin bundle | `make sync-plugin` && `make check-plugin` |
| PR-ready slice | `make gates` or `prepare.py` GATES |

## Escalation

| Need | Agent |
|------|--------|
| Architecture audit | `enterprise-auditor` |
| Tests | `test-runner` |
| Application code | `implementer` |
| Merge | `review-pr` → `prepare-pr` → `merge-pr` |

See also: [connect-external-mcp.md](connect-external-mcp.md), [local-workspace-layout.md](local-workspace-layout.md), [gate-matrix.md](gate-matrix.md).
