<!--
File: PLUGIN-ARCHITECTURE.md
Path: .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
Role: Product architecture — Cursor Agent Infrastructure Plugin vs optional MCP.
Used By:
 - README.md
 - consumer-quickstart.md
 - REFACTOR plan phases
Depends On:
 - .ai_infra/manifest.yaml
Notes:
 - Kit dev repo vs installed consumer tree; Pattern A unchanged.
-->

# Cursor Agent Infrastructure Plugin — architecture

**Product:** installable **multi-agent workflow infrastructure** for any Cursor project (not a PyPI package, not an MCP-first product).

**User journey:** plugin unpacks the full **consumer infrastructure** → user completes **`.local/user_settings/`** (GitHub + MCP worksheets) → **`integrator-mas-agent`** extends agents/skills/MCP while preserving Pattern A, gates, and three-plane layout.

**Optional add-on:** MCP server under `.ai_infra/mcp_servers/` — wraps the same scripts; agents do not require it.

**Expansion path:** after install, use **`integrator-mas-agent`** to add agents/skills/MCP. Machine checks: `python -m cursor_workflow integrate validate` (P0: agent sections, registry parity, pipeline names, user_settings schema). ADR-006 defines MAS-integrated vs independent-governed modes.

---

## Three planes

| Plane | Path | Cursor loads? |
|-------|------|---------------|
| Cursor contract | `.cursor/`, `.agents/` | Yes |
| Infrastructure | `.ai_infra/` | No — scripts and docs reference it |
| Runtime | `.local/` | No — gitignored per project |

---

## Kit dev repo (where we build the plugin)

```text
mas-workflow-kit/
├── AGENTS.md
├── .cursor/
├── .agents/
├── .ai_infra/              # canonical product tree
│   ├── manifest.yaml
│   ├── paths.py
│   ├── scripts/
│   ├── docs/
│   ├── templates/
│   ├── mcp_servers/        # optional workflow_mcp
│   └── install/cursor_workflow/
├── .local/
├── Makefile
├── pytest.ini
└── tests/
```

Maintainer megadocs live under `.ai_infra/docs/maintainer/` (not copied to consumers).

---

## Installed consumer project (default profile)

```text
my-app/
├── AGENTS.md                 # thin router
├── .cursor/                  # agents, rules, skills
├── .agents/                  # maintainer slash skills
├── .ai_infra/                # slim infrastructure bundle
│   ├── manifest.yaml
│   ├── scripts/pr/
│   ├── scripts/architecture/
│   ├── docs/operations/      # agent-facing ops docs only
│   ├── templates/local-workspace/
│   └── project.config.yaml.example
├── overlays/                 # product rules source (copy → .cursor/rules/)
└── .local/                   # scaffolded trackers
```

**Not installed by default:** kit `tests/`, full `governance/`, product release scripts, maintainer megadocs.

**Kit dev repo only (not in consumer `.ai_infra/`):** `scripts/ci/`, `scripts/release/`, `docs/handoff/`, root `Makefile`, full `tests/modules/`. Consumers use the slim bundle from `manifest.yaml` `copy_ai_infra` only.

### `ci/kit-dev` local workspace fixtures

The path `.ai_infra/templates/local-workspace/ci/kit-dev/` holds **kit-repository-only** tracker exemplars (e.g. full `test-index.md` with all `tests/modules/` owners). CI runs [`seed_kit_workspace.py`](../../scripts/ci/seed_kit_workspace.py) before gates because `.local/` is gitignored. **Consumers** receive neutral exemplars under `templates/local-workspace/exemplars/` — not the `ci/kit-dev/` tree. Do not reference `ci/kit-dev` paths in consumer onboarding docs.

---

## Install profiles (`manifest.yaml`)

| Profile | Adds |
|---------|------|
| `default` | `.cursor/`, `.agents/`, slim `.ai_infra/`, `.local/` exemplars, `AGENTS.md` stub |
| `with_mcp` | `.ai_infra/mcp_servers/workflow_mcp/`, `requirements-mcp.txt`, `mcp.json` |

Product rules: copy `overlays/rules/*.mdc` into `.cursor/rules/` after install (not a separate profile).

---

## Pattern A (unchanged)

- Agents run **one script command** per maintainer action.
- `GATES` hardcoded in `.ai_infra/scripts/pr/prepare.py`.
- Canonical invoke: `python .ai_infra/scripts/pr/prepare.py …`

---

## Plugin vs MCP vs Marketplace

| Mechanism | What it is |
|-----------|------------|
| **This plugin** | File bundle installed per project via `cursor_workflow install` |
| **MCP** | Optional `.cursor/mcp.json` → `workflow_mcp` tools wrapping scripts |
| **Cursor Marketplace** | Future distribution channel for the same bundle |

Plugins ≠ MCP. This product is agent infrastructure; MCP is an optional wire.
