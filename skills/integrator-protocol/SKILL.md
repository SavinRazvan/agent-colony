---
name: integrator-protocol
description: Procedural integration of new agents, skills, MCP servers, and kit expansions into Agent Colony — templates, scripts, three-plane discipline.
---

# Integrator protocol

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Goal

Integrate **new agents, skills, MCP servers, scripts, or docs** for unpack + personal settings. Keep work procedural and deterministic.

**Canonical ops:** [mas-infrastructure-integration.md](../../.ai_infra/docs/operations/mas-infrastructure-integration.md) · **Agent:** `.cursor/agents/integrator.md`

## Evidence contract

**Universal canon:** `evidence-first` skill · [evidence-first.md](../../.ai_infra/docs/operations/evidence-first.md). Integrator-specific:

- Every claim cites **repo path** or **command output**.
- Not inspected → **Unknown**. No invented layout or gate behavior.

## Phase 0 — Intake

| Type | Examples | Outputs |
|------|----------|---------|
| **Agent** | `my-domain-agent.md` | `.cursor/agents/`, registry |
| **Skill** | `.cursor/skills/` or `.agents/skills/` | SKILL.md, plugin sync |
| **MCP** | GitHub, browser, DB | `mcp.user.json`, registry |
| **Infrastructure** | script, gate | `.ai_infra/`, manifest, tests |
| **Doc-only** | runbook | `.ai_infra/docs/` |

Ask: MAS-integrated vs independent (ADR-006)? Architecture/manifest touch → plan `auditor`. Consumer-visible → `manifest.yaml` + `install-contract.json`. **`consumer_lite` profile** → [consumer-lite-profile.md](../../.ai_infra/docs/operations/consumer-lite-profile.md). Research pack → read `AGENT_BRIEF.md`.

**Token-efficiency:** Do not duplicate gate lists in new docs — link `prepare.py` `resolve_gates()`.

## Phase 1 — Read base workflow

`workflow-architecture.md` · `agent-workflow-procedures.md` · `local-workspace-layout.md` · `github.collaboration.yaml` · similar agent/skill as template.

## Phase 2 — Templates

From `.ai_infra/templates/agent-integration/`:

| Template | Use |
|----------|-----|
| `AGENT.template.md` | `.cursor/agents/<id>.md` |
| `SKILL.template.md` | `.cursor/skills/<name>/` |
| `INTEGRATION-CHECKLIST.md` | Board card or `work-tracker.md` |

**Agent:** frontmatter; **Anchor**; **Read first**; **MCP integration**. Board SSOT when enabled; else `session-pointer.md`. Independent agents: omit pipelines unless PR phase owner.

## Phase 3 — Wire surfaces

### MAS-integrated

| Step | Action |
|------|--------|
| 1–2 | Agent + skill if non-trivial |
| 3–4 | `mcp.registry.yaml` + `mcp.agents.yaml` worksheet |
| 5 | `github.collaboration.yaml` pipeline if PR/slice |
| 6–7 | `manifest.yaml` / `install-contract.json`; `make sync-plugin` + `check-plugin` |
| 8 | `tests/modules/` if new scripts |

### Independent

Agent + skill with **boundaries**; optional scoped MCP; no core PR pipeline unless maintainer phase; document handoff when crossing kit infra.

### External MCP

[connect-external-mcp.md](../../.ai_infra/docs/operations/connect-external-mcp.md): `mcp.agents.yaml` row → `mcp.user.json` fragment → `mcp.registry.yaml` → `mcp validate`.

### Canvases / plans (ADR-010)

`.cursor/skills/canvas-artifacts/SKILL.md`. `.local/plans/` = snapshots only.

### Maintainer script

`.ai_infra/scripts/` only; never duplicate `GATES` outside `prepare.py`; file header on new Python; thin MCP wrapper in `agent_colony_mcp/server.py`.

## Phase 4 — Verify

```bash
python -m agent_colony contributors validate
python -m agent_colony integrate validate
python .ai_infra/scripts/architecture/check_governance_consistency.py   # if .cursor/ changed
pytest -q tests/modules/<relevant>/
make gates && make check-plugin    # if payload touched
make install-dry-run               # if manifest changed
```

Say *prepare gates green* or paste failing stderr. Record in `change-index.md` + `updates-log.md`.

## Phase 5 — Handoff

| Outcome | Next |
|---------|------|
| Product code / tests | `implementer` + `test-runner` |
| Architecture-impacting | `auditor` |
| Ready for PR | `review-pr` with `--pipeline` + `--agents-from-session` |

## Anti-patterns

Duplicate GATES in prose · agents without Anchor/MCP · skip `change-index.md` Agent column · `Made-with:` · load entire `.local/` · independent agents bypass governance.

## Exit criteria

- [ ] Type documented (MAS vs independent)
- [ ] Templates + file headers on new Python
- [ ] Registry/exemplars if MCP/pipelines touched
- [ ] Manifest if consumer tree changed
- [ ] Verify commands run; blockers logged
- [ ] Board Notes when `board_only`; `change-index.md` always
