

# Cursor Agent Infrastructure Plugin — architecture

**Product:** installable **multi-agent workflow infrastructure** for any Cursor project (not a PyPI package, not an MCP-first product).

**User journey:** plugin unpacks the full **consumer infrastructure** → user completes `.local/user_settings/` (GitHub + MCP worksheets) → **`/integrator-mas-agent`** extends agents/skills/MCP while preserving Pattern A, gates, and three-plane layout.

**Optional add-on:** MCP server under `.ai_infra/mcp_servers/` — wraps the same scripts; agents do not require it.

**Expansion path:** after install, use **`/integrator-mas-agent`** to add agents/skills/MCP. Machine checks: `python -m cursor_workflow integrate validate` (P0: agent sections, registry parity, pipeline names, user_settings schema). ADR-006 defines MAS-integrated vs independent-governed modes.

---



## Three planes


| Plane           | Path                   | Cursor loads?                      |
| --------------- | ---------------------- | ---------------------------------- |
| Cursor contract | `.cursor/`, `.agents/` | Yes                                |
| Infrastructure  | `.ai_infra/`           | No — scripts and docs reference it |
| Runtime         | `.local/`              | No — gitignored per project        |

---

## Automated activation (three planes on disk)

Enabling the **Marketplace plugin** loads agents/rules/skills into Cursor, but **does not** copy infrastructure into the workspace until activation runs (ADR-001 Option B).

```mermaid
flowchart LR
  User[User enables plugin] --> Cursor[Cursor contract in IDE]
  Cursor --> Activate["cursor_workflow activate"]
  Activate --> P1["Plane 1: .cursor/ + .agents/"]
  Activate --> P2["Plane 2: .ai_infra/ + cursor_workflow/"]
  Activate --> P3["Plane 3: .local/ scaffold"]
  P3 --> Settings["User edits user_settings/ only"]
```

| Step | Who | Command |
|------|-----|---------|
| 1. Enable plugin | Human | Cursor Marketplace |
| 2. Activate planes | Agent or human | `python -m cursor_workflow activate --directory .` |
| 3. Personalize | Human | `.local/user_settings/github.collaboration.yaml` |
| 4. Validate | Agent or human | `contributors validate` + `integrate validate` |
| 5. Extend infra | Agent or human | **`/integrator-mas-agent`** in Agent chat (not shell) |

**Source for activate:** plugin `payload/` directory. Set `WORKFLOW_KIT_PAYLOAD=/path/to/payload` when auto-detect fails.

**Agents are not CLI commands.** Names like `integrator-mas-agent` are Cursor subagents — invoke with **`/integrator-mas-agent`** in Agent chat or via parent Agent Task delegation ([Subagents](https://cursor.com/docs/subagents)).

---



## Kit dev repo (where we build the plugin)

```text
mas-workflow-kit/
├── AGENTS.md
├── .cursor-plugin/plugin.json  # marketplace manifest — no path fields (spec-exact discovery)
├── agents/                     # generated (make sync-plugin) — COMMITTED, sibling of .cursor-plugin/
├── rules/                      # generated — COMMITTED
├── skills/                     # generated — COMMITTED
├── payload/                    # generated (ADR-001 install source) — COMMITTED
├── assets/logo.png
├── .cursor/                    # canonical dev source for agents/rules/skills above
├── .agents/                    # maintainer-only slash skills, merged into skills/
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

**`agents/`, `rules/`, `skills/`, `payload/` are generated but MUST be committed to git** — Cursor Marketplace reads the repository tree directly; there is no build step at install/review time. `make check-plugin` guards drift between `.cursor/` + `.agents/skills/` (source of truth) and these generated, committed trees. Layout matches [`cursor/plugin-template`](https://github.com/cursor/plugin-template) exactly: `agents/`, `rules/`, `skills/`, `commands/`, `hooks/`, `mcp.json` as direct siblings of `.cursor-plugin/`, discovered by convention — **no path-override fields** in `plugin.json` (the official validator's frontmatter walker ignores such fields even when present, so relying on them risks a false pass with zero components actually loaded).

---



## Installed consumer project (default profile)

```text
my-app/
├── AGENTS.md                 # thin router
├── .cursor/                  # agents, rules, skills
├── .agents/                  # maintainer slash skills
├── .ai_infra/                # slim infrastructure bundle
│   ├── manifest.yaml
│   ├── install-contract.json
│   ├── scripts/pr|architecture|integration|workflow|install/
│   ├── install/cursor_workflow/
│   ├── docs/operations|governance|roadmap|decisions|architecture/
│   ├── templates/local-workspace|user-settings|agent-integration/
│   ├── mcp_servers/workflow_mcp/   # with_mcp profile
│   └── workflows/
├── overlays/                 # product rules source (copy → .cursor/rules/)
└── .local/                   # scaffolded trackers
```

**Not installed by default:** kit full `tests/`, `Makefile`, `docs/handoff/`, CI/release scripts, maintainer megadocs under `docs/maintainer/`.

**Kit dev repo only (not in consumer** `.ai_infra/`**):** `scripts/ci/`, `scripts/release/`, `docs/handoff/`, root `Makefile`, full `tests/modules/`. Consumers use the slim bundle from `manifest.yaml` `copy_ai_infra` only.

### `ci/kit-dev` local workspace fixtures

The path `.ai_infra/templates/local-workspace/ci/kit-dev/` holds **kit-repository-only** tracker exemplars (e.g. full `test-index.md` with all `tests/modules/` owners). CI runs `[seed_kit_workspace.py](../../scripts/ci/seed_kit_workspace.py)` before gates because `.local/` is gitignored. **Consumers** receive neutral exemplars under `templates/local-workspace/exemplars/` — not the `ci/kit-dev/` tree. Do not reference `ci/kit-dev` paths in consumer onboarding docs.

---



## Install profiles (`manifest.yaml`)


| Profile    | Adds                                                                             |
| ---------- | -------------------------------------------------------------------------------- |
| `default`  | `.cursor/`, `.agents/`, slim `.ai_infra/`, `.local/` exemplars, `AGENTS.md` stub |
| `with_mcp` | `.ai_infra/mcp_servers/workflow_mcp/`, `requirements-mcp.txt`, `mcp.json`        |


Product rules: copy `overlays/rules/*.mdc` into `.cursor/rules/` after install (not a separate profile).

**Skill merge policy:**

| Tree | Skills source | Purpose |
|------|---------------|---------|
| `skills/` (repo root) | `.cursor/skills/` then additive merge from `.agents/skills/` | Cursor Marketplace loads slash skills from repo-root `skills/` |
| `payload/.cursor/skills/` | **Kit `.cursor/skills/` only** (no maintainer merge) | Consumer disk must not duplicate `.agents/skills/` folder names |
| `payload/.agents/skills/` | Kit `.agents/skills/` | Maintainer PR slash skills on consumer disk |

`sync_plugin_bundle.py` merges `.agents/skills/` into repo-root `skills/` only when the folder name is absent from `.cursor/skills/`. Canonical protocols must never be replaced by maintainer stubs. **Do not** copy merged `skills/` into `payload/.cursor/skills/` — governance `check_governance_consistency.py` fails on duplicate folder names.

---



## Pattern A (unchanged)

- Agents run **one script command** per maintainer action.
- `GATES` hardcoded in `.ai_infra/scripts/pr/prepare.py`.
- Canonical invoke: `python .ai_infra/scripts/pr/prepare.py …`

---



## Plugin vs MCP vs Marketplace


| Mechanism              | What it is                                                          |
| ---------------------- | ------------------------------------------------------------------- |
| **This plugin**        | File bundle installed per project via `cursor_workflow activate` or `install` |
| **MCP**                | Optional `.cursor/mcp.json` → `workflow_mcp` tools wrapping scripts |
| **Cursor Marketplace** | Future distribution channel for the same bundle                     |


Plugins ≠ MCP. This product is agent infrastructure; MCP is an optional wire.