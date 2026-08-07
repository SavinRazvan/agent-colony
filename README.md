<p align="center">
  <img src="assets/logo.png" alt="Agent Colony" width="160" height="160" />
</p>

# Agent Colony

**Installable multi-agent workflow infrastructure for Cursor**, with a **GitHub Project** as the only writable SSOT for backlog, Status, and agent continuation when `project_ssot.enabled` and `sync_policy: board_only`. Local `.local/` holds PR gates, audits, and evidence — never a second Status writer.

| | |
|--|--|
| **Product repo** | [agent-colony](https://github.com/SavinRazvan/agent-colony) |
| **Version** | `0.6.1` · **Tests** · 1465 · **Agents** · 8 · **Rules** · **7 universal** |
| **Board (kit-dev)** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) — reference layout for **Prioritized backlog** + **Status board** |

---

## Who is this for?

| Audience | Start here |
|----------|------------|
| **Consumer** — install into *your* app repo | [§ Install in your project](#install-in-your-project-consumers) → [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) |
| **Kit maintainer / agent** — develop *this* repo | [§ Work in this repository](#work-in-this-repository-kit-dev) → **[AGENTS.md](AGENTS.md)** (read first) |

---

## What you get

- **8 agents:** `implementer`, `test-runner`, `verifier`, `auditor`, `researcher`, `integrator`, `drift-guard`, `board`
- **13 canonical skills** + maintainer PR slash skills (`/review-pr` → `/prepare-pr` → `/merge-pr`)
- **Board Pattern A CLI:** `python3 -m agent_colony project …` (claim, handoff, Tier-1 fields, outbox)
- **PR gates** via `prepare.py` · optional MCP (`agent_colony_mcp`) · research corpus under `_research_results/` (opt-in)

**North star:** Entry = read the Project; Exit = update Status + Notes. Details: [ADR-008](.ai_infra/docs/decisions/ADR-008-project-board-ssot.md) · [project-board-collaboration.md](.ai_infra/docs/operations/project-board-collaboration.md).

---

## Install in your project (consumers)

**Need:** [Cursor](https://cursor.com) · Python 3.11+ · **your app folder** open (not this kit repo).

### 1. Add the plugin (Agent chat — not the terminal)

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

Click the **Agent Colony** card:

![Install Agent Colony from Agent chat](assets/agent-colony-install.png)

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
| Infrastructure | `.ai_infra/`, `agent_colony/` | CLI, scripts, docs, templates |
| Runtime | `.local/`, `.venv` | Trackers, **user settings** (gitignored) |

### 3. Your identity, then wire the board (Project SSOT)

**Order matters:** set identity → validate → (optional) `gh` check → **`/board`** wires YAML → shell UI.

#### 3a. Identity

Edit **`.local/user_settings/github.collaboration.yaml`**:

```yaml
owner:
  display_name: "Your Full Name"    # → Author: / Action-By:
  github_user: "@yourhandle"        # → GitHub-User:
```

Set **`project_ssot.enabled: true`** when you want the GitHub Project as SSOT (you can leave board ids empty until step 3c).

```bash
source .venv/bin/activate
python3 -m agent_colony contributors validate   # must PASS
python3 -m agent_colony health
```

#### 3b. GitHub CLI (Project SSOT only)

Agents call **`gh`** for board operations. Check scopes first — **skip refresh** if you already have Project access:

```bash
gh auth status   # need: repo + project (read:project may appear too)
```

If Project scopes are missing:

```bash
gh auth login -h github.com
# or add scopes on an existing login:
gh auth refresh -h github.com -s read:project,project
```

WSL / no browser: copy the one-time code → [github.com/login/device](https://github.com/login/device) → approve → return to terminal.

#### 3c. Wire `project_ssot` (API slice) — use **`/board`**

After **`contributors validate`** passes, paste **both URLs** in Agent chat (same message):

```text
/board

Project: https://github.com/users/YOU/projects/N
Repo:    https://github.com/YOU/your-app
```

The **`/board`** agent uses `gh project view` / `field-list` to propose **`project_ssot`** (board ids, Status/Priority/Size/Estimate/Start date field ids) and **`default_repo`**. **Confirm before save.**

Day-to-day board protocol lives in the **`board-ssot`** skill; onboarding wiring + shell coach is always **`/board`**.

Then verify the API slice:

```bash
source .venv/bin/activate
python3 -m agent_colony project doctor
python3 -m agent_colony project status
```

Expect:

```text
board-onboard status: api=complete · shell=incomplete · views=ui-only · next=/board CONSENT+TURN
```

**API slice done ≠ board ready.** Views and column visibility are **human UI only** (§4).

**Expected on a brand-new Project:** `doctor: ok` but `board-bootstrap --check` **FAIL** until you finish §4 — do **not** start `/implementer` yet.

Full checklist: [PLUGIN-USER-GUIDE § Consumer project_ssot onboarding](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#consumer-project_ssot-onboarding-checklist).

---

### 4. Prepare the board shell (required when SSOT is on)

> **After §3c.** Skip this and `/implementer` will fight a blank `View 1` board.

**You are here** when `project doctor` is ok but `board-bootstrap --check` prints `FAIL — missing minimum view …` and/or column FAILs.

Choose **one** shell path:

| Path | Views required | When |
|------|----------------|------|
| **Minimal 2-view** (recommended for small teams) | **Prioritized backlog** + **Status board** only | Match [AI Project Playground #3](https://github.com/users/SavinRazvan/projects/3) |
| **Playground default** | Six views (Roadmap, Bugs, In review, My items, …) | Kit default schema — no overlay |

#### Minimal 2-view (matches Playground #3)

**New installs:** activate auto-seeds `.local/user_settings/board-shell.schema.yaml` from the minimal exemplar (consumer repos only). **Existing installs:**

```bash
python3 -m agent_colony project board-shell init --minimal
```

Or copy manually:

In GitHub UI, mirror [Playground #3](https://github.com/users/SavinRazvan/projects/3):

| View | Layout |
|------|--------|
| **Prioritized backlog** | Table · show Priority, Size, Estimate, Start date |
| **Status board** | Board · group by **Status** · same Tier-1 columns |

Tab order does not matter — bootstrap matches by **view name**.

#### Playground default (six views)

See table in §4B below — use when you do **not** copy the minimal overlay.

#### What runs where

| Action | Where | Command / prompt |
|--------|--------|------------------|
| Check shell | Terminal | `python3 -m agent_colony project board-bootstrap --check` |
| Create missing **fields** | Terminal (optional) | `… board-bootstrap --check --ensure-fields` |
| Push Project **README** | Terminal (optional) | `… board-bootstrap --check --apply-readme` |
| Create/rename **views** + **columns** | Browser + **`/board`** | CONSENT GATE + TURN PROTOCOL — **no view CLI** |
| Day-to-day cards | After `--check` green | `/implementer` |

#### A. Agent chat (copy/paste)

```text
/board

Using minimal 2-view overlay (or: Playground six-view default).
board-bootstrap --check still FAIL — coach CONSENT GATE then TURN PROTOCOL:
one view per turn, wait for "done", re-run --check after each turn.
Project: https://github.com/users/YOU/projects/N
Repo: https://github.com/YOU/your-app
```

Skill: [board-shell](.cursor/skills/board-shell/SKILL.md) · [views-setup.md](.ai_infra/templates/project-board/views-setup.md)

#### B. GitHub UI — Playground default (six views)

| View | Layout (short) |
|------|----------------|
| **Status board** | Board · group by Status |
| **Prioritized backlog** | Table · Tier-1 columns |
| **Roadmap** | Roadmap |
| **Bugs** | Table · filter title contains `[BUG]` |
| **In review** | Table · Status = In review |
| **My items** | Table · Assignees = `@me` |

On **Status board** and **Prioritized backlog**, show: **Priority**, **Size**, **Estimate**, **Start date**.

#### C. Prove the shell (repeat until exit 0)

```bash
source .venv/bin/activate
python3 -m agent_colony project board-bootstrap --check
python3 -m agent_colony project status
```

Schema path should show `.local/user_settings/board-shell.schema.yaml` when using the minimal overlay.

**Do not** start with `/auditor`. When bootstrap is green → **§5** `/implementer`.

---

### 5. Start building

| Goal | In Agent chat |
|------|----------------|
| Implement a slice | `/implementer` |
| Tests / coverage | `/test-runner` |
| Verify a claim | `/verifier` |
| PR lifecycle | `/review-pr` → `/prepare-pr` → `/merge-pr` |
| Research a repo | `/researcher` + a GitHub URL |
| Extend agents/skills/MCP | `/integrator` |
| Architecture audit *(later)* | `/auditor` — not day-0 onboarding |

**Every session Entry:** if `project_ssot.enabled` → `python3 -m agent_colony project status`; else → `.local/index-and-planning/current/session-pointer.md`.

Shorter path: [consumer-quickstart.md](.ai_infra/docs/operations/consumer-quickstart.md).

### Optional — Update the kit / plugin later

Docs and agents in **your app** come from the plugin payload + `/workflow-activate`. Re-reading the kit README on GitHub does **not** change Smart-Notes until you refresh.

1. **Ship on the kit repo first** (maintainer): merge the change to `main` (PR workflow).
2. **In your app** (e.g. Smart-Notes), Agent chat — refresh the plugin from GitHub:

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

3. Re-activate (safe / idempotent — keeps `.local/user_settings/` and existing `AGENTS.md`):

```text
/workflow-activate
```

Or terminal:

```bash
source .venv/bin/activate
python3 -m agent_colony activate --directory .
```

4. Sanity check:

```bash
python3 -m agent_colony health
python3 -m agent_colony project board-bootstrap --check   # still FAIL until you finish step 4 views in GitHub UI
```

**Force** full overwrite of agents/skills/scripts (review diffs): `python3 -m agent_colony activate --directory . --force`  
Details: [upgrade-kit.md](.ai_infra/docs/operations/upgrade-kit.md).

**Board views are not fixed by a plugin update.** `board-bootstrap --check` FAIL on missing views only clears after you complete **step 4** (`/board` + human UI). Updating the plugin only refreshes docs/coaching text.

---

## Work in this repository (kit-dev)

```bash
gh repo clone SavinRazvan/agent-colony
cd agent-colony
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,mcp]"
```

1. Open the folder in Cursor.
2. Read **[AGENTS.md](AGENTS.md)** first.
3. Confirm collaboration YAML under `.local/user_settings/` (owner + `project_ssot`).
4. Start:

```bash
python3 -m agent_colony project status
python3 -m agent_colony project list --status ready
# create / claim — see: python3 -m agent_colony project guide
```

Maintainer gates: `make gates` · `make drift-validate` · `make doc-validate` · shipped matrix: [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md). Kit canvases: **15** files under `canvases/` (**11** agent/roster hubs + 4 concept hubs — see IMPLEMENTATION-STATUS § Kit canvases). Canvas/plan local artifacts: [ADR-010](.ai_infra/docs/decisions/ADR-010-canvas-plan-local-artifacts.md) · [canvas-artifacts](.cursor/skills/canvas-artifacts/SKILL.md).

---

## Documentation map

| Doc | Audience |
|-----|----------|
| [AGENTS.md](AGENTS.md) | Kit-dev front door — identity, north star, execution roster |
| [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) | Consumers — install, activate, board onboarding |
| [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md) | 5-minute consumer path |
| [Docs index](.ai_infra/docs/README.md) | Full `.ai_infra/docs/` navigation |
| [repository-map](.ai_infra/docs/handoff/repository-map.md) | Kit vs payload vs consumer install |
| [assets/](assets/README.md) | Logo + install screenshot |

---

## License

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)
