---
name: workflow-activate
description: Install MAS Workflow Kit — Project SSOT infrastructure into the current workspace from the plugin payload (ADR-001 Option B).
---

# Workflow activate

## When

User enabled the **MAS Workflow Kit — Project SSOT** plugin (`mas-workflow-kit-project-ssot`) and opened **their app** (not the kit product repo). Run on first use or when planes are missing.

## Guide the user (keep it simple)

**Product promise:** Plugin install loads agents/skills in Cursor only. **`/workflow-activate`** in **their app repo** installs the **full kit**. They edit `.local/user_settings/github.collaboration.yaml` for identity + board ids. Usage matches kit-dev after **`board-bootstrap --check` exit 0** — see [PLUGIN-USER-GUIDE § Product promise](../../../docs/operations/PLUGIN-USER-GUIDE.md#product-promise).

1. If plugin not installed: Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` (chat only — not terminal).
2. Confirm the open folder is **their app**, not the kit product repo.
3. Run activate (below) — or **`/workflow-activate`** from the **`/`** menu.
4. Wire collaboration YAML — set name/@handle; when enabling Project SSOT: **`gh` auth first**, then paste **Project URL + repo URL** → **`/project-board`** proposes ids + `default_repo` (or `gh project view` / `field-list`) → `contributors validate` → `project doctor`. Grant scopes `read:project,project` (+ `repo`).
5. When `project_ssot.enabled`: first-run board shell — **`/project-board`** + `board-shell-onboard` **CONSENT GATE** then TURN PROTOCOL → `project board-bootstrap --check` (optional `--ensure-fields` / `--apply-readme`) → `project status`. **Do not** start with `/enterprise-auditor`.
6. Point them to **`/implementer`**. When board SSOT on, Entry is `python -m cursor_workflow project status`; else read `session-pointer.md` first.

## One command (agent or human)

From the **open workspace** (Pattern A — one script command):

```bash
python3 -m cursor_workflow activate --directory .
```

**Auto source resolution:** `WORKFLOW_KIT_PAYLOAD` env → `./payload/` → kit `payload/` (plugin bundle). Override with `--source /path/to/payload`.

**MCP:** `workflow_activate` on the `workflow-kit` server (same behavior).

## What `activate` does

| Plane | Paths installed | Cursor loads? |
|-------|-----------------|---------------|
| Cursor contract | `.cursor/`, `.agents/`, `AGENTS.md` | Yes |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` | No — scripts/CLI |
| Runtime | `.local/` Tier 1 scaffold: trackers, six `workflow-artifacts/*` buckets + README stubs, `pages.json`, dashboards; `user_settings/` exemplars | No — gitignored |

Re-activate does not overwrite trackers, `user_settings/`, or `AGENTS.md`. Kit-managed dashboard HTML, JS/CSS, `module-audit.html`, and `pages.json` refresh from the activate source (`payload/` when resolved) or embedded `.ai_infra/templates/local-workspace/`.

- Idempotent: skips full install when all planes already pass `install-contract.json`, but still refreshes dashboards
- Creates `.venv`, merges MCP json, runs verify gates
- Prints **settings-only** next steps (no re-install)

**MCP config files:** the Marketplace repo-root `agents/`, `rules/`, `skills/` trees load agents,
skills, and rules only. MCP examples install under `.cursor/` from **payload** when `activate`
runs — not before. Use **`/connect-external-mcp`** after activate.

## Post-activate (tell the user)

1. Open `.local/user_settings/github.collaboration.yaml` — set **display_name**, **github_user**. For Project SSOT: enable + `board_only`; after **`gh` auth** paste **Project URL + repo URL** → **`/project-board`** proposes ids + `default_repo` (or `gh project view` / `field-list`). Optional: `board-bootstrap --check --ensure-fields`.
2. Terminal: `source .venv/bin/activate && python3 -m cursor_workflow contributors validate` (must PASS). Grant `gh` Project scopes before doctor.
3. When board SSOT enabled: `python3 -m cursor_workflow project doctor` → **`/project-board`** + `board-shell-onboard` → `python3 -m cursor_workflow project board-bootstrap --check` until **default Playground shell** green → `python3 -m cursor_workflow project status`
4. **`/implementer`** to start · audit (`/enterprise-auditor`) is later / architecture-impacting — not day-0.

Optional: `integrate validate`, `health`. Add infrastructure later: **`/integrator-mas-agent`**.

## Adding agents/skills/MCP later

Invoke subagent **`/integrator-mas-agent`** with skill **`/mas-infrastructure-integration`** — not shell commands.

## Agent delegation

After plugin enable, parent agent or user should:

0. If plugin not installed: Agent chat → `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` (chat only — not terminal).
1. Run **`workflow_activate`** or `cursor_workflow activate`
2. Hand user to personalize `user_settings/` + `gh` Project scopes
3. When SSOT on: **`/project-board`** (board-shell-onboard) until `board-bootstrap --check` green
4. Point to **`/implementer`**; optionally delegate **`/integrator-mas-agent`** for extensions

## Success

- All three planes `ready` in activate output
- `contributors validate` exit 0 (after user edits placeholders)
- When SSOT on: `project board-bootstrap --check` green (default Playground shell)
- `integrate validate` exit 0 (optional)

## Reference

- [PLUGIN-USER-GUIDE.md](../../../docs/operations/PLUGIN-USER-GUIDE.md) — unified consumer manual
- [ADR-001 Option B](../../../docs/decisions/ADR-001-distribution-activation.md)
- [consumer-quickstart.md](../../../docs/operations/consumer-quickstart.md)
