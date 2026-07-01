# MAS Workflow Kit

Multi-agent workflow for Cursor — agents, skills, rules, PR scripts, and `.local/` trackers. Install into **your** project (not a standalone app).

| If you are… | Start here |
|-------------|------------|
| **New user** | [Get started in 4 steps](#get-started-most-users) below |
| **Want full detail** | [Consumer quickstart](.ai_infra/docs/operations/consumer-quickstart.md) (copied into your project after activate) |
| **Kit maintainer** | [Developing the kit](#developing-the-kit-repo-only) |

---

## Get started (most users)

**You need:** Cursor · Python 3.11+ (`python3 --version`) · a **project folder** (your app — **not** this `mas-workflow-kit` repo).

### 1. Install the plugin

- **Cursor → Marketplace** → search **MAS Workflow Kit** → Install  
- **Before Marketplace is live:** `/add-plugin` → select this repo root

### 2. Activate into your project

1. **File → Open Folder** → your app (e.g. `~/Projects/my-app`)
2. In Agent chat, run **`/workflow-activate`**
3. Wait for **`VERIFY PASS: all gates green`** and all planes **ready**

The plugin gives you subagents and skills in chat; **activate** copies the full kit into that folder (`.cursor/`, `.ai_infra/`, `.local/`, CLI).

### 3. Add your name (~1 min)

Open **`.local/user_settings/github.collaboration.yaml`** in your project and replace:

```yaml
owner:
  display_name: "Your Full Name"    # → your real name
  github_user: "@yourhandle"        # → e.g. @SavinRazvan
```

Then run (from **your project folder**, not the kit repo):

```bash
cd ~/Projects/my-app    # your activated project
python3 -m cursor_workflow contributors validate
```

Expected: `contributors validate: PASS`. Required before your first git commit or PR.

> **YAML tip:** Only change `owner.display_name` and `owner.github_user` at first. Leave commented `# - display_name:` examples commented — uncommenting them under `human_coauthors: []` breaks the file.

### 4. Start building

| Do this | How |
|---------|-----|
| Implement a feature | **`/implementer`** in Agent chat ([subagents](https://cursor.com/docs/subagents)) |
| Run tests / coverage | **`/test-runner`** |
| Add your own agent or skill | **`/integrator-mas-agent`** |
| Check install health | `python3 -m cursor_workflow health` |

> **In Agent chat:** type **`/`** — Cursor shows **subagents**, **skills**, and **commands** in one menu ([Customize](https://cursor.com/docs/customize-cursor)). Pick **`/workflow-activate`**, **`/implementer`**, **`/review-pr`**, etc. Use **`@`** only to attach files, docs, or git context — not to start kit workflows ([Prompting](https://cursor.com/docs/agent/prompting)).

Each session, read first: `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`

---

### Quick tips (common mistakes)

- **Open your app in Cursor** — not the `mas-workflow-kit` repo when activating
- **Use real paths** — e.g. `~/Projects/my-app`, never copy `/path/to/your-project` literally
- **Ignore `make …` commands** in this repo unless you are developing the kit itself

<details>
<summary><strong>Pre-launch: terminal activate (consumer trial)</strong></summary>

Skip this if Marketplace + **`/workflow-activate`** in chat works for you.

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

## What you get

After activate, your project includes:

- **7 agents** — `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `integrator-mas-agent`, `workflow-drift-guard`, `researcher`
- **10 skills** — activate, implementation loop, tests, audits, integration, MCP connect, …
- **6 universal rules** — always-on Cursor policy under `.cursor/rules/`
- **PR scripts** — review → prepare → merge under `.ai_infra/scripts/pr/`
- **`.local/` workspace** — trackers, dashboards, gitignored artifacts
- **CLI** — `python3 -m cursor_workflow` (`activate`, `gates`, `health`, `integrate`, …)

Optional product rules: [`overlays/rules/`](overlays/README.md)

---

## Git / PR workflow (when you use git)

1. Create a branch (`feature/…`, `fix/…`, or `chore/…`)
2. Work with **`/implementer`**; trackers live in `.local/index-and-planning/current/`
3. Before merge: `python3 .ai_infra/scripts/pr/prepare.py --pr <url> --pipeline default`

Details after activate: `AGENTS.md` and `.agents/skills/pr-workflow/`

---

## Advanced install (no Marketplace)

```bash
git clone https://github.com/SavinRazvan/mas-workflow-kit.git
cd mas-workflow-kit && python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt

export TARGET=~/Projects/my-app && mkdir -p "$TARGET"
.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" --with-venv --with-mcp-json --verify
cd "$TARGET"
```

Then continue from [step 3](#3-add-your-name-1-min) above. Preview: add `--dry-run`. See [install dry-run](.ai_infra/docs/operations/install-dry-run.md).

---

## Developing the kit repo only

> **Consumers:** you can ignore this section.

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,mcp]"
make gates && make smoke-consumer && make sync-plugin && make check-plugin
```

[IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) · [Marketplace / versioning](.ai_infra/docs/handoff/marketplace-publish.md)

---

## License

Apache 2.0 — [`LICENSE`](LICENSE) · [`NOTICE`](NOTICE)
