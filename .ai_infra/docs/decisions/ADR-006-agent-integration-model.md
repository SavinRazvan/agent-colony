# ADR-006: Agent integration model (MAS-integrated vs independent-governed)

**Status:** accepted  
**Date:** 2026-06-14

## Context

Consumers extend the MAS Workflow Kit by adding agents, skills, MCP servers, and scripts. Without a clear integration contract, new capability drifts from gates, PR pipelines, registry parity, and procedural discipline.

The **integrator-mas-agent** and **mas-infrastructure-integration** skill proceduralize extension; this ADR records the architectural decision.

## Decision

Two integration modes:

### MAS-integrated

Agent participates in the multi-agent slice and PR workflow.

| Requirement | Detail |
|-------------|--------|
| Agent file | `.cursor/agents/<id>.md` with **Anchor**, **MCP integration** |
| Trackers | Log `Agent` in `change-index.md`; update `session-pointer.md` |
| MCP registry | Listed under appropriate server in `.cursor/mcp.registry.yaml` (+ `.example`) |
| Pipelines | Optional entry in `.local/user_settings/github.collaboration.yaml` `pr_collaboration.pipelines` |
| Exemplars | Update `templates/user-settings/exemplars/` when pipeline-related |
| Ship set | `manifest.yaml`, `install-contract.json`, `make sync-plugin` when consumer-facing |
| Verify | `integrate validate`, `contributors validate`, targeted `pytest` |

### Independent-governed

Standalone agent for a narrow domain; not in default PR pipelines unless explicitly added.

| Requirement | Detail |
|-------------|--------|
| Agent file | Same Anchor + MCP block; universal `.cursor/rules/*` apply |
| Pipelines | **Not** added to default pipelines unless user opts in |
| Registry | Optional registry slot for MCP tools |
| Handoff | Document when work touches kit infrastructure → invoke integrator |

## Decision criteria

| Choose MAS-integrated when | Choose independent-governed when |
|-----------------------------|--------------------------------|
| Agent runs during normal slices / PR phases | Agent is ad-hoc or external-only |
| Work updates trackers, gates, or manifest | Work is read-only or single-shot |
| Agent id should appear in PR `Agent/s` | Agent should not appear in PR attribution |
| Multiple agents coordinate on same slice | Single-purpose tool with no PR coupling,
| Examples: implementer, integrator-mas-agent, enterprise-auditor | Examples: one-off research, external-only automation |

## Consequences

- **`integrate validate`** enforces P0 parity (agent sections, registry ↔ files, pipeline names, user_settings schema).
- **ADR index** updated in [README.md](README.md).
- Ops mirror: [mas-infrastructure-integration.md](../operations/mas-infrastructure-integration.md).
- Skill decision tree references this ADR.

## References

- `.cursor/agents/integrator-mas-agent.md`
- `.cursor/skills/mas-infrastructure-integration/SKILL.md`
- `.ai_infra/templates/agent-integration/INTEGRATION-CHECKLIST.md`
