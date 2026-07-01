<!--
File: consumer-quickstart.md
Path: .ai_infra/docs/operations/consumer-quickstart.md
Role: Five-minute install path for adopting the kit in a new or existing project.
Used By:
 - README.md
 - IMPLEMENTATION-STATUS.md document map
Depends On:
 - .ai_infra/install/cursor_workflow/cli.py
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/docs/operations/project-config.md
Notes:
 - Pattern A: agents call scripts; GATES live in prepare.py only.
-->

# Consumer quickstart (< 5 minutes)

Adopt the **MAS Workflow Kit** in a fresh directory or existing repo. No git remote required for local validation.

**Architecture overview:** [`.ai_infra/docs/architecture/workflow-architecture.md`](../architecture/workflow-architecture.md) (shipped with install).

---

## Before you start — do and don't

| Do | Don't |
|----|-------|
| Open **your app project** in Cursor | Use `mas-workflow-kit` as your day-to-day workspace |
| Run **`workflow-activate`** in chat (recommended) | Run `make sync-plugin`, `make smoke-consumer`, or `make gates` — **kit-dev only** |
| Use a **real path** you created (e.g. `~/Projects/my-app`) | Copy `/path/to/your-project` literally |
| Run CLI commands **from your project** after activate | Run `activate --directory .` while cwd is the kit repo |

---

## Marketplace path (recommended)

1. **Cursor → Marketplace** → search **MAS Workflow Kit** → Install.  
   (Pre-launch: `/add-plugin` → kit repo root with `.cursor-plugin/plugin.json`.)
2. Open your **target project** in Cursor (**not** the kit repo).
3. Run skill **`workflow-activate`** in chat (runs `python3 -m cursor_workflow activate --directory .` with profile **`with_mcp`**).

**Terminal — pre-launch dogfood only** (skip when chat activate works):

```bash
export KIT=~/Projects/mas-workflow-kit
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" --source "$KIT/payload"
cd "$TARGET"
```

4. Edit `.local/user_settings/github.collaboration.yaml` → `python3 -m cursor_workflow contributors validate`.
5. `python3 -m cursor_workflow integrate validate` (expect P0 = 0).
6. `python3 -m cursor_workflow gates`

**Add agents/skills/MCP later:** @ **`integrator-mas-agent`** + skill **`mas-infrastructure-integration`** → `integrate validate`.

---

## Kit clone path (advanced)

Use when installing without the plugin UI. Requires cloning **mas-workflow-kit** once.

### Prerequisites

| Need | Notes |
|------|--------|
| Python 3.11+ | `python3 --version` |
| Kit source | Clone repo or use generated `payload/` after `make sync-plugin` |
| Cursor IDE | For agents, rules, optional MCP |

From the **kit repo root**:

```bash
git clone https://github.com/SavinRazvan/mas-workflow-kit.git
cd mas-workflow-kit
python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt
```

### Preview (optional)

```bash
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" \
  --dry-run
```

Confirm the copy plan lists `.cursor/`, `.agents/`, `.ai_infra/`, `AGENTS.md`, and `.ai_infra/project.config.yaml.example`.

### Install

```bash
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"

.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" \
  --with-venv \
  --with-mcp-json \
  --verify

cd "$TARGET"
```

**What install / activate does**

- Copies **three planes**: `.cursor/` + `.agents/`, `.ai_infra/` + `cursor_workflow/`, `.local/` Tier 1 scaffold
- Writes **`AGENTS.md`** from kit stub (first install only; not overwritten on re-activate)
- Creates six **`workflow-artifacts/*`** buckets with README stubs (Tier 1); runtime `.md` files appear on first use (Tier 2)
- Writes `.ai_infra/.kit-version` (currently **0.3.0** from manifest)
- Scaffolds `tests/modules/smoke/test_kit_installed.py` (not the full kit `tests/` tree)
- Merges `.cursor/mcp.json` from kit example (+ optional `mcp.user.json`)
- Creates `.venv` and runs verify gates (4 checks: artifacts + pytest + governance + debrand)

**Kit dev only:** `--with-tests` copies the full kit `tests/` tree.

---

## Customize once (~1 min)

**Artifact tiers:** Tier 1 base at install; Tier 2 runtime under `workflow-artifacts/` during work. See [local-workspace-layout.md](local-workspace-layout.md) § Artifact tiers.

```bash
cd ~/Projects/my-app   # your activated project

cp .ai_infra/project.config.yaml.example project.config.yaml   # optional

# Personal settings — replace placeholders:
#   .local/user_settings/github.collaboration.yaml
#   .local/user_settings/mcp.agents.yaml

python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow integrate validate

# Optional external MCP:
cp .cursor/mcp.registry.yaml.example .cursor/mcp.registry.yaml
cp .cursor/mcp.user.example.json .cursor/mcp.user.json
python3 -m cursor_workflow mcp validate
```

**Extend infrastructure later:** @ **`integrator-mas-agent`** + skill **`mas-infrastructure-integration`** — see [mas-infrastructure-integration.md](mas-infrastructure-integration.md), ADR-006.

Product overlay rules (from kit repo at install time): `cp overlays/rules/*.mdc .cursor/rules/`.

---

## Verify (~1 min)

**From your activated project** (preferred):

```bash
python3 -m cursor_workflow gates
python3 -m cursor_workflow health
python3 -m cursor_workflow integrate validate
python3 -m cursor_workflow mcp validate    # after registry setup
```

**From kit repo** (alternative — pass target explicitly):

```bash
.venv/bin/python -m cursor_workflow gates --directory "$TARGET"
.venv/bin/python -m cursor_workflow health --directory "$TARGET"
```

Expected: testing-artifact PASS, pytest green, governance PASS, debrand PASS; doc facts auto-skipped on consumer (`DOC-000`).

Gate surfaces: [gate-matrix.md](gate-matrix.md) — prepare **2** universal; scaffold verify **4**; kit-dev `make gates` **5**.

---

## Cursor setup

1. Open your project folder in Cursor.
2. Agents: `.cursor/agents/` (7); rules: `.cursor/rules/` (6 universal).
3. **MCP:** merged `.cursor/mcp.json` from activate (profile `with_mcp`). External servers: [connect-external-mcp.md](connect-external-mcp.md).
4. Start a slice: `.local/index-and-planning/current/session-pointer.md` → `plan.md`.

### Subagent model (cost control)

Kit agent cards use **`model: auto`** in frontmatter.

**Built-in Cursor subagents** (`explore`, `bash`, `browser`) are **not** in the repo. Configure in **Cursor → Settings → Agents → Subagents** — **Auto** recommended for Explore.

Repo subagents load from `.cursor/agents/` after install or plugin activate.

Maintainer PR flow: `.agents/skills/pr-workflow/SKILL.md`.

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pytest` not found | Re-run activate/install with venv (default on `with_mcp`) |
| `contributors validate` FAIL | Replace placeholders in `github.collaboration.yaml` |
| `integrate validate` P2 on `plugin/agents/` | Fixed in kit ≥ 0.3.0 — consumer skips plugin parity; upgrade or ignore if P0 = 0 |
| `mcp validate` fails | Registry server keys must exist in merged `mcp.json` |
| Governance warns on CI | Normal when `.github/` absent in greenfield consumer |

Deep checklist: [install-dry-run.md](install-dry-run.md). Upgrade: [upgrade-kit.md](upgrade-kit.md).

---

## Installed consumer tree (default)

```text
your-project/
├── AGENTS.md
├── .cursor/          agents (7), skills (10), rules (6), mcp.json
├── .agents/skills/   pr-workflow, review-pr, prepare-pr, merge-pr
├── .ai_infra/        scripts, docs, manifest, .kit-version
├── .local/           gitignored — Tier 1 trackers + workflow-artifacts buckets
├── cursor_workflow/  python3 -m cursor_workflow
└── tests/modules/smoke/test_kit_installed.py
```

**Ongoing CLI:** run **`python3 -m cursor_workflow`** from the consumer project, or from kit/payload with `--directory "$TARGET"`.

**Pattern A:** one script command per agent action. `GATES` in `.ai_infra/scripts/pr/prepare.py` — **2** universal on consumer projects.
