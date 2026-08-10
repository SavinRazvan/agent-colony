<!--
File: consumer-quickstart.md
Path: .ai_infra/docs/operations/consumer-quickstart.md
Role: Five-minute install path for adopting the kit in a new or existing project.
Used By:
 - README.md
 - IMPLEMENTATION-STATUS.md document map
Depends On:
 - .ai_infra/install/agent_colony/cli.py
 - .ai_infra/scripts/install/scaffold.py
 - .ai_infra/docs/operations/project-config.md
Notes:
 - Pattern A: agents call scripts; merge gates via `resolve_gates()` in prepare.py (`GATES` = alias).
-->

# Consumer quickstart

> **From the [kit README](https://github.com/SavinRazvan/agent-colony#install-consumers):** this is the 5-step install path after `/add-plugin` + `/workflow-activate`. Full manual: [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md).

Install **Agent Colony** (`agent-colony`) into your project in a few minutes. No special git setup required.

**Product promise:** Install the plugin → open **your app repo** → **`/workflow-activate`** installs the **full kit**. Customize identity in `github.collaboration.yaml`, then **`/board`** wires board ids from Project + repo URLs. **Ready for agents** requires `board-bootstrap --check` **exit 0** — either **two views** (minimal overlay, matches [Playground #3](https://github.com/users/SavinRazvan/projects/3)) or **six Playground views** (kit default). Wire-only is not enough. Details: [PLUGIN-USER-GUIDE § Product promise](PLUGIN-USER-GUIDE.md#product-promise).

> **Also:** [MCP](connect-external-mcp.md) · [upgrade](upgrade-kit.md) · [abbreviations](abbreviations-notepad.md) · skill `research-corpus` · skill `board-shell`

---

## First run (5 steps)

**Need:** Cursor · Python 3.11+ · **your project folder open in Cursor** (not the kit product repo `agent-colony`).

| Step | Action |
|------|--------|
| **1. Plugin** | In **Agent chat** (not terminal): `/add-plugin https://github.com/SavinRazvan/agent-colony` — or **Cursor → Marketplace** when listed |
| **2. Activate** | Open **your app folder** → Agent chat: **`/workflow-activate`** → wait for **`VERIFY PASS`** |
| **3. Identity** | Edit `github.collaboration.yaml` → `display_name` + `github_user` → `source .venv/bin/activate && python3 -m agent_colony contributors validate` |
| **3b. GitHub auth** *(board SSOT)* | `gh auth status` — if Project scopes missing: `gh auth refresh -h github.com -s read:project,project`. Device flow: [github.com/login/device](https://github.com/login/device). [PLUGIN-USER-GUIDE § GitHub CLI auth](PLUGIN-USER-GUIDE.md#github-cli-auth-projects). |
| **3c. Wire board** *(board SSOT)* | Agent chat **`/board`** + paste **Project URL + repo URL** → agent proposes `project_ssot` + `default_repo` (confirm) → `project doctor` + `project status` |
| **4. Board shell** *(when SSOT on)* | **Minimal 2-view** (recommended): copy overlay → Prioritized backlog + Status board in UI ([Playground #3](https://github.com/users/SavinRazvan/projects/3)). **Or** six-view Playground default. **`/board`**: CONSENT GATE + TURN PROTOCOL → `--check` exit **0**. |
| **5. Build** | **`/implementer`** · Entry = `python3 -m agent_colony project status` when board SSOT on |

**Healthy install?** `python3 -m agent_colony health` · with board on: `gh auth status` → `project doctor` → `project board-bootstrap --check`

**Update kit later (optional):** merge kit changes to `main` → in your app Agent chat `/add-plugin https://github.com/SavinRazvan/agent-colony` → **`/update-agent-colony`** (or `python3 -m agent_colony update --directory .`). First install remains `/workflow-activate`. Full force/semver: [upgrade-kit.md](upgrade-kit.md). **Does not** create GitHub Project views — finish step 4 for that.

> **Cheat sheet:** [Visual walkthrough](#visual-walkthrough) · [Agent chat vs terminal](#agent-chat-vs-terminal) · [Dashboards (deprecated)](#control-center-dashboards-deprecated) · [All CLI commands](#terminal-commands-cheat-sheet)

## Visual walkthrough

Onboarding screenshots are ~**1920×1080**. Each displays at **800px** — **click** any image for full resolution, then zoom in the browser (<kbd>Ctrl</kbd>+<kbd>+</kbd> / <kbd>−</kbd>).

| # | What you see | Section |
|---|--------------|---------|
| 01–03 | `/add-plugin` → Add Plugin → installing | [Step 1](#step-1-detail--install-plugin-from-github) |
| 04 | `/workflow-activate` in chat | [Step 2](#step-2-detail--activate) |
| 05–06 | Identity YAML + `contributors validate` | [Step 3](#step-3-detail--identity-auth-wire-board) |
| 07–08 | New Project + `/board` wire | [Step 3](#step-3-detail--identity-auth-wire-board) |
| 09–12 | Board shell — views + columns | [Step 4](#step-4-detail--board-shell-minimal-2-view-or-six-view-default) |
| 13–15 | Reference board + draft cards *(kit example)* | [Reference board](#reference-board-example) |
| 16–17 | DeepWiki MCP chat + CLI | [MCP smoke](#mcp-smoke-deepwiki) |

### Step 1 detail — install plugin from GitHub

`/add-plugin` runs in **Cursor Agent chat only** — it is not a shell command.

```bash
/add-plugin https://github.com/SavinRazvan/agent-colony
```

Cursor shows an **Add Plugin** preview — click the **Agent Colony** card to install:

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/01_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/01_tutorial_agent-colony.png" alt="Cursor Agent chat: type /add-plugin with the GitHub URL and review the Agent Colony preview card" width="800" />
  </a>
</p>
<p align="center"><sub><strong>01</strong> — Preview card · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/01_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/02_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/02_tutorial_agent-colony.png" alt="Select your app project in Cursor and click Add Plugin" width="800" />
  </a>
</p>
<p align="center"><sub><strong>02</strong> — Select project → Add Plugin · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/02_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/03_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/03_tutorial_agent-colony.png" alt="Agent Colony plugin installing in Cursor" width="800" />
  </a>
</p>
<p align="center"><sub><strong>03</strong> — Installing · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/03_tutorial_agent-colony.png">Full size</a></sub></p>

Optional — pin `main`:

```bash
/add-plugin https://github.com/SavinRazvan/agent-colony/tree/main
```

After install you may see only `.cursor/settings.json` in the project. That is expected — run **step 2** to copy the full bundle.

### In Agent chat — type `/`

Cursor lists **subagents**, **skills**, and **commands** in the same **`/`** menu ([Customize Cursor](https://cursor.com/docs/customize-cursor)). Names match the `name:` field in each file.

| What you want | Type in chat | Lives on disk |
|---------------|--------------|---------------|
| Activate the kit | **`/workflow-activate`** | `.cursor/skills/workflow-activate/` |
| Wire board + shell coach | **`/board`** | `.cursor/agents/board.md` + `board-shell` |
| Day-to-day board protocol | **`board-ssot`** skill (auto-loaded) | `.cursor/skills/board-ssot/` |
| Implement a slice | **`/implementer`** | `.cursor/agents/implementer.md` |
| Run tests | **`/test-runner`** | `.cursor/agents/test-runner.md` |
| PR review / prepare / merge | **`/review-pr`**, `/prepare-pr`, `/merge-pr` | `.agents/skills/` (loaded as skills) |
| Extend agents/skills/MCP | **`/integrator`** + `/integrator-protocol` | agent + skill |
| Attach a file or doc | **`@`** + pick context | — ([Prompting](https://cursor.com/docs/agent/prompting)) |

Agent may also **auto-delegate** subagents or **auto-apply** skills when the task matches their `description` — explicit **`/name`** is the reliable manual path.

---

## Step 2 detail — activate

1. **File → Open Folder** → your app (e.g. `~/Projects/my-app`)
2. In **Agent chat** (not the terminal):

```text
/workflow-activate
```

Or type `/` and pick **workflow-activate** from the menu.

3. Wait for **`VERIFY PASS`** and all planes **ready**

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/04_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/04_tutorial_agent-colony.png" alt="Agent chat: type /workflow-activate and pick workflow-activate from the Agent Colony menu" width="800" />
  </a>
</p>
<p align="center"><sub><strong>04</strong> — Activate · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/04_tutorial_agent-colony.png">Full size</a></sub></p>

**What it does:** copies three planes into your project:

| Plane | What lands on disk |
|-------|-------------------|
| Cursor | `.cursor/`, `.agents/`, `AGENTS.md` |
| Infrastructure | `.ai_infra/`, `agent_colony/` |
| Runtime | `.local/` trackers + dashboards (gitignored) |

Also creates `.venv`, merges MCP config (profile **`with_mcp`**), seeds DeepWiki into
`mcp.user.json` + live registry when missing, runs smoke gates.

**Re-activate is safe:** won't overwrite your trackers, `user_settings/`, or `AGENTS.md`. Kit-managed **dashboard HTML**, JS/CSS, `module-audit.html`, and `pages.json` **are refreshed** on each activate (from plugin payload when available).

**Terminal equivalent** (same as `/workflow-activate`):

```bash
cd ~/Projects/my-app          # your activated project
source .venv/bin/activate     # after first activate
python3 -m agent_colony activate --directory .
```

### First activate troubleshooting

On a **brand-new app repo**, `python3 -m agent_colony` fails with *No module named agent_colony* until activate copies infrastructure. **Agents:** run activate from the **Cursor plugin cache payload** (created by `/add-plugin`) — not bare `python3 -m agent_colony` in an empty folder:

```bash
cd ~/Projects/my-app
PAYLOAD="$(ls -1dt ~/.cursor/plugins/cache/agent-colony/agent-colony/*/payload 2>/dev/null | head -1)"
test -n "$PAYLOAD" || { echo "Re-run /add-plugin first"; exit 1; }
python3 "$PAYLOAD/agent_colony" activate --directory . --source "$PAYLOAD"
# or: python3 "$PAYLOAD/.ai_infra/scripts/install/bootstrap_activate.py" --directory .
source .venv/bin/activate
```

Kit-dev checkout (optional alternative):

```bash
export KIT=~/Projects/agent-colony
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
python3 "$KIT/payload/agent_colony" activate \
  --directory "$TARGET" --source "$KIT/payload"
cd "$TARGET"
source .venv/bin/activate
```

If **VERIFY FAIL** on missing test deps after first install:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
python3 -m agent_colony activate --directory .
```

After **VERIFY PASS**, always prefix CLI commands with `source .venv/bin/activate &&`.

To pull the latest dashboards after a kit update without a full reinstall:

```bash
python3 -m agent_colony activate --directory .
```

<details>
<summary><strong>Alternative: terminal activate (no plugin UI)</strong></summary>

```bash
export KIT=~/Projects/agent-colony
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
"$KIT/.venv/bin/python" "$KIT/payload/agent_colony" activate \
  --directory "$TARGET" --source "$KIT/payload"
cd "$TARGET"
```

</details>

---

## Step 3 detail — identity, auth, wire board

File: `.local/user_settings/github.collaboration.yaml`

```yaml
owner:
  display_name: "Your Full Name"
  github_user: "@yourhandle"
```

```bash
cd ~/Projects/my-app
source .venv/bin/activate
python3 -m agent_colony contributors validate   # must PASS — do this before wiring board ids
python3 -m agent_colony health
```

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/05_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/05_tutorial_agent-colony.png" alt="After VERIFY PASS: edit github.collaboration.yaml display_name and github_user" width="800" />
  </a>
</p>
<p align="center"><sub><strong>05</strong> — Identity YAML · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/05_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/06_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/06_tutorial_agent-colony.png" alt="Terminal: python3 -m agent_colony contributors validate showing PASS" width="800" />
  </a>
</p>
<p align="center"><sub><strong>06</strong> — contributors validate PASS · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/06_tutorial_agent-colony.png">Full size</a></sub></p>

> **YAML tip:** Edit only `owner` at first. Do not uncomment example lines under `human_coauthors: []`.

### GitHub CLI (when `project_ssot.enabled`)

```bash
gh auth status
```

If scopes already include **`project`** (and **`repo`**), skip refresh. Otherwise:

```bash
gh auth refresh -h github.com -s read:project,project
```

### Wire board — **`/board`** (Agent chat)

Create a **GitHub Project** for your app and set the **default repository** to your code repo (human UI):

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/07_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/07_tutorial_agent-colony.png" alt="GitHub: new Project with default repository set to the app repo" width="800" />
  </a>
</p>
<p align="center"><sub><strong>07</strong> — New Project + default repo · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/07_tutorial_agent-colony.png">Full size</a></sub></p>

After **`contributors validate`** passes, paste both URLs:

```text
/board

Project: https://github.com/users/YOU/projects/N
Repo:    https://github.com/YOU/your-app
```

The agent fills **`project_ssot`** field ids and **`default_repo`**. Confirm before save. Then:

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/08_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/08_tutorial_agent-colony.png" alt="Agent chat /board with Project and repo URLs; github.collaboration.yaml Board Identity section updated" width="800" />
  </a>
</p>
<p align="center"><sub><strong>08</strong> — /board wire + YAML Board Identity · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/08_tutorial_agent-colony.png">Full size</a></sub></p>

```bash
python3 -m agent_colony project doctor
python3 -m agent_colony project status
# If doctor WARNs incomplete cards: project heal-cards --check  (then --apply if CLOSED+empty Status)
```

Expect `api=complete · shell=incomplete` until step 4.

Optional: `.local/user_settings/mcp.agents.yaml` · external MCP → **`/mcp-connect`**
(DeepWiki is seeded on activate; re-run `python3 -m agent_colony mcp seed --deepwiki` if needed)

---

## Step 4 detail — board shell (minimal 2-view or six-view default)

### Minimal 2-view (matches [Playground #3](https://github.com/users/SavinRazvan/projects/3))

**New installs:** activate auto-seeds `.local/user_settings/board-shell.schema.yaml`. **Existing installs:**

```bash
source .venv/bin/activate
python3 -m agent_colony project board-shell init --minimal
```

GitHub UI — two views only:

| View | Layout |
|------|--------|
| **Prioritized backlog** | Table + Tier-1 columns |
| **Status board** | Board · group by Status + Tier-1 columns |

Tier-1 columns on **both**: Priority, Size, Estimate, Start date, End date.

Agent chat: **`/board`** → CONSENT GATE → TURN PROTOCOL (Turn A + Turn B for minimal overlay).

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/09_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/09_tutorial_agent-colony.png" alt="First Project view after board wire; board agent instructions for Status board setup" width="800" />
  </a>
</p>
<p align="center"><sub><strong>09</strong> — First view + coach turn · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/09_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/10_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/10_tutorial_agent-colony.png" alt="Prioritized backlog and Status board views; board agent configuring Tier-1 columns" width="800" />
  </a>
</p>
<p align="center"><sub><strong>10</strong> — Two views + column setup · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/10_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/11_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/11_tutorial_agent-colony.png" alt="Board agent using in-IDE browser to configure GitHub Project views" width="800" />
  </a>
</p>
<p align="center"><sub><strong>11</strong> — Browser-in-IDE setup (continued) · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/11_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/12_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/12_tutorial_agent-colony.png" alt="Prioritized backlog view with Tier-1 columns visible" width="800" />
  </a>
</p>
<p align="center"><sub><strong>12</strong> — Prioritized backlog columns · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/12_tutorial_agent-colony.png">Full size</a></sub></p>

### Six-view Playground default

Skip the overlay copy; coach all six views per [views-setup.md](../../templates/project-board/views-setup.md).

### Verify (both paths)

```bash
source .venv/bin/activate
python3 -m agent_colony project board-bootstrap --check   # exit 0
python3 -m agent_colony project status
```

---

## Reference board (example)

These shots use the **Agent Colony kit repo** example Project after onboarding — your board fills in as you add cards. Not required on day 0; useful as a target layout.

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/13_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/13_tutorial_agent-colony.png" alt="Reference Prioritized backlog view with many cards on the Agent Colony board SSOT example project" width="800" />
  </a>
</p>
<p align="center"><sub><strong>13</strong> — Reference Prioritized backlog · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/13_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/14_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/14_tutorial_agent-colony.png" alt="Reference Status board with Ready through Done columns and sample cards" width="800" />
  </a>
</p>
<p align="center"><sub><strong>14</strong> — Reference Status board · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/14_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/15_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/15_tutorial_agent-colony.png" alt="Agent chat: board agent drafting sample cards with P0 P1 P2 priorities on the tutorial project" width="800" />
  </a>
</p>
<p align="center"><sub><strong>15</strong> — Draft cards (priority examples) · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/15_tutorial_agent-colony.png">Full size</a></sub></p>

---

## MCP smoke (DeepWiki)

DeepWiki is **seeded on activate** by default. Pattern A CLI + Agent chat (indexed repo: [karpathy/nanochat](https://deepwiki.com/karpathy/nanochat)):

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png" alt="Agent chat: ask DeepWiki MCP about karpathy/nanochat repository" width="800" />
  </a>
</p>
<p align="center"><sub><strong>16</strong> — DeepWiki in chat · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/16_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png" alt="Terminal: python3 -m agent_colony mcp call deepwiki ask_question success output" width="800" />
  </a>
</p>
<p align="center"><sub><strong>17</strong> — CLI mcp call PASS · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/17_tutorial_agent-colony.png">Full size</a></sub></p>

Detail: [connect-external-mcp.md § DeepWiki](connect-external-mcp.md#worked-example-deepwiki-zero-auth).

---

## Step 5 detail — daily workflow

*(After first-run board shell in step 4 when SSOT is on.)*

1. When `project_ssot.enabled`: `python3 -m agent_colony project status` (board first); else open `.local/index-and-planning/current/session-pointer.md`
2. Claim/update the board card (Status + Notes `@user/agent · <ISO-8601-UTC> · …`); local `plan.md` / `work-tracker.md` only as offline fallback under `board_only`; optional `history/continuity-index.md` (≥3-day local rollup)
3. If board writes hit GraphQL rate-limit (EXIT_QUEUED): `project outbox status` / later `outbox flush` — enable `project_ssot.outbox` defaults after activate
4. **`/implementer`** (or `/test-runner`, `/verifier`; `/auditor` only for architecture-impacting / pre-merge audits — not day-0 onboarding)
5. Canvas/plan (ADR-010): `canvas doctor` · `canvas sync --name <stem>` · `plan snapshot|list|open` — see [canvas-artifacts](../../.cursor/skills/canvas-artifacts/SKILL.md)
6. Dashboard (optional, **deprecated**): see [Control Center dashboards](#control-center-dashboards-deprecated) below

**Add your own agent/skill/MCP:** **`/integrator`** + **`/integrator-protocol`**

---

## Agent chat vs terminal

| Where | Use for | Examples |
|-------|---------|----------|
| **Agent chat** | Plugin install, subagents, skills, slash workflows | `/add-plugin …`, `/workflow-activate`, `/implementer`, `/review-pr` |
| **Terminal** | Validation, health, gates, serving deprecated dashboards | `python3 -m agent_colony health`, `http.server` → [dashboard URL](#control-center-dashboards-deprecated) |

**Rule:** `/add-plugin` and `/workflow-activate` are **chat commands** — do not paste them into bash.

### Agent chat — type `/` in Cursor

| Goal | Command |
|------|---------|
| Install plugin (once) | `/add-plugin https://github.com/SavinRazvan/agent-colony` |
| Activate / refresh kit | `/workflow-activate` |
| Implement a slice | `/implementer` |
| Tests / coverage | `/test-runner` |
| Verify claims | `/verifier` |
| Architecture audit | `/auditor` |
| Drift check | `/drift-guard` |
| Add agents/skills/MCP | `/integrator` |
| External MCP setup | `/mcp-connect` |
| PR workflow | `/review-pr` → `/prepare-pr` → `/merge-pr` |
| Attach file context | `@` + pick file (not for starting workflows) |

---

## Terminal commands cheat sheet

Run from **your activated project root** (`~/Projects/my-app`), not `agent-colony`.

```bash
cd ~/Projects/my-app
source .venv/bin/activate          # recommended; gates auto-use `.venv/bin/python` when present
```

| Command | When |
|---------|------|
| `python3 -m agent_colony activate --directory .` | First install, re-activate, or refresh dashboards |
| `python3 -m agent_colony contributors validate` | After editing `github.collaboration.yaml` — must PASS before PR |
| `python3 -m agent_colony health` | Quick layout + `kit_version` (no kit smoke pytest under `tests/` by default) |
| `python3 -m agent_colony integrate validate` | Agent/skill/MCP integration sanity (P0 = 0) |
| `python3 -m agent_colony gates` | Full smoke gates (pytest skipped when consumer has no tests/) |
| `python3 -m agent_colony drift validate` | Plan ↔ tracker coherence |
| `python3 -m agent_colony drift validate --profile consumer` | **Use on consumer apps** — no agent required; see [Drift on consumer apps](#drift-on-consumer-apps) |
| `python3 -m agent_colony project heal-cards --check` | Board SSOT: inventory empty Status / incomplete Tier-1 (`--apply` repairs CLOSED+empty→Done) |
| `python3 -m agent_colony mcp validate` | MCP config after edits |
| `python3 -m http.server 8000` | Serve dashboards — open http://localhost:8000/.local/agents-control-center/dashboards/index.html |

Commit trailer preview: `python3 -m agent_colony contributors commit-trailers`

---

## Control Center dashboards (deprecated)

> **Deprecated (2026-07-19).** Prefer the **GitHub Project board** when `project_ssot.enabled`
> (`python3 -m agent_colony project status`) and **Ctrl+Shift+P → Open Canvas** for kit
> visualizations. Local HTML under `.local/agents-control-center/` remains an **offline**
> markdown/tracker browser only; it is not the backlog or status SSOT (ADR-008).

Local HTML pages still ship on activate for legacy/offline use.

**Do not** open HTML via `file://` — browsers block `fetch()`.

From **project root**:

```bash
cd ~/Projects/my-app
python3 -m http.server 8000
```

**Open in browser:** http://localhost:8000/.local/agents-control-center/dashboards/index.html

*(Port busy? Use `8001` — swap the port in every URL below.)*

| Page | URL |
|------|-----|
| **Home** | http://localhost:8000/.local/agents-control-center/dashboards/index.html |
| **Implementation Control Center** | http://localhost:8000/.local/agents-control-center/dashboards/implementation-control-center.html |
| **Module audit** | http://localhost:8000/.local/agents-control-center/audits/module-audit.html |

### What still works (offline only)

- **Control Center** — sidebar tabs over local markdown (`session-pointer`, `plan`, …) and read-only board export snapshot
- **Module audit** — workflow module map HTML when exported

### Refresh after a kit update

Re-run activate (chat or terminal):

```text
/workflow-activate
```

```bash
python3 -m agent_colony activate --directory .
```

This overwrites kit-managed dashboard files with the latest templates from the plugin payload.

---

## PR lifecycle (summary)

1. Feature branch (`feature/`, `fix/`, `chore/`)
2. Implement + test → **`/review-pr`**
3. **`/prepare-pr`** (runs `prepare.py` → `resolve_gates()`)
4. **`/merge-pr`** (staged — stop here; branches may remain) · optional **`/full-pr-workflow`** → sync `main`, delete branch + `finalize.md`

Want the linked GitHub Issue closed automatically once cleanup finishes? Set `conventions.close_linked_issue_on_cleanup: true` in `.local/user_settings/github.collaboration.yaml` (default `false` — off unless you opt in; see `board-ssot` skill § "Issue state vs board Status").

Full checklist: [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) §6 · [workflow-complete.md](workflow-complete.md) §A.

---

## Architecture audit (summary)

For architecture-impacting work before merge prep:

1. **`/auditor`** with **`/auditor-protocol`**
2. Outputs under `.local/workflow-artifacts/enterprise-architecture-audit/`

Procedure: [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) §7 · [agent-workflow-procedures.md](agent-workflow-procedures.md) §1.

---

## Quick tips

| Do | Don't |
|----|-------|
| Open **your app** in Cursor | Activate while inside `agent-colony` |
| **`/workflow-activate`** in chat | Run `make gates` (kit-dev only) |
| Real paths like `~/Projects/my-app` | Literal `/path/to/your-project` |

---

## Verify (optional)

```bash
python3 -m agent_colony gates      # full gate pass
python3 -m agent_colony health     # layout + kit_version
```

Gate details: [gate-matrix.md](gate-matrix.md) (consumer scaffold = 4 checks).

---

## Kit clone path (advanced)

When not using the plugin UI — clone [agent-colony](https://github.com/SavinRazvan/agent-colony), then:

```bash
python3 -m venv .venv && .venv/bin/pip install -q -r requirements-dev.txt
export TARGET=~/Projects/my-app && mkdir -p "$TARGET"
.venv/bin/python -m agent_colony install \
  --target "$TARGET" --with-venv --with-mcp-json --verify
cd "$TARGET"
```

Dry-run preview: add `--dry-run`. Upgrade later: [upgrade-kit.md](upgrade-kit.md).

Architecture: [workflow-architecture.md](../architecture/workflow-architecture.md) · Layout: [local-workspace-layout.md](local-workspace-layout.md)

---

## Drift on consumer apps

Run from your project root. **No agent is required** before this command — `/drift-guard` is optional (writes advisory artifacts under `.local/workflow-artifacts/drift/`).

```bash
python3 -m agent_colony drift validate --directory . --profile consumer
```

Use **`--profile consumer`** for the minimal consumer set. When the tracker contains `STARTER-001` **and** `sync_policy: board_only`, auto-detect upgrades to **`consumer-board`** (or pass `--profile consumer-board` explicitly). Kit-dev repos stay on `--profile kit-dev` even when board_only is enabled.

| Profile | Checks |
|---------|--------|
| `consumer` | DRIFT-005 + DRIFT-008 |
| `consumer-board` | DRIFT-005 + DRIFT-008 + DRIFT-009 + DRIFT-010 |

Auto-detect defaults to **`kit-dev`** unless `work-tracker.md` contains `STARTER-001`; without the flag you may see kit-dev-only checks (DRIFT-003, DRIFT-006) that do not apply to your app.

| Check (consumer profile) | Meaning |
|--------------------------|---------|
| **DRIFT-005** | IMPLEMENTATION-STATUS test count — **not shipped to consumer installs** |
| **DRIFT-008** | Scaffold trackers (`session-pointer`, `plan`, `work-tracker`) present |

### DRIFT-005 FAIL — kit bug (not your app)

If you see:

```text
[P1] DRIFT-005 FAIL: IMPLEMENTATION-STATUS missing **Tests:** count
```

| Question | Answer |
|----------|--------|
| Is it your app's problem? | **No** — your install can be valid while this fails |
| Is it a kit bug? | **Yes** — the checker assumed a maintainer-only file exists |
| False positive? | **Yes** — `IMPLEMENTATION-STATUS.md` lives only in the **agent-colony** product repo |
| Who needs to fix it? | **Kit maintainers** (skip the check when the file is absent) |
| What should you do? | Re-run with `--profile consumer` after upgrading the kit; until then, treat DRIFT-005 as ignorable |

**Kit-dev vs consumer:** On the kit repo, DRIFT-005 compares `IMPLEMENTATION-STATUS.md` **Tests:** count to `pytest --collect-only` — that is real drift detection for maintainers. Consumer projects never ship that file, so the same check was a false failure on plugin installs (fixed on kit `main`: absent file → **PASS**, detail *skipped (consumer install)*).

After the kit fix, expect:

```text
[P2] DRIFT-005 PASS: IMPLEMENTATION-STATUS absent — test count check skipped (consumer install)
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `No module named 'agent_colony'` on first activate | **Expected** in empty app — run activate from kit **payload** (see § First activate troubleshooting above), not bare `python3 -m agent_colony` before install |
| VERIFY FAIL / missing pytest deps after activate | `source .venv/bin/activate && pip install -r requirements-dev.txt && python3 -m agent_colony activate --directory .` |
| `bash: /add-plugin: No such file or directory` | `/add-plugin` is **Agent chat only** — paste the GitHub URL in chat, not the terminal |
| Only `.cursor/settings.json` after plugin install | Normal — run **`/workflow-activate`** in your app folder for the full bundle |
| `contributors validate` FAIL | Replace placeholders in `github.collaboration.yaml` |
| YAML `ParserError` / traceback | Fix `human_coauthors` — keep `[]` or use a proper list; don't uncomment example lines as siblings of `[]` |
| Validate passes from kit repo but fails in your app | Run commands from **your project** (`cd ~/Projects/my-app`), not `agent-colony` |
| `pytest` not found | Re-run **`/workflow-activate`** (creates `.venv`) |
| Permission denied on `/path` | You used a placeholder path — create a real folder |
| Subagents/skills missing in **`/`** menu | Open **your activated project**, not `agent-colony`; re-run **`/workflow-activate`** if planes are incomplete |
| Control Center shows **Failed to fetch** | From project root: `python3 -m http.server 8000` then open http://localhost:8000/.local/agents-control-center/dashboards/index.html — not `file://` |
| Raw markdown (no tables/bold) in Control Center | Re-run **`/workflow-activate`** to refresh `local-markdown.js` |
| Stale dashboard UI after kit update | `python3 -m agent_colony activate --directory .` |
| `DRIFT-005 FAIL` on `drift validate --profile consumer` | **Kit bug (not your app)** — false positive when kit lacks the skip-if-absent fix; upgrade kit or ignore until fixed. See [DRIFT-005](#drift-005-fail--kit-bug-not-your-app) |
| `drift validate` without `--profile consumer` shows DRIFT-003/006 | Auto profile picked **kit-dev** — re-run with `--profile consumer` |
| `mcp validate` → typer required | Use `python3 -m agent_colony mcp validate` — not bare `mcp validate` |

---

## What’s on disk after install

```text
your-project/
├── AGENTS.md
├── .cursor/       agents, skills, rules
├── .agents/skills/   PR skills (/review-pr, /prepare-pr, …)
├── .ai_infra/     scripts + docs
├── .local/        trackers (gitignored)
├── agent_colony/
└── (app tests optional — kit leaves no tests/modules/smoke/ by default)
```

**CLI:** `source .venv/bin/activate && python3 -m agent_colony` from your project root.
