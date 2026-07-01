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
3. Run skill **`workflow-activate`** in chat.

**Terminal — pre-launch dogfood only** (skip if Marketplace + chat activate work):

```bash
export KIT=~/Projects/mas-workflow-kit
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" --source "$KIT/payload"
cd "$TARGET"
```

4. Edit `.local/user_settings/github.collaboration.yaml` → `python3 -m cursor_workflow contributors validate`.
5. `python3 -m cursor_workflow gates`

**Add agents/skills/MCP later:** @ **`integrator-mas-agent`** + skill **`mas-infrastructure-integration`** → `integrate validate`.

---

## 0. Prerequisites

| Need | Notes |
|------|--------|
| Python 3.11+ | `python3 --version` |
| Kit source | Clone **mas-workflow-kit** locally (or use plugin `payload/`) |
| Cursor IDE | For agents, rules, optional MCP |

From the **kit repo root**, create a venv once:

```bash
python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt
```

---

## 1. Preview (optional, ~30 s)

```bash
.venv/bin/python -m cursor_workflow install \
  --target /tmp/my-project \
  --dry-run
```

Confirm the copy plan lists `.cursor/`, `.ai_infra/`, `AGENTS.md`, and `.ai_infra/project.config.yaml.example`.

---

## 2. Install (~2 min)

**Plugin / Marketplace (recommended):**

```bash
cd /path/to/your-project
python3 -m cursor_workflow activate --directory .
# Or from kit repo venv: .venv/bin/python -m cursor_workflow activate --directory .
```

One command installs all **three planes** (`.cursor/` + `.agents/`, `.ai_infra/`, `.local/`). Then edit settings only — see §3.

**Kit clone / advanced:**

```bash
TARGET=/path/to/your-project

.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" \
  --with-venv \
  --with-mcp-json \
  --verify
```

**What this does**

- Copies agents, skills, rules, slim `.ai_infra/`, exemplar `.local/` trackers, **`AGENTS.md`** (from kit stub, first install only)
- Creates all `workflow-artifacts/*` buckets with README stubs (Tier 1 base); runtime `.md` files appear on first use (Tier 2)
- Writes `.ai_infra/.kit-version` (semver from manifest)
- Scaffolds minimal `tests/modules/smoke/test_kit_installed.py` (not full kit `tests/`)
- Merges `.cursor/mcp.json` from `mcp.json.kit.example` (+ optional `mcp.user.json`)
- Creates `.venv` and runs verify gates (artifacts + pytest + governance + debrand)

**Kit dev only:** `--with-tests` copies the full kit `tests/` tree.

**Marketplace / plugin:** see `workflow-activate` skill — `python3 -m cursor_workflow activate --directory .` (uses plugin `payload/` as source; kit dev: `.venv/bin/python -m cursor_workflow activate …`).

---

## 3. Customize once (~1 min)

**What `.local` contains:** Tier 1 base artifacts (neutral trackers + empty artifact buckets) from install; Tier 2 runtime files (PR review/prep/merge, drift, alignment, audits) filled during work. See [local-workspace-layout.md](local-workspace-layout.md) § Artifact tiers.

```bash
cd "$TARGET"
cp .ai_infra/project.config.yaml.example project.config.yaml
# Personal settings (GitHub + MCP worksheets — edit placeholders):
#   .local/user_settings/github.collaboration.yaml
#   .local/user_settings/mcp.agents.yaml
python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow integrate validate
# Optional external MCP:
cp .cursor/mcp.registry.yaml.example .cursor/mcp.registry.yaml
cp .cursor/mcp.user.example.json .cursor/mcp.user.json
```

**Extend infrastructure later:** use agent **`integrator-mas-agent`** + skill **`mas-infrastructure-integration`** (see `.ai_infra/docs/operations/mas-infrastructure-integration.md`, ADR-006).

Product overlay: `cp overlays/rules/*.mdc .cursor/rules/` (from kit repo).

---

## 4. Verify (~1 min)

From **kit repo** (consumer has no `cursor_workflow` shim unless installed via plugin payload):

```bash
.venv/bin/python -m cursor_workflow gates --directory "$TARGET"
.venv/bin/python -m cursor_workflow health --directory "$TARGET"
.venv/bin/python -m cursor_workflow integrate validate --directory "$TARGET"
.venv/bin/python -m cursor_workflow mcp validate --directory "$TARGET"  # after registry setup
```

Expected: testing-artifact PASS, pytest green, governance PASS, debrand PASS.

---

## 5. Cursor setup

1. Open `$TARGET` in Cursor.
2. Agents: `.cursor/agents/`; rules: `.cursor/rules/`.
3. **MCP:** merged `.cursor/mcp.json` from `--with-mcp-json`. Kit fragment: `.cursor/mcp.json.kit.example`. External servers: [connect-external-mcp.md](connect-external-mcp.md).
4. Start a slice: `.local/index-and-planning/current/session-pointer.md` → `plan.md`.

### Subagent model (cost control)

Kit agent cards use **`model: auto`** in frontmatter (Auto + Composer pool — avoids inheriting parent Composer fast routing).

**Built-in Cursor subagents** (`explore`, `bash`, `browser`) are **not** in the repo. Configure in **Cursor → Settings → Agents → Subagents**:

| Built-in | Recommended | Why |
|----------|-------------|-----|
| Explore | **Auto** | Default Explore uses a fast Composer variant; Auto routes cost-efficiently |
| Bash / Browser | **Auto** or task-appropriate | Match your plan and task depth |

Repo subagents (`enterprise-auditor`, `implementer`, …) load from `.cursor/agents/` after install or plugin activate.

Maintainer PR: [`.agents/skills/pr-workflow/SKILL.md`](../../../.agents/skills/pr-workflow/SKILL.md).

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `pytest` not found | Re-run with `--with-venv` |
| `mcp validate` fails | Registry server keys must exist in merged `mcp.json` |
| Governance warns on CI | Normal when `.github/` absent in greenfield consumer |

Deep checklist: [install-dry-run.md](install-dry-run.md). Upgrade: [upgrade-kit.md](upgrade-kit.md).

---

## Installed consumer tree (default)

```text
your-project/
├── AGENTS.md
├── .cursor/          agents, skills, rules, mcp.json
├── .agents/skills/   review-pr, prepare-pr, merge-pr, pr-workflow
├── .ai_infra/        scripts, docs, manifest, .kit-version
├── .local/           gitignored — Tier 1 trackers + workflow-artifacts buckets (Tier 2 at runtime)
├── cursor_workflow/  python -m cursor_workflow (install|gates|health|mcp)
└── tests/modules/smoke/test_kit_installed.py
```

**Ongoing CLI** (`gates`, `health`, `mcp`): run **`python -m cursor_workflow`** from the consumer project (shim copied at install) or from kit/payload with `--directory "$TARGET"`.

See [gate-matrix.md](gate-matrix.md) for prepare GATES (2) vs kit gates (5) vs consumer scaffold verify (4).

**Pattern A:** one script command per agent action. `GATES` in `.ai_infra/scripts/pr/prepare.py`.
