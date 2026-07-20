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
 - Pattern A: agents call scripts; merge gates via `resolve_gates()` in prepare.py (`GATES` = alias).
-->

# Consumer quickstart

Install **MAS Workflow Kit — Project SSOT** (`mas-workflow-kit-project-ssot`) into your project in a few minutes. No special git setup required.

**Product promise:** Install the plugin → open **your app repo** → **`/workflow-activate`** installs the **full kit** (agents, skills, rules, CLI, `.local/` scaffold). You only customize `.local/user_settings/github.collaboration.yaml` (your name, **your** GitHub Project field ids, `default_repo`). Same agent/board workflow as kit-dev after doctor/status pass. Board must be kit-shaped (Status + Priority + Size + Estimate **points** + Start date) — wiring + Size↔Estimate: [PLUGIN-USER-GUIDE § Product promise](PLUGIN-USER-GUIDE.md#product-promise) and `.cursor/skills/project-board-ssot/SKILL.md` § Tier-1.

> **Full manual:** [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) — plugin vs activate, complete file tree, use-case matrix, PR and audit chapters.

---

## First run (5 steps)

**Need:** Cursor · Python 3.11+ · **your project folder open in Cursor** (not the kit product repo `mas-workflow-kit-project-ssot`).

| Step | Action |
|------|--------|
| **1. Plugin** | In **Agent chat** (not terminal): `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` — or **Cursor → Marketplace** when listed |
| **2. Activate** | Open **your app folder** → Agent chat: **`/workflow-activate`** → wait for **`VERIFY PASS`** |
| **3. Your name** | Edit `.local/user_settings/github.collaboration.yaml` → set `display_name` + `github_user` → `python3 -m cursor_workflow contributors validate` |
| **3b. GitHub auth** (board SSOT) | `gh auth login` or `gh auth refresh -h github.com -s read:project,project` — grant **repo + Project** permissions. If no browser opens: copy the one-time code → open **https://github.com/login/device** → approve → return to terminal. Details: [PLUGIN-USER-GUIDE § GitHub CLI auth](PLUGIN-USER-GUIDE.md#github-cli-auth-projects). |
| **3c. Wire board** (board SSOT) | After auth: paste **Project URL + this repo URL** in Agent chat → **`/project-board`** proposes `project_ssot` ids + `default_repo` (you confirm). Or fill ids yourself via `gh project view` / `field-list`. |
| **4. Board shell** *(when `project_ssot.enabled`)* | Run `project doctor` (expect **ok**) then `board-bootstrap --check`. **Brand-new Project:** expect **FAIL** missing six views / `View 1` WARN — that is normal. Agent chat **`/project-board`** → follow [views-setup.md](../../templates/project-board/views-setup.md) in the GitHub UI → README paste or `--apply-readme` → re-run `--check` until green → `project status`. **Not** first-run: `/enterprise-auditor`. Details: [PLUGIN-USER-GUIDE § Consumer onboarding](PLUGIN-USER-GUIDE.md#consumer-project_ssot-onboarding-checklist). |
| **5. Build** | **`/implementer`** · when board SSOT on, Entry = `python3 -m cursor_workflow project status`; else `session-pointer.md` → `plan.md` → `work-tracker.md` |

**Healthy install?** `python3 -m cursor_workflow health` · with board on: `gh auth status` → `project doctor` → `project board-bootstrap --check`

**Update kit later (optional):** merge kit changes to `main` → in your app Agent chat `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` → `/workflow-activate` (or `python3 -m cursor_workflow activate --directory .`). Full force/semver: [upgrade-kit.md](upgrade-kit.md). **Does not** create GitHub Project views — finish step 4 for that.

> **Cheat sheet:** [Agent chat vs terminal](#agent-chat-vs-terminal) · [Dashboards (deprecated)](#control-center-dashboards-deprecated) · [All CLI commands](#terminal-commands-cheat-sheet)

### Step 1 detail — install plugin from GitHub

`/add-plugin` runs in **Cursor Agent chat only** — it is not a shell command.

```bash
/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot
```

Cursor shows an **Add Plugin** preview — click the **MAS Workflow Kit — Project SSOT** card to install:

![Install MAS Workflow Kit — Project SSOT from Agent chat — type /add-plugin with the GitHub URL, then click the plugin card](assets/mas-workflow-kit-install.png)

Optional — pin `main`:

```bash
/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot/tree/main
```

After install you may see only `.cursor/settings.json` in the project. That is expected — run **step 2** to copy the full bundle.

### In Agent chat — type `/`

Cursor lists **subagents**, **skills**, and **commands** in the same **`/`** menu ([Customize Cursor](https://cursor.com/docs/customize-cursor)). Names match the `name:` field in each file.

| What you want | Type in chat | Lives on disk |
|---------------|--------------|---------------|
| Activate the kit | **`/workflow-activate`** | `.cursor/skills/workflow-activate/` |
| First-run board shell | **`/project-board`** | `.cursor/agents/project-board.md` + `board-shell-onboard` |
| Implement a slice | **`/implementer`** | `.cursor/agents/implementer.md` |
| Run tests | **`/test-runner`** | `.cursor/agents/test-runner.md` |
| PR review / prepare / merge | **`/review-pr`**, `/prepare-pr`, `/merge-pr` | `.agents/skills/` (loaded as skills) |
| Extend agents/skills/MCP | **`/integrator-mas-agent`** + `/mas-infrastructure-integration` | agent + skill |
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

**What it does:** copies three planes into your project:

| Plane | What lands on disk |
|-------|-------------------|
| Cursor | `.cursor/`, `.agents/`, `AGENTS.md` |
| Infrastructure | `.ai_infra/`, `cursor_workflow/` |
| Runtime | `.local/` trackers + dashboards (gitignored) |

Also creates `.venv`, merges MCP config (profile **`with_mcp`**), runs smoke gates.

**Re-activate is safe:** won't overwrite your trackers, `user_settings/`, or `AGENTS.md`. Kit-managed **dashboard HTML**, JS/CSS, `module-audit.html`, and `pages.json` **are refreshed** on each activate (from plugin payload when available).

**Terminal equivalent** (same as `/workflow-activate`):

```bash
cd ~/Projects/my-app          # your activated project
source .venv/bin/activate     # after first activate
python3 -m cursor_workflow activate --directory .
```

To pull the latest dashboards after a kit update without a full reinstall:

```bash
python3 -m cursor_workflow activate --directory .
```

<details>
<summary><strong>Alternative: terminal activate (no plugin UI)</strong></summary>

```bash
export KIT=~/Projects/mas-workflow-kit-project-ssot
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
cd ~/Projects/my-app   # your activated project — not `mas-workflow-kit-project-ssot` (the kit product repo)
python3 -m cursor_workflow contributors validate   # must PASS before first PR
python3 -m cursor_workflow integrate validate      # optional; P0 must be 0
python3 -m cursor_workflow health
```

> **YAML tip:** Edit only `owner` at first. Do not uncomment `# - display_name: Alice Example` under `human_coauthors: []` — that causes a YAML syntax error. To add a co-author, replace `[]` with a proper list (see exemplar comments).

Optional: `.local/user_settings/mcp.agents.yaml` · external MCP → **`/connect-external-mcp`**

---

## Step 5 detail — daily workflow

*(After first-run board shell in step 4 when SSOT is on.)*

1. When `project_ssot.enabled`: `python3 -m cursor_workflow project status` (board first); else open `.local/index-and-planning/current/session-pointer.md`
2. Claim/update the board card (Status + Notes `@user/agent · <ISO-8601-UTC> · …`); local `plan.md` / `work-tracker.md` only as offline fallback under `board_only`; optional `history/continuity-index.md` (≥3-day local rollup)
3. If board writes hit GraphQL rate-limit (EXIT_QUEUED): `project outbox status` / later `outbox flush` — enable `project_ssot.outbox` defaults after activate
4. **`/implementer`** (or `/test-runner`, `/verifier`; `/enterprise-auditor` only for architecture-impacting / pre-merge audits — not day-0 onboarding)
5. Dashboard (optional, **deprecated**): see [Control Center dashboards](#control-center-dashboards-deprecated) below

**Add your own agent/skill/MCP:** **`/integrator-mas-agent`** + **`/mas-infrastructure-integration`**

---

## Agent chat vs terminal

| Where | Use for | Examples |
|-------|---------|----------|
| **Agent chat** | Plugin install, subagents, skills, slash workflows | `/add-plugin …`, `/workflow-activate`, `/implementer`, `/review-pr` |
| **Terminal** | Validation, health, gates, serving deprecated dashboards | `python3 -m cursor_workflow health`, `http.server` → [dashboard URL](#control-center-dashboards-deprecated) |

**Rule:** `/add-plugin` and `/workflow-activate` are **chat commands** — do not paste them into bash.

### Agent chat — type `/` in Cursor

| Goal | Command |
|------|---------|
| Install plugin (once) | `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit-project-ssot` |
| Activate / refresh kit | `/workflow-activate` |
| Implement a slice | `/implementer` |
| Tests / coverage | `/test-runner` |
| Verify claims | `/verifier` |
| Architecture audit | `/enterprise-auditor` |
| Drift check | `/workflow-drift-guard` |
| Add agents/skills/MCP | `/integrator-mas-agent` |
| External MCP setup | `/connect-external-mcp` |
| PR workflow | `/review-pr` → `/prepare-pr` → `/merge-pr` |
| Attach file context | `@` + pick file (not for starting workflows) |

---

## Terminal commands cheat sheet

Run from **your activated project root** (`~/Projects/my-app`), not `mas-workflow-kit-project-ssot`.

```bash
cd ~/Projects/my-app
source .venv/bin/activate          # recommended; gates auto-use `.venv/bin/python` when present
```

| Command | When |
|---------|------|
| `python3 -m cursor_workflow activate --directory .` | First install, re-activate, or refresh dashboards |
| `python3 -m cursor_workflow contributors validate` | After editing `github.collaboration.yaml` — must PASS before PR |
| `python3 -m cursor_workflow health` | Quick layout + `kit_version` check |
| `python3 -m cursor_workflow integrate validate` | Agent/skill/MCP integration sanity (P0 = 0) |
| `python3 -m cursor_workflow gates` | Full smoke gates (4 checks on consumer) |
| `python3 -m cursor_workflow drift validate` | Plan ↔ tracker coherence |
| `python3 -m cursor_workflow drift validate --profile consumer` | **Use on consumer apps** — no agent required; see [Drift on consumer apps](#drift-on-consumer-apps) |
| `python3 -m cursor_workflow mcp validate` | MCP config after edits |
| `python3 -m pytest -q tests/modules/smoke/` | Install smoke test |
| `python3 -m http.server 8000` | Serve dashboards — open http://localhost:8000/.local/agents-control-center/dashboards/index.html |

Commit trailer preview: `python3 -m cursor_workflow contributors commit-trailers`

---

## Control Center dashboards (deprecated)

> **Deprecated (2026-07-19).** Prefer the **GitHub Project board** when `project_ssot.enabled`
> (`python3 -m cursor_workflow project status`) and **Ctrl+Shift+P → Open Canvas** for kit
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
python3 -m cursor_workflow activate --directory .
```

This overwrites kit-managed dashboard files with the latest templates from the plugin payload.

---

## PR lifecycle (summary)

1. Feature branch (`feature/`, `fix/`, `chore/`)
2. Implement + test → **`/review-pr`**
3. **`/prepare-pr`** (runs `prepare.py` → `resolve_gates()`)
4. **`/merge-pr`** → sync `main`, delete branch

Full checklist: [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) §6 · [workflow-complete.md](workflow-complete.md) §A.

---

## Architecture audit (summary)

For architecture-impacting work before merge prep:

1. **`/enterprise-auditor`** with **`/enterprise-architecture-audit`**
2. Outputs under `.local/workflow-artifacts/enterprise-architecture-audit/`

Procedure: [PLUGIN-USER-GUIDE.md](PLUGIN-USER-GUIDE.md) §7 · [agent-workflow-procedures.md](agent-workflow-procedures.md) §1.

---

## Quick tips

| Do | Don't |
|----|-------|
| Open **your app** in Cursor | Activate while inside `mas-workflow-kit-project-ssot` |
| **`/workflow-activate`** in chat | Run `make gates` (kit-dev only) |
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

When not using the plugin UI — clone [mas-workflow-kit-project-ssot](https://github.com/SavinRazvan/mas-workflow-kit-project-ssot), then:

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

## Drift on consumer apps

Run from your project root. **No agent is required** before this command — `/workflow-drift-guard` is optional (writes advisory artifacts under `.local/workflow-artifacts/drift/`).

```bash
python3 -m cursor_workflow drift validate --directory . --profile consumer
```

Use **`--profile consumer`** for the minimal consumer set. When the tracker contains `STARTER-001` **and** `sync_policy: board_only`, auto-detect upgrades to **`consumer-board`** (or pass `--profile consumer-board` explicitly). Kit-dev repos stay on `--profile kit-dev` even when board_only is enabled.

| Profile | Checks |
|---------|--------|
| `consumer` | DRIFT-005 + DRIFT-008 |
| `consumer-board` | DRIFT-005 + DRIFT-008 + DRIFT-009 + DRIFT-010 |

Auto-detect defaults to **`kit-dev`** unless `work-tracker.md` contains `STARTER-001`; without the flag you may see kit-dev-only checks (DRIFT-003, DRIFT-006) that do not apply to your app.

| Check (consumer profile) | Meaning |
|--------------------------|---------|
| **DRIFT-005** | Maintainer handoff doc test count — **not shipped to consumer installs** |
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
| False positive? | **Yes** — `IMPLEMENTATION-STATUS.md` lives only in the **mas-workflow-kit-project-ssot** product repo |
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
| `bash: /add-plugin: No such file or directory` | `/add-plugin` is **Agent chat only** — paste the GitHub URL in chat, not the terminal |
| Only `.cursor/settings.json` after plugin install | Normal — run **`/workflow-activate`** in your app folder for the full bundle |
| `contributors validate` FAIL | Replace placeholders in `github.collaboration.yaml` |
| YAML `ParserError` / traceback | Fix `human_coauthors` — keep `[]` or use a proper list; don't uncomment example lines as siblings of `[]` |
| Validate passes from kit repo but fails in your app | Run commands from **your project** (`cd ~/Projects/my-app`), not `mas-workflow-kit-project-ssot` |
| `pytest` not found | Re-run **`/workflow-activate`** (creates `.venv`) |
| Permission denied on `/path` | You used a placeholder path — create a real folder |
| Subagents/skills missing in **`/`** menu | Open **your activated project**, not `mas-workflow-kit-project-ssot`; re-run **`/workflow-activate`** if planes are incomplete |
| Control Center shows **Failed to fetch** | From project root: `python3 -m http.server 8000` then open http://localhost:8000/.local/agents-control-center/dashboards/index.html — not `file://` |
| Raw markdown (no tables/bold) in Control Center | Re-run **`/workflow-activate`** to refresh `local-markdown.js` |
| Stale dashboard UI after kit update | `python3 -m cursor_workflow activate --directory .` |
| `DRIFT-005 FAIL` on `drift validate --profile consumer` | **Kit bug (not your app)** — false positive when kit lacks the skip-if-absent fix; upgrade kit or ignore until fixed. See [DRIFT-005](#drift-005-fail--kit-bug-not-your-app) |
| `drift validate` without `--profile consumer` shows DRIFT-003/006 | Auto profile picked **kit-dev** — re-run with `--profile consumer` |
| `mcp validate` → typer required | Use `python3 -m cursor_workflow mcp validate` — not bare `mcp validate` |

---

## What’s on disk after install

```text
your-project/
├── AGENTS.md
├── .cursor/       agents, skills, rules
├── .agents/skills/   PR skills (/review-pr, /prepare-pr, …)
├── .ai_infra/     scripts + docs
├── .local/        trackers (gitignored)
├── cursor_workflow/
└── tests/modules/smoke/
```

**CLI:** `python3 -m cursor_workflow` from your project root.
