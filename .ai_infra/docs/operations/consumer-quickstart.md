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

# Consumer quickstart

Install the **MAS Workflow Kit** into your project in a few minutes. No special git setup required.

---

## First run (4 steps)

**Need:** Cursor · Python 3.11+ · **your project folder open in Cursor** (not the kit repo).

| Step | Action |
|------|--------|
| **1. Plugin** | Cursor → Marketplace → **MAS Workflow Kit** → Install *(or `/add-plugin` → kit repo while waiting)* |
| **2. Activate** | In chat: skill **`workflow-activate`** → wait for **`VERIFY PASS`** |
| **3. Your name** | Edit `.local/user_settings/github.collaboration.yaml` → set `display_name` + `github_user` → `python3 -m cursor_workflow contributors validate` |
| **4. Build** | **@ implementer** · read `session-pointer.md` → `plan.md` → `work-tracker.md` |

**Healthy install?** `python3 -m cursor_workflow health`

---

## Step 2 detail — activate

**In chat (recommended):** skill **`workflow-activate`** on the open workspace.

**What it does:** copies three planes into your project:

| Plane | What lands on disk |
|-------|-------------------|
| Cursor | `.cursor/`, `.agents/`, `AGENTS.md` |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` |
| Runtime | `.local/` trackers + dashboards (gitignored) |

Also creates `.venv`, merges MCP config (profile **`with_mcp`**), runs smoke gates. Safe to re-run — won't overwrite your settings or trackers.

<details>
<summary><strong>Terminal activate (consumer trial, pre-Marketplace)</strong></summary>

```bash
export KIT=~/Projects/mas-workflow-kit
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" --source "$KIT/payload"
cd "$TARGET"
```

</details>

---

## Step 3 detail — personalize

File: `.local/user_settings/github.collaboration.yaml`

```yaml
owner:
  display_name: "Your Full Name"
  github_user: "@yourhandle"
```

```bash
cd ~/Projects/my-app   # your activated project — not mas-workflow-kit
python3 -m cursor_workflow contributors validate   # must PASS before first PR
python3 -m cursor_workflow integrate validate      # optional; P0 must be 0
python3 -m cursor_workflow health
```

> **YAML tip:** Edit only `owner` at first. Do not uncomment `# - display_name: Alice Example` under `human_coauthors: []` — that causes a YAML syntax error. To add a co-author, replace `[]` with a proper list (see exemplar comments).

Optional: `.local/user_settings/mcp.agents.yaml` · external MCP → skill **`connect-external-mcp`**

---

## Step 4 detail — daily workflow

1. Open `.local/index-and-planning/current/session-pointer.md`
2. Update `plan.md` and `work-tracker.md` for your slice
3. **@ implementer** (or **test-runner**, **verifier**, **enterprise-auditor**)
4. Dashboard (optional): `.local/agents-control-center/dashboards/`

**Add your own agent/skill/MCP:** **@ integrator-mas-agent** + skill **`mas-infrastructure-integration`**

---

## Quick tips

| Do | Don't |
|----|-------|
| Open **your app** in Cursor | Activate while inside `mas-workflow-kit` |
| **`workflow-activate`** in chat | Run `make gates` (kit-dev only) |
| Real paths like `~/Projects/my-app` | Literal `/path/to/your-project` |

---

## Verify (optional)

```bash
python3 -m cursor_workflow gates      # full gate pass
python3 -m cursor_workflow health     # layout + kit_version
```

Gate details: [gate-matrix.md](gate-matrix.md) (consumer scaffold = 4 checks).

---

## Kit clone path (advanced)

When not using the plugin UI — clone [mas-workflow-kit](https://github.com/SavinRazvan/mas-workflow-kit), then:

```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
export TARGET=~/Projects/my-app && mkdir -p "$TARGET"
.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" --with-venv --with-mcp-json --verify
cd "$TARGET"
```

Dry-run preview: add `--dry-run`. Upgrade later: [upgrade-kit.md](upgrade-kit.md).

Architecture: [workflow-architecture.md](../architecture/workflow-architecture.md) · Layout: [local-workspace-layout.md](local-workspace-layout.md)

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `contributors validate` FAIL | Replace placeholders in `github.collaboration.yaml` |
| YAML `ParserError` / traceback | Fix `human_coauthors` — keep `[]` or use a proper list; don't uncomment example lines as siblings of `[]` |
| Validate passes from kit repo but fails in your app | Run commands from **your project** (`cd ~/Projects/my-app`), not `mas-workflow-kit` |
| `pytest` not found | Re-run **`workflow-activate`** (creates `.venv`) |
| Permission denied on `/path` | You used a placeholder path — create a real folder |
| Agents missing in @ picker | Open **your activated project**, not the kit repo |

---

## What’s on disk after install

```text
your-project/
├── AGENTS.md
├── .cursor/       agents, skills, rules
├── .agents/skills/   PR slash commands (review-pr, prepare-pr, …)
├── .ai_infra/     scripts + docs
├── .local/        trackers (gitignored)
├── cursor_workflow/
└── tests/modules/smoke/
```

**CLI:** `python3 -m cursor_workflow` from your project root.
