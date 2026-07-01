# MAS Workflow Kit

Universal **multi-agent workflow** infrastructure for Cursor — agents, skills, rules, PR scripts, `.local/` trackers, and optional MCP. Install into **your** project; this repo is **not** a standalone application.

| Audience | Start here |
|----------|------------|
| **Users (Marketplace / plugin)** | [Consumer quick start](#consumer-quick-start-marketplace) below |
| **Full onboarding** | [Consumer quickstart](.ai_infra/docs/operations/consumer-quickstart.md) (copied into your project on activate) |
| **Architecture** | [Workflow architecture](.ai_infra/docs/architecture/workflow-architecture.md) |
| **Kit maintainers** | [Developing the kit](#developing-the-kit-repo-only) — **not** for normal users |

---

## Consumer quick start (Marketplace)

**Prerequisites:** Cursor IDE, Python 3.11+ (`python3 --version`), a **target project folder** (new or existing repo — **not** this kit repo).

### Before you start — do and don't

| Do | Don't |
|----|-------|
| Open **your app project** in Cursor | Use `mas-workflow-kit` as your day-to-day workspace |
| Run **`workflow-activate`** in chat (recommended) | Run `make sync-plugin`, `make smoke-consumer`, or `make gates` — those are **kit-dev only** |
| Use a **real path** you created (e.g. `~/Projects/my-app`) | Copy `/path/to/your-project` or `/path` literally |
| Run `python3 -m cursor_workflow …` **from your project** after activate | Run `activate --directory .` while cwd is the kit repo (already installed; will skip) |
| Edit `.local/user_settings/github.collaboration.yaml` before your first PR | Ignore `contributors validate` — it fails until placeholders are replaced |

> **Marketplace live:** steps 1–2 below are enough; skip the terminal `KIT`/`TARGET` block unless you are dogfooding before listing approval.

### 1. Install the plugin

1. In Cursor: **Marketplace** (or `/add-plugin` while waiting for listing approval).
2. Search **`MAS Workflow Kit`** (publisher: Savin Ionuț Răzvan).
3. Install / enable the plugin.

> **Before Marketplace is live:** `/add-plugin` → select this repo root (must contain `.cursor-plugin/plugin.json`).

### 2. Activate the full bundle (three planes)

The plugin loads agents and skills into Cursor. **`workflow-activate`** (or `cursor_workflow activate`) copies infrastructure into **your project**.

| Plane | Installed paths | Loaded by Cursor? |
|-------|-----------------|-------------------|
| **Cursor contract** | `.cursor/`, `.agents/`, `AGENTS.md` | Yes — agents, skills, rules |
| **Infrastructure** | `.ai_infra/`, `cursor_workflow/` | No — scripts and CLI |
| **Runtime** | `.local/` Tier 1 scaffold (trackers, six `workflow-artifacts/*` buckets, dashboards) | No — gitignored |

Default profile: **`with_mcp`** (includes MCP server + merged `.cursor/mcp.json` + `.venv`).

**Recommended — in Cursor chat:**

1. Open your **target project** in Cursor (**not** `mas-workflow-kit`).
2. Run skill **`workflow-activate`**.
3. Wait for `VERIFY PASS: all gates green` and post-install plane status **ready**.

**Terminal — pre-launch dogfood only** (Marketplace users: use chat above instead):

```bash
export KIT=~/Projects/mas-workflow-kit    # where you cloned THIS repo
export TARGET=~/Projects/my-app           # YOUR project — create this folder
mkdir -p "$TARGET"

"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" \
  --source "$KIT/payload"
```

**Re-activate** (after `cursor_workflow` already exists in the target):

```bash
cd ~/Projects/my-app    # your project, not the kit repo
python3 -m cursor_workflow activate --directory .
```

`activate` is idempotent: safe to re-run; it does **not** overwrite `user_settings/`, trackers, `AGENTS.md`, or `pages.json`.

### 3. Personalize settings (required before PRs)

```bash
cd ~/Projects/my-app    # your activated project

# Edit placeholders → your real name and @handle:
#   .local/user_settings/github.collaboration.yaml
#   .local/user_settings/mcp.agents.yaml  (optional)

python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow integrate validate
```

### 4. Verify the install

```bash
python3 -m cursor_workflow gates
python3 -m cursor_workflow health
```

Expected on a **consumer** project:

- **Activate verify / `gates`:** testing artifacts, pytest, governance, debrand (doc facts auto-skipped when not kit-dev)
- **`integrate validate`:** P0 = 0 (14 checks; plugin bundle parity skipped on consumer)
- **`health`:** required paths present; reports `kit_version`

See [gate matrix](.ai_infra/docs/operations/gate-matrix.md) for prepare (2 universal) vs kit-dev (4) vs scaffold verify (4).

### 5. Start working

Read in order (paths are **in your project** after activate):

1. `.local/index-and-planning/current/session-pointer.md`
2. `plan.md` → `work-tracker.md`
3. `AGENTS.md` in the project root (created from kit stub on first install)

Open the local dashboard: `.local/agents-control-center/dashboards/` (tabs from `pages.json`).

---

## Add your own agents, skills, or MCP

Use the **integrator** agent — a Cursor chat agent, **not** a shell command:

1. In Cursor: **@** → **`integrator-mas-agent`**
2. Follow skill **`mas-infrastructure-integration`**
3. After changes, run **from your project root**:

```bash
python3 -m cursor_workflow integrate validate
python3 -m cursor_workflow contributors validate   # if pipelines or user_settings changed
python3 -m cursor_workflow gates
```

Procedure (shipped after activate): `.ai_infra/docs/operations/mas-infrastructure-integration.md`  
Checklist: `.ai_infra/templates/agent-integration/INTEGRATION-CHECKLIST.md`

**Modes:** MAS-integrated agents join slice/PR workflow; independent agents stay governed but off default pipelines (ADR-006).

**External MCP servers:** skill **`connect-external-mcp`** after activate.

---

## What you get after activate

| Layer | Contents |
|-------|----------|
| **Agents (7)** | `implementer`, `test-runner`, `verifier`, `enterprise-auditor`, `integrator-mas-agent`, `workflow-drift-guard`, `researcher` |
| **Skills (10)** | `workflow-activate`, `implementation-execution-loop`, `test-module-coverage`, `enterprise-architecture-audit`, `audit-orchestration`, `audit-module-map`, `workflow-drift-audit`, `mas-infrastructure-integration`, `connect-external-mcp`, `research-corpus-execution` |
| **Maintainer slash skills (5)** | `.agents/skills/`: `pr-workflow`, `review-pr`, `prepare-pr`, `merge-pr`, `audit-alignment` (redirect) |
| **Rules** | **6 universal** always-applied `.cursor/rules/*.mdc` |
| **Scripts** | `.ai_infra/scripts/pr/*` (review → prepare → merge) + governance, integration, drift checks |
| **`.local/`** | Gitignored — Tier 1 trackers + six `workflow-artifacts/*` buckets (Tier 2 filled at runtime) |
| **CLI** | `python3 -m cursor_workflow` — `activate`, `install`, `gates`, `health`, `mcp`, `contributors`, `integrate`, `drift`, `doc`, `verify` |
| **MCP** | `workflow-kit` server (profile `with_mcp`; `.venv` created on activate) |

Product-specific Cursor rules: copy from [`overlays/rules/`](overlays/README.md) into `.cursor/rules/` if needed.

---

## Pattern A — one script per maintainer action

Agents run **one command** per action; merge gates live in `prepare.py` only (**2** universal on consumer projects).

```bash
python3 .ai_infra/scripts/pr/prepare.py --pr <id|url> --pipeline default
```

See project `AGENTS.md` and `.agents/skills/pr-workflow/` after activate. Do not duplicate gate lists in chat — say *prepare gates green* or paste failing output only.

---

## Advanced install (no Marketplace)

For teams that clone the kit repo and install without the plugin UI (same bundle as generated `payload/`):

```bash
git clone https://github.com/SavinRazvan/mas-workflow-kit.git
cd mas-workflow-kit
python3 -m venv .venv
.venv/bin/pip install -q -r requirements-dev.txt

export TARGET=~/Projects/my-app
mkdir -p "$TARGET"

.venv/bin/python -m cursor_workflow install \
  --target "$TARGET" \
  --with-venv \
  --with-mcp-json \
  --verify
```

Preview only: add `--dry-run`. Details: [install dry-run](.ai_infra/docs/operations/install-dry-run.md).

Then `cd "$TARGET"` and continue from [step 3](#3-personalize-settings-required-before-prs) above.

---

## Developing the kit repo only

> **Consumers:** stop here — nothing below applies to your project.

For contributors to **mas-workflow-kit** (not consumer projects):

```bash
python3 -m venv .venv && .venv/bin/pip install -e ".[dev,mcp]"
make gates                    # 5 steps incl. doc facts on kit-dev
make smoke-consumer           # Track A + B consumer smoke
make sync-plugin && make check-plugin
```

Status and roadmap: [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) · Marketplace: [marketplace-publish](.ai_infra/docs/handoff/marketplace-publish.md)

---

## License

Apache License 2.0 — see [`LICENSE`](LICENSE) and [`NOTICE`](NOTICE).
