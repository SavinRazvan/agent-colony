---
name: workflow-activate
description: Install MAS Workflow Kit — Project SSOT infrastructure into the current workspace from the plugin payload (ADR-001 Option B).
---
<!--
File: SKILL.md
Path: .cursor/skills/workflow-activate/SKILL.md
Role: Install MAS Workflow Kit — Project SSOT three planes into the open workspace (ADR-001 Option B).
Used By:
 - PLUGIN-ARCHITECTURE.md
 - sync_plugin_bundle.py (canonical; template fallback at .ai_infra/templates/plugin/skills/)
Depends On:
 - .ai_infra/install/cursor_workflow/activate_cli.py
Notes:
 - Pattern A: one script command per action.
-->

# Workflow activate

## When

User enabled the **MAS Workflow Kit — Project SSOT** plugin (`mas-workflow-kit-project-ssot`) and opened **their app** (not this kit product repo). Run on first use or when planes are missing.

## When user just installed plugin (`/add-plugin`)

If the user ran **`/add-plugin`** and sees the kit welcome summary, use this **canonical first run** — do **not** invent a shorter list that hides the GitHub UI step:

1. **`/workflow-activate`** in **their app repo** (wait for VERIFY PASS)
2. Edit `github.collaboration.yaml` → identity → `contributors validate`
3. **`gh auth status`** — refresh Project scopes only if missing
4. Paste **Project URL + repo URL** → **`/project-board`** wire (API slice — print `board-onboard status: api=complete · shell=incomplete · views=ui-only`)
5. Optional: copy **minimal 2-view overlay** (matches Playground #3) or use six-view default
6. **`/project-board`** + **CONSENT GATE** + **TURN PROTOCOL** (human UI; 2 or 6 views)
7. `board-bootstrap --check` **exit 0** → **`/implementer`**

Never list `/board-shell` before wire. Never imply views are API-automated. Default shell coaching is human UI (TURN PROTOCOL); use browser MCP for views/columns only when the user explicitly asks.

## Guide the user (keep it simple)

**Product promise:** Plugin install loads agents/skills in Cursor only. **`/workflow-activate`** in **their app repo** installs the **full kit** (same three planes as kit-dev). They edit `.local/user_settings/github.collaboration.yaml` for identity + board ids. Usage matches kit-dev after **`board-bootstrap --check` exit 0** (not wire-only). See [PLUGIN-USER-GUIDE § Product promise](../../.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#product-promise).

1. If plugin not installed: Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` (chat only — not terminal). Show [install screenshot](https://raw.githubusercontent.com/SavinRazvan/mas-workflow-kit-project-ssot/main/assets/mas-workflow-kit-install.png) or [consumer-quickstart § step 1](../../.ai_infra/docs/operations/consumer-quickstart.md#step-1-detail--install-plugin-from-github) — user clicks the **MAS Workflow Kit — Project SSOT** card in the preview.
2. Confirm the open folder is **their app**, not the kit product repo (`mas-workflow-kit-project-ssot`).
3. Run activate (below) — or tell them to pick **`/workflow-activate`** from the **`/`** menu.
4. Wire collaboration YAML — set name/@handle → **`contributors validate`** → **`gh auth status`** (refresh only if needed) → paste **Project URL + repo URL** in chat → **`/project-board`** wires `project_ssot` + `default_repo` → `project doctor`.
5. When `project_ssot.enabled`: copy **minimal 2-view overlay** (optional; [Playground #3](https://github.com/users/SavinRazvan/projects/3)) → **`/project-board`** + [board-shell](board-shell/SKILL.md) **CONSENT GATE** + **TURN PROTOCOL** → `board-bootstrap --check` exit **0** → `project status`.
6. Point them to **`/implementer`** (from **`/`** menu). When board SSOT on, Entry is **`python -m cursor_workflow project status`**; else read `session-pointer.md` first.

Do **not** dump gate lists or maintainer `make` commands.

## One command

From the **open workspace** (Pattern A — one script command):

```bash
python3 -m cursor_workflow activate --directory .
```

**Auto source resolution:** `WORKFLOW_KIT_PAYLOAD` env → `./payload/` → kit `payload/` (plugin bundle). Override with `--source /path/to/payload`.

**MCP:** `workflow_activate` on the `workflow-kit` server (same behavior).

### First install (`cursor_workflow` module absent)

On a **brand-new app repo**, `python3 -m cursor_workflow` fails until activate copies infrastructure. **Do not stop** — run activate from the **plugin payload** (or kit checkout):

```bash
export KIT=~/Projects/mas-workflow-kit-project-ssot   # or plugin cache path
export TARGET=~/Projects/my-app
cd "$TARGET"
"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" --source "$KIT/payload"
```

Or set `WORKFLOW_KIT_PAYLOAD` to the payload directory and invoke the payload entrypoint the same way. After **VERIFY PASS**, all later commands use:

```bash
source .venv/bin/activate && python3 -m cursor_workflow …
```

If **VERIFY FAIL** on missing test deps, retry:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m cursor_workflow activate --directory .
```

See [consumer-quickstart.md](../../.ai_infra/docs/operations/consumer-quickstart.md) § First activate troubleshooting.

## What `activate` does

| Plane | Paths installed | Cursor loads? |
|-------|-----------------|---------------|
| Cursor contract | `.cursor/`, `.agents/`, `AGENTS.md` | Yes |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` | No — scripts/CLI |
| Runtime | `.local/` Tier 1 scaffold: trackers, six `workflow-artifacts/*` buckets + README stubs, `pages.json`, dashboards; `user_settings/` exemplars | No — gitignored |

Tier 1 paths are created on first install; Tier 2 runtime `.md` files appear when agents/scripts run. See [local-workspace-layout.md](../../.ai_infra/docs/operations/local-workspace-layout.md) § Artifact tiers. Re-activate does not overwrite existing trackers, `user_settings/`, or `AGENTS.md`. Kit-managed dashboard HTML, JS/CSS assets, `module-audit.html`, and `pages.json` are refreshed from the activate source (plugin `payload/` when resolved) or embedded `.ai_infra/templates/local-workspace/` when not.

- Idempotent: skips full install when all planes already pass `install-contract.json`, but still refreshes dashboards
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

**MCP config files:** The Marketplace repo-root `agents/`, `rules/`, `skills/` trees load agents, skills, and rules only. MCP examples (`mcp.json.kit.example`, `mcp.registry.yaml.example`, `mcp.user.example.json`, `MCP-CONFIG.md`) install under `.cursor/` from **payload** when `activate` runs — not before. Use **`/mcp-connect`** after activate.

## Post-activate (tell the user)

1. Open `.local/user_settings/github.collaboration.yaml` — set **display_name**, **github_user**. For Project SSOT: enable + `board_only`.
2. Terminal: `source .venv/bin/activate && python3 -m cursor_workflow contributors validate` (must PASS).
3. **`gh auth status`** — refresh Project scopes only if missing — [PLUGIN-USER-GUIDE § GitHub CLI auth](../../.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#github-cli-auth-projects).
4. Paste **Project URL + repo URL** in chat → **`/project-board`** wires `project_ssot` + `default_repo` (confirm before save) → `project doctor` + `project status`.
5. When board SSOT enabled: optional **minimal 2-view overlay** ([Playground #3](https://github.com/users/SavinRazvan/projects/3)) → **`/project-board`** + `board-shell` (**CONSENT GATE** then TURN PROTOCOL) → `board-bootstrap --check` until **exit 0** → `project status`. See [views-setup.md](../../.ai_infra/templates/project-board/views-setup.md).
6. **`/implementer`** to start · each session Entry: **`source .venv/bin/activate && python3 -m cursor_workflow project status`** when board SSOT on; else read `session-pointer.md` first. Audit (`/enterprise-auditor`) is later — not day-0.

**Dashboards (optional):** from project root run `source .venv/bin/activate && python3 -m http.server 8000`, then open
http://localhost:8000/.local/agents-control-center/dashboards/index.html (not `file://`).

Optional: `integrate validate`, `health`. Add infrastructure later: **`/integrator-mas-agent`**.

## Adding agents/skills/MCP later

Invoke subagent **`/integrator-mas-agent`** with skill **`/integrator-protocol`** — not shell commands ([Subagents](https://cursor.com/docs/subagents), [Skills](https://cursor.com/docs/skills)).

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- `integrate validate` exit 0

## Reference

- [PLUGIN-USER-GUIDE.md](../../.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) — unified consumer manual
- [ADR-001 Option B](../../.ai_infra/docs/decisions/ADR-001-distribution-activation.md)
- [consumer-quickstart.md](../../.ai_infra/docs/operations/consumer-quickstart.md)
