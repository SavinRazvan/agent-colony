<p align="center">
  <img src="assets/logo.png" alt="MAS Workflow Kit — Project SSOT" width="160" height="160" />
</p>

# MAS Workflow Kit — Project SSOT

**Installable multi-agent workflow infrastructure for Cursor**, with a **GitHub Project** as the only writable SSOT for backlog, Status, and agent continuation when `project_ssot.enabled` and `sync_policy: board_only`. Local `.local/` holds PR gates, audits, and evidence — never a second Status writer.

| | |
|--|--|
| **Product repo** | [mas-workflow-kit-project-ssot](https://github.com/SavinRazvan/mas-workflow-kit-project-ssot) |
| **Version** | `0.4.0` · **Tests** · 1121 · **Agents** · 8 · **Rules** · **7 universal** |
| **Board (kit-dev)** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) |
| **Standing** | **STANDALONE** — permanent product; lineage only from [mas-workflow-kit](https://github.com/SavinRazvan/mas-workflow-kit) (`v0.4.0` / `8a779fa`) |

---

## Who is this for?

| Audience | Start here |
|----------|------------|
| **Consumer** — install into *your* app repo | [§ Install in your project](#install-in-your-project-consumers) → [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) |
| **Kit maintainer / agent** — develop *this* repo | [§ Work in this repository](#work-in-this-repository-kit-dev) → **[HANDOFF.md](HANDOFF.md)** (read first) → [AGENTS.md](AGENTS.md) |

---

## What you get

- **8 agents:** `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `researcher`, `integrator-mas-agent`, `workflow-drift-guard`, `project-board`
- **11 canonical skills** + maintainer PR slash skills (`/review-pr` → `/prepare-pr` → `/merge-pr`)
- **Board Pattern A CLI:** `python3 -m cursor_workflow project …` (claim, handoff, Tier-1 fields, outbox)
- **PR gates** via `prepare.py` · optional MCP (`workflow_mcp`) · research corpus under `_research_results/` (opt-in)

**North star:** Entry = read the Project; Exit = update Status + Notes. Details: [ADR-008](.ai_infra/docs/decisions/ADR-008-project-board-ssot.md) · [project-board-collaboration.md](.ai_infra/docs/operations/project-board-collaboration.md).

---

## Install in your project (consumers)

**Need:** [Cursor](https://cursor.com) · Python 3.11+ · **your app folder** open (not this kit repo).

### 1. Add the plugin (Agent chat — not the terminal)

```text
/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot
```

Click the **MAS Workflow Kit — Project SSOT** card:

![Install MAS Workflow Kit — Project SSOT from Agent chat](assets/mas-workflow-kit-install.png)

*Marketplace listing is deferred; `/add-plugin` from GitHub is the supported path today.*

### 2. Activate into your workspace

Still in **your app** folder, Agent chat:

```text
/workflow-activate
```

Wait for **`VERIFY PASS`** and all three planes **ready**. Activate is idempotent (safe to re-run).

| Plane | Paths | Purpose |
|-------|-------|---------|
| Cursor contract | `.cursor/`, `.agents/`, `AGENTS.md` | Agents, skills, rules |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` | CLI, scripts, docs, templates |
| Runtime | `.local/`, `.venv` | Trackers, **user settings** (gitignored) |

### 3. Configure your identity (and optional Project SSOT)

Edit **`.local/user_settings/github.collaboration.yaml`** (copied from exemplars on activate):

```yaml
owner:
  display_name: "Your Full Name"    # → Author: / Action-By:
  github_user: "@yourhandle"        # → GitHub-User:

# Optional — GitHub Project as only writable Status SSOT
project_ssot:
  enabled: true
  sync_policy: board_only           # board wins; local trackers = offline fallback
  # + name, number, owner, project_id, fields.* option ids
```

Validate:

```bash
source .venv/bin/activate
python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow health
```

**With Project SSOT on** (kit-shaped board: Status · Priority · Size · Estimate **points** · Start date):

```bash
gh auth refresh -h github.com -s read:project,project   # keep repo
python3 -m cursor_workflow project doctor
python3 -m cursor_workflow project status
python3 -m cursor_workflow project guide                # safe recipes
```

Wire field ids with `gh project view` / `gh project field-list` — full checklist: [PLUGIN-USER-GUIDE § Product promise](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#product-promise).

### 4. Start building

| Goal | In Agent chat |
|------|----------------|
| Implement a slice | `/implementer` |
| Tests / coverage | `/test-runner` |
| Verify a claim | `/verifier` |
| PR lifecycle | `/review-pr` → `/prepare-pr` → `/merge-pr` |
| Research a repo | `/researcher` + a GitHub URL |
| Extend agents/skills/MCP | `/integrator-mas-agent` |

**Every session Entry:** if `project_ssot.enabled` → `python3 -m cursor_workflow project status`; else → `.local/index-and-planning/current/session-pointer.md`.

Shorter path: [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md).

---

## Work in this repository (kit-dev)

```bash
gh repo clone SavinRazvan/mas-workflow-kit-project-ssot
cd mas-workflow-kit-project-ssot
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

1. Open the folder in Cursor.
2. Read **[HANDOFF.md](HANDOFF.md)** first, then [AGENTS.md](AGENTS.md).
3. Confirm collaboration YAML under `.local/user_settings/` (owner + `project_ssot`).
4. Start:

```bash
python3 -m cursor_workflow project status
python3 -m cursor_workflow project list --status ready
# create / claim — see: python3 -m cursor_workflow project guide
```

Maintainer gates: `make gates` · `make drift-validate` · `make doc-validate` · shipped matrix: [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md). Kit canvases: **14** files under `canvases/` (**11** agent/roster hubs + 3 concept hubs — see IMPLEMENTATION-STATUS § Kit canvases).

---

## Documentation map

| Doc | Audience |
|-----|----------|
| [HANDOFF.md](HANDOFF.md) | Kit-dev agents & maintainers (identity, north star) |
| [AGENTS.md](AGENTS.md) | Day-to-day agent execution |
| [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) | Consumers — install, activate, board onboarding |
| [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md) | 5-minute consumer path |
| [Docs index](.ai_infra/docs/README.md) | Full `.ai_infra/docs/` navigation |
| [repository-map](.ai_infra/docs/handoff/repository-map.md) | Kit vs payload vs consumer install |
| [assets/](assets/README.md) | Logo + install screenshot |

---

## License

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)
