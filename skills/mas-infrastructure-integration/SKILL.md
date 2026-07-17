---
name: mas-infrastructure-integration
description: Procedural integration of new agents, skills, MCP servers, and kit expansions into MAS Workflow Kit — templates, scripts, three-plane discipline.
---

# MAS infrastructure integration

## Goal

Integrate **new agents, skills, MCP servers, scripts, or docs** into the kit so the user gets the same **unpack + personal settings** experience: full consumer infrastructure from the plugin, human completes `.local/user_settings/`, everything else stays **procedural, deterministic, and enterprise-grade**.

**Canonical ops mirror:** `.ai_infra/docs/operations/mas-infrastructure-integration.md`

## When to use

- User adds a **new Cursor agent** or **skill**
- User connects an **external MCP server** for multiple agents
- User expands **manifest / install contract / plugin payload**
- User asks to merge a **standalone agent** into the MAS pipeline (or keep independent but governed)

**Agent card:** `.cursor/agents/integrator-mas-agent.md`

## Evidence contract

- Every integration claim cites a **repo path** or **command output**.
- If not inspected: label **Unknown** — do not invent file layout or gate behavior.
- No narrative without a checklist row or script result backing it.

---

## Phase 0 — Intake (classify)

| Type | Examples | Primary outputs |
|------|----------|-----------------|
| **Agent** | `my-domain-agent.md` | `.cursor/agents/`, registry, optional pipeline |
| **Skill** | `.cursor/skills/foo/` or `.agents/skills/` | SKILL.md, cross-links, plugin sync |
| **MCP external** | GitHub, browser, DB | `mcp.user.json`, registry, `mcp.agents.yaml` worksheet |
| **Infrastructure** | new script, gate, template dir | `.ai_infra/`, manifest, tests |
| **Doc-only** | runbook, charter | `.ai_infra/docs/` |

Ask (or infer from request):

1. **MAS-integrated** or **independent contract**? (see ADR-006: `.ai_infra/docs/decisions/ADR-006-agent-integration-model.md`)
2. Touches **architecture / manifest / workflows**? → plan `enterprise-auditor` before merge prep.
3. **Consumer-visible** (copied on install)? → update `manifest.yaml` + `install-contract.json`.

---

## Phase 1 — Read base workflow (do not skip)

Minimum read set:

1. `.ai_infra/docs/architecture/workflow-architecture.md` — three planes
2. `.ai_infra/docs/operations/agent-workflow-procedures.md` — Pattern A
3. `.ai_infra/docs/operations/local-workspace-layout.md` — `.local/` contract
4. `.local/user_settings/github.collaboration.yaml` — pipelines + attribution
5. Target area already in repo (similar agent/skill as template)

---

## Phase 2 — Apply templates

Copy and edit from **`.ai_infra/templates/agent-integration/`**:

| Template | Use |
|----------|-----|
| `AGENT.template.md` | New `.cursor/agents/<id>.md` |
| `SKILL.template.md` | New skill under `.cursor/skills/<name>/` |
| `INTEGRATION-CHECKLIST.md` | Track slice; attach to `work-tracker.md` |

**Agent file rules:**

- YAML frontmatter: `name`, `model`, `description`
- **Anchor** block (Entry/Exit) — same discipline as `implementer.md`
- **Read first** — bounded file set; no whole-repo loads
- **MCP integration** section — required (governance scanner)
- Procedural exits: update `session-pointer.md`, `change-index.md`

**Independent agent:** still includes Anchor + universal rules; omit from `github.collaboration.yaml` pipelines unless it participates in PR phases.

---

## Phase 3 — Wire integration surfaces

### A. MAS-integrated agent (multi-agent system)

| Step | Action |
|------|--------|
| 1 | Add `.cursor/agents/<id>.md` from template |
| 2 | Add skill if procedural steps are non-trivial |
| 3 | Update `.cursor/mcp.registry.yaml` (+ example): list agent under `workflow-kit` or external server |
| 4 | Update `.local/user_settings/mcp.agents.yaml` worksheet + exemplar under `templates/user-settings/` |
| 5 | Add to `github.collaboration.yaml` pipeline if it runs in PR/slice flow (or rely on `--agents-from-session` via `change-index`) |
| 6 | If consumer-installed: add paths to `manifest.yaml` / `install-contract.json` when new dirs ship |
| 7 | If marketplace: `make sync-plugin` + `make check-plugin` |
| 8 | Add tests under `tests/modules/` if new scripts |

### B. Independent agent (governed, not in MAS pipeline)

| Step | Action |
|------|--------|
| 1 | Agent + skill with explicit **boundaries** (what it must not do) |
| 2 | Registry: optional MCP servers scoped to that agent id only |
| 3 | **Do not** add to core PR pipelines unless it owns a maintainer phase |
| 4 | Document handoff to `implementer` / `integrator-mas-agent` when work crosses into kit infrastructure |

### C. External MCP server

Follow `.ai_infra/docs/operations/connect-external-mcp.md` plus:

1. Row in `.local/user_settings/mcp.agents.yaml`
2. Fragment in `.cursor/mcp.user.json` (gitignored)
3. Keys in `.cursor/mcp.registry.yaml` — `agents: [...]` per server
4. `python -m cursor_workflow mcp validate`

### D. New maintainer script

- Lives under `.ai_infra/scripts/` — never duplicate `GATES` outside `prepare.py`
- File header per `file-docstring-header-relations.mdc`
- Wire MCP tool in `workflow_mcp/server.py` only as thin wrapper (Pattern A)

---

## Phase 4 — Verify (commands, not prose)

Run applicable subset:

```bash
python -m cursor_workflow contributors validate
python -m cursor_workflow integrate validate
python .ai_infra/scripts/architecture/check_governance_consistency.py   # if .cursor/ or workflows changed
pytest -q tests/modules/<relevant>/
make gates                    # kit dev
make check-plugin             # if agents/rules/skills/payload touched
make install-dry-run          # if manifest / scaffold changed
python -m cursor_workflow health --directory .
```

Record PASS/FAIL in `change-index.md` and `updates-log.md`.

---

## Phase 5 — Handoff

| Outcome | Next agent |
|---------|------------|
| Needs product code / tests | `implementer` + `test-runner` |
| Architecture-impacting | `enterprise-auditor` → alignment artifacts |
| Ready for PR | maintainer `review-pr` with `--pipeline` + `--agents-from-session` |

---

## Anti-patterns (reject)

- Duplicating `prepare.py` GATES in skills or agent prose
- New agents without Anchor / MCP integration section
- Skipping `change-index.md` Agent column (breaks PR `--agents-from-session`)
- `Made-with:` or fake human sign-off in commits
- Loading entire `.local/` or megadocs when a checklist suffices
- Independent agents that bypass governance scripts

---

## Exit criteria

- [ ] Integration type documented (MAS vs independent)
- [ ] Templates filled; file headers present on new Python
- [ ] Registry / user_settings exemplars updated if MCP or pipelines affected
- [ ] Manifest + install-contract if consumer tree changed
- [ ] Verification commands run; failures fixed or logged as blockers
- [ ] `session-pointer.md` + `change-index.md` updated
