<p align="center">
  <img src="assets/agent-colony-logo.png" alt="Agent Colony" width="380" />
</p>

# Agent Colony

**Stop losing Status in chat.** Agent Colony installs a full multi-agent kit into *your* [Cursor](https://cursor.com) app repo — **8** agents, PR gates, and optional GitHub Project coordination so backlog and Status live on the board when you enable it.

<p align="center">
  <video src="https://github.com/user-attachments/assets/f9015ab5-28bf-47f7-a065-2127c098b80e" width="720" controls></video>
</p>

<p align="center"><em>Agent Colony at work</em></p>

| | |
|--|--|
| **Version** | [`0.6.7`](https://github.com/SavinRazvan/agent-colony/releases) · **Tests** · 1537 · **Agents** · 8 · **Skills** · 15 · **Rules** · **7 universal** · **License** · [Apache-2.0](LICENSE) |
| **Reference board** | [AI Project Playground](https://github.com/users/SavinRazvan/projects/3) |

---

## The problem

Agent chats lose Status. Trackers and docs drift. Teams re-explain the same slice every session.

## The solution

**Agent Colony** installs a full Cursor kit into *your* app repo (not this kit repo). When Project SSOT is on, the **GitHub Project** is the only writable place for backlog and Status — agents **enter** by reading the board and **exit** by updating Status and Notes. Local `.local/` holds gates, audits, and evidence — not a second Status writer.

**Proof:** 1537 tests · 8 agents · reference layout on [Playground #3](https://github.com/users/SavinRazvan/projects/3).

---

## What this is / is not

| | |
|--|--|
| **Is** | Installable Cursor workflow kit: 8 agents, PR gates, local evidence; optional GitHub Project coordination, MCP, and research packs |
| **Is not** | A new LLM runtime, chatbot framework, or hosted SaaS |

---

## Why teams use it

- **Optional board SSOT** — when enabled, backlog and Status stay on the GitHub Project; chat is execution, not the source of truth
- **Eight specialized agents** — implement, test, verify, audit, research, integrate, drift-check, board coach
- **PR gates** — prepare/merge evidence before ship
- **MCP-ready** — kit MCP server; DeepWiki seeded on consumer activate by default
- **Local evidence** — `.local/` for audits, coverage, and workflow artifacts (gitignored)

---

## Agents

| Agent | Job |
|-------|-----|
| `implementer` | Disciplined implementation slices with trackers and Pattern A gates |
| `test-runner` | Module-focused tests, regressions, and coverage |
| `verifier` | Check “done” claims against fresh evidence (try to disprove; no code fixes) |
| `auditor` | Deep/periodic evidence architecture audit (CHK-*; not plan pulse) |
| `researcher` | Brief-driven multi-round research packs; no product code |
| `integrator` | Integrate agents, skills, MCP expansions (procedural, Pattern A) |
| `drift-guard` | Continuous goal/plan/doctrine coherence + DRIFT scripts (handoff remediations only) |
| `board` | Wire Project SSOT, triage cards, and coach first-run board shell |

When `project_ssot.enabled`, agents **enter** by reading the board and **exit** by updating Status and Notes — see [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md).

Slash skills cover activate, update, board protocols, PR lifecycle (`/review-pr` → `/prepare-pr` → `/merge-pr`), and more — see the [Plugin User Guide](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md).

---

## Requirements

[Cursor](https://cursor.com) · Python 3.11+ · open **your app folder** (not this kit repo) · for board SSOT: [GitHub CLI](https://cli.github.com/) with Project access

**Full checklist:** [What you need — permissions & prerequisites](.ai_infra/docs/operations/permissions-and-prerequisites.md) (Cursor, `gh` scopes, git, MCP)

**For agents:** **Use ASD-STE100** (inspired by; not compliant) — [asd-ste100-prose.md](.ai_infra/docs/operations/asd-ste100-prose.md) · [token-efficiency.md](.ai_infra/docs/operations/token-efficiency.md)

---

## Install (consumers)

Screenshots are ~**1920×1080**. Each image displays at **800px** width — **click** to open full resolution, then use browser zoom (<kbd>Ctrl</kbd>+<kbd>+</kbd> / <kbd>−</kbd> or pinch). Full gallery: [consumer-quickstart § Visual walkthrough](.ai_infra/docs/operations/consumer-quickstart.md#visual-walkthrough).

### 1. Install the plugin (Agent chat)

In **Agent chat** (not the terminal):

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/01_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/01_tutorial_agent-colony.png" alt="Cursor Agent chat: type /add-plugin with the GitHub URL and review the Agent Colony preview card" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 1a</strong> — Preview card · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/01_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/02_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/02_tutorial_agent-colony.png" alt="Select your app project in Cursor and click Add Plugin" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 1b</strong> — Select project → <strong>Add Plugin</strong> · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/02_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/03_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/03_tutorial_agent-colony.png" alt="Agent Colony plugin installing in Cursor" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 1c</strong> — Installing · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/03_tutorial_agent-colony.png">Full size</a></sub></p>

### 2. Activate + identity

Open **your app folder** in Cursor. In **Agent chat**:

```text
/workflow-activate
```

Wait for **`VERIFY PASS`**, then set identity in `.local/user_settings/github.collaboration.yaml`:

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/04_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/04_tutorial_agent-colony.png" alt="Agent chat: type /workflow-activate and pick workflow-activate from the Agent Colony menu" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 2</strong> — Activate · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/04_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/05_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/05_tutorial_agent-colony.png" alt="After VERIFY PASS: edit github.collaboration.yaml display_name and github_user" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 3</strong> — Identity YAML · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/05_tutorial_agent-colony.png">Full size</a></sub></p>

```bash
source .venv/bin/activate
python3 -m agent_colony contributors validate
python3 -m agent_colony health
```

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/06_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/06_tutorial_agent-colony.png" alt="Terminal: python3 -m agent_colony contributors validate showing PASS" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Step 3</strong> — <code>contributors validate</code> PASS · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/06_tutorial_agent-colony.png">Full size</a></sub></p>

### 3. Board SSOT (optional)

When `project_ssot.enabled`, finish this ladder ([consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md) · [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md)):

1. Create a GitHub Project (default repo = your app) · **`gh auth status`**
2. **Wire board** — Agent chat **`/board`** + **Project URL** + **repo URL** → confirm YAML → `project doctor` + `project status`
3. **Board shell** — coach with **`/board`** until `project board-bootstrap --check` exits **0**
4. **Build** — **`/implementer`** (not day-0 **`/auditor`**)

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/08_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/08_tutorial_agent-colony.png" alt="Agent chat /board with Project and repo URLs; github.collaboration.yaml Board Identity section updated" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Wire board</strong> — <code>/board</code> + YAML ids · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/08_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/10_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/10_tutorial_agent-colony.png" alt="Board agent configuring Prioritized backlog and Status board views and Tier-1 columns" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Board shell</strong> — views + columns (agent-assisted) · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/10_tutorial_agent-colony.png">Full size</a></sub></p>

<p align="center">
  <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/14_tutorial_agent-colony.png" title="Open full resolution (1920×1080)">
    <img src="assets/img/tutorials_img/14_tutorial_agent-colony.png" alt="Reference Status board: Ready through Done columns with sample cards (kit repo example project)" width="800" />
  </a>
</p>
<p align="center"><sub><strong>Reference</strong> — Status board when shell is ready (kit example) · <a href="https://raw.githubusercontent.com/SavinRazvan/agent-colony/main/assets/img/tutorials_img/14_tutorial_agent-colony.png">Full size</a></sub></p>

**MCP (optional):** DeepWiki is seeded on activate — see [connect-external-mcp](.ai_infra/docs/operations/connect-external-mcp.md#worked-example-deepwiki-zero-auth).

**Ready when:** `health` passes after activate; **and** (if board SSOT is on) `board-bootstrap --check` exits **0** before day-to-day agents.

### 4. Upgrade kit (when a new release ships)

Upgrading is **two steps**: refresh the **plugin payload** in Cursor, then run **`update`** in **your app repo** terminal (not this kit repo).

#### Step A — Refresh the plugin (Cursor)

Distribution is **GitHub `/add-plugin`**, not an auto-updating Marketplace listing. A new git tag (e.g. [`v0.6.7`](https://github.com/SavinRazvan/agent-colony/releases)) does **not** change your local plugin cache until you re-add the plugin.

In **Agent chat** (your app project open):

```text
/add-plugin agent-colony@https://github.com/SavinRazvan/agent-colony
```

Plain URL form also works when discovery is healthy:

```text
/add-plugin https://github.com/SavinRazvan/agent-colony
```

Confirm the preview shows the **latest version** (see the badge at the top of this README). Re-add even if the plugin is already installed — Cursor stores a checkout under `~/.cursor/plugins/cache/agent-colony/…/payload/`.

**Optional (maintainers with a local kit clone):** skip Step A and point update at the clone:

```bash
export WORKFLOW_KIT_PAYLOAD=/path/to/agent-colony/payload
```

#### Step B — Update your app repo (terminal)

Open **your app folder** (e.g. `~/Projects/module-ai`), not `agent-colony`:

```bash
cd ~/Projects/your-app
source .venv/bin/activate

python3 -m agent_colony update --check --directory .
python3 -m agent_colony update --directory .
python3 -m agent_colony update --directory . --clean-only   # optional: runtime + orphan cleanup without upgrade
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```

Read the first lines of `--check`:

```text
installed=0.6.6
available=0.6.7
source=…/payload
action=upgrade
```

| Output | Meaning | What to do |
|--------|---------|------------|
| `available` **matches** latest release | Plugin cache is fresh | Run `update --directory .` |
| `available` **older** than [Releases](https://github.com/SavinRazvan/agent-colony/releases) | Stale plugin cache | Repeat **Step A**, then `--check` again |
| `installed` **newer** than `available` | Stamp ahead of payload (common after partial update) | Refresh plugin (Step A); do **not** assume you are on the latest kit |
| `action=heal` | Installed ≥ available — light heal only | Refresh plugin if you expected a full upgrade |
| `action=upgrade` | Source is newer — full kit copy | Run `update --directory .` once — **no `--force`** unless `--check` lists deltas you accept overwriting |
| `--check` exit **1** + kit-managed deltas | Local edits differ from payload | Review diffs; use `update --force` only if you accept overwrite |
| `--check` FAIL on `__pycache__` / orphans only | Pre-0.6.7 noise | Upgrade to **0.6.7+** or run `update --clean-only --directory .` |

Full refresh when `--check` lists kit-managed deltas you want overwritten:

```bash
python3 -m agent_colony update --check --directory .
python3 -m agent_colony update --directory . --force
```

**Do not** need `--force` when `--check` shows `action=upgrade` and exits 0 — one plain `update --directory .` is enough when the payload source is fresh. Kit **0.6.7+** runs pre/post cleanup automatically (`__pycache__`, kit orphans) on heal and upgrade.

Agent chat equivalent: **`/update-agent-colony`** (same version gate as terminal `update`).

#### Step C — Verify (your app repo)

All three must match the [latest release](https://github.com/SavinRazvan/agent-colony/releases):

```bash
cat .ai_infra/.kit-version
grep kit_version .ai_infra/manifest.yaml
python3 -m agent_colony update --check --directory .   # installed == available
test -f .ai_infra/docs/operations/multi-consumer-isolation.md && echo OK   # 0.6.6+ feature file
python3 -m agent_colony drift validate --profile consumer
```

Example on **0.6.7** (consumer update reliability):

```text
0.6.7
kit_version: "0.6.7"
installed=0.6.7
available=0.6.7
action=heal
check: PASS — kit version current
```

If `.kit-version` and `manifest.yaml` disagree, the upgrade did not finish cleanly — run `update --directory .` once more (same payload source).

| Flag / command | Role |
|----------------|------|
| `update --check` | Installed vs available + kit-managed diffs — **no writes** |
| `update --directory .` | **Heal** when current; **full upgrade** when `available` > `installed` |
| `update --force` | Full refresh from current `source` — run `--check` first |
| `WORKFLOW_KIT_PAYLOAD` | Use a local `payload/` tree instead of plugin cache |

**Preserved on upgrade:** `.local/user_settings/`, trackers, `AGENTS.md`, `mcp.user.json`. **Overwritten on full upgrade:** `.cursor/`, `.ai_infra/`, `agent_colony/` kit copy.

Details: [upgrade-kit.md](.ai_infra/docs/operations/upgrade-kit.md) · isolation: [multi-consumer-isolation.md](.ai_infra/docs/operations/multi-consumer-isolation.md)

---

## What happens next

| Topic | Go to |
|-------|--------|
| Identity / user settings | [PLUGIN-USER-GUIDE § Personalize](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#10-personalize-settings) |
| Board wire + shell | [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md) · [`board-shell`](.cursor/skills/board-shell/SKILL.md) |
| MCP (DeepWiki, custom servers) | [connect-external-mcp.md](.ai_infra/docs/operations/connect-external-mcp.md) |
| Research packs | [`research-corpus`](.cursor/skills/research-corpus/SKILL.md) · Guide [use-case matrix](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#6-use-case-matrix) |
| Upgrade an existing install | Step A: `/add-plugin` (refresh cache) → Step B: `update --check` then `update --directory .` · [§4 Upgrade kit](#4-upgrade-kit-when-a-new-release-ships) · [upgrade-kit.md](.ai_infra/docs/operations/upgrade-kit.md) |
| Three planes (architecture) | [workflow-architecture.md](.ai_infra/docs/architecture/workflow-architecture.md) |

---

## Kit maintainers

Developing **this** repository? See **[CONTRIBUTING.md](CONTRIBUTING.md)** (clone, venv, gates), then **[AGENTS.md](AGENTS.md)** for agent doctrine.

---

## Documentation map

| Doc | Audience |
|-----|----------|
| [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md) | Consumers — 5-step install |
| [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) | Consumers — full manual |
| [Abbreviations notepad](.ai_infra/docs/operations/abbreviations-notepad.md) | Consumers + kit-dev — glossary (SSOT, DRIFT, Pattern A, agents) |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Kit-dev setup |
| [AGENTS.md](AGENTS.md) | Kit-dev agent doctrine |
| [Docs index](.ai_infra/docs/README.md) | Full `.ai_infra/docs/` navigation |
| [repository-map](.ai_infra/docs/handoff/repository-map.md) | Kit vs payload vs consumer install |
| [assets/](assets/README.md) | Logo, video, tutorial screenshots |

---

## License

Apache 2.0 — [LICENSE](LICENSE) · [NOTICE](NOTICE)
