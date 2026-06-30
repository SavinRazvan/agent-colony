# MAS Workflow Kit

Universal, installable **Multi-Agent System (MAS) workflow** infrastructure for Cursor — agents, skills, rules, PR scripts, `.local/` anchoring, and optional MCP. This repo is **not** a product application; it is infrastructure you install into any project.

**Quick install:** [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md)  
**Shipped state:** [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md)  
**Architecture:** [`.ai_infra/docs/architecture/workflow-architecture.md`](.ai_infra/docs/architecture/workflow-architecture.md)

---

## What you get

| Layer | Contents |
|-------|----------|
| **Agents** | `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `integrator-mas-agent`, `workflow-drift-guard`, optional `researcher` — see [`AGENTS.md`](AGENTS.md) |
| **Skills** | Implementation, test, audit protocols + maintainer PR slash commands |
| **Rules** | **6 universal** always-applied `.cursor/rules/*.mdc` |
| **Scripts** | `.ai_infra/scripts/pr/*` (review → prepare → merge) + governance checks |
| **`.local/`** | Gitignored operating workspace — trackers, PR artifacts, audits |
| **Overlays** | Per-project rules at install ([`overlays/`](overlays/README.md)) |
| **Config** | Optional [`.ai_infra/project.config.yaml.example`](.ai_infra/project.config.yaml.example) |
| **MCP** | Optional `.ai_infra/mcp_servers/workflow_mcp/` (`with_mcp` profile) |

---

## Pattern A — one script command per action

Agents run **one command** per maintainer action; the script runs gates internally.

```bash
python .ai_infra/scripts/pr/prepare.py --pr <id|url> --actor "<Your Name>" --agents "review-pr | prepare-pr"
```

**`GATES` in `.ai_infra/scripts/pr/prepare.py` is the single source of truth.** Skills and rules point to that file — they do not duplicate the command list.

### Default gates (universal — 2 only)

```python
GATES = [
    ["python", ".ai_infra/scripts/pr/check_testing_artifacts.py"],
    ["python", "-m", "pytest", "-q"],
]
```

Append product-specific gates **once** at install by editing `prepare.py`.

---

## Overlay model

Core ships **6 universal rules** only. Product policy lives in **`overlays/rules/*.mdc`** copied into the target `.cursor/rules/` at install.

```bash
cp overlays/rules/*.mdc /path/to/project/.cursor/rules/
```

See [`overlays/README.md`](overlays/README.md).

---

## `.local/` — agent anchoring

`.local/` is **gitignored** per project. Contract: [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) (**Artifact tiers**: Tier 1 base scaffold at install; Tier 2 runtime files during work).

| Read often | Write per phase |
|------------|-----------------|
| `.local/index-and-planning/current/session-pointer.md` | `change-index.md`, `history/updates-log.md` |
| `plan.md`, `work-tracker.md`, `test-plan.md`, `test-index.md` | `workflow-artifacts/*` via agents and PR scripts |

---

## Quick install

**Plugin / Marketplace (recommended):**

```bash
cd /path/to/your-project
python -m cursor_workflow activate --directory .
```

**Kit clone / advanced:**

```bash
python -m cursor_workflow install --target /path/to/your-project --with-venv --verify
python -m cursor_workflow gates
python -m cursor_workflow install --target /path/to/your-project --dry-run
```

Optional MCP: `python -m workflow_mcp` — see [`.cursor/mcp.json.kit.example`](.cursor/mcp.json.kit.example) and [connect-external-mcp](.ai_infra/docs/operations/connect-external-mcp.md).

Full path: [`.ai_infra/docs/operations/consumer-quickstart.md`](.ai_infra/docs/operations/consumer-quickstart.md).

---

## Agent routing

See [`AGENTS.md`](AGENTS.md). Maintainer PR: [`.agents/skills/pr-workflow/SKILL.md`](.agents/skills/pr-workflow/SKILL.md) → `review-pr` / `prepare-pr` / `merge-pr`.

---

## Verification

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,mcp]"
.venv/bin/python -m pytest -q
make gates
make doc-validate
make verify-all
.venv/bin/python .ai_infra/scripts/architecture/check_governance_consistency.py
.venv/bin/python .ai_infra/scripts/architecture/check_debrand.py
```

---

## What this repo is NOT

- Not a product application (`src/`, domain adapters, product strategy docs)
- Not a runtime YAML gate orchestrator for agents
- Not a copy-paste rename of another product repo

---

## License

Licensed under the **Apache License, Version 2.0**. See [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
