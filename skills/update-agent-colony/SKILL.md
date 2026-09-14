---
name: update-agent-colony
description: Upgrade an already-activated consumer workspace to the latest kit payload (version-gated heal vs full refresh).
---
<!--
File: SKILL.md
Path: .cursor/skills/update-agent-colony/SKILL.md
Role: Consumer-facing kit upgrade after Marketplace/plugin bump (ADR-001 Option B follow-on).
Used By:
 - PLUGIN-USER-GUIDE.md
 - upgrade-kit.md
 - sync_plugin_bundle.py (canonical; template fallback at .ai_infra/templates/plugin/skills/)
Depends On:
 - .ai_infra/install/agent_colony/update_cli.py
 - .cursor/skills/workflow-activate/SKILL.md (first install only)
Notes:
 - Pattern A: one script command per action. First install remains /workflow-activate.
-->

# Update Agent Colony

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## When

User ran **`/workflow-activate`** in **their app**, then updated the Agent Colony plugin and needs kit-managed files refreshed.

**Not for first install** — use [workflow-activate](workflow-activate/SKILL.md) when `.ai_infra/` is missing.

## Guide the user

1. Confirm folder is **their activated app**, not kit-dev repo.
2. **Refresh plugin first** (Agent chat): `/add-plugin agent-colony@https://github.com/SavinRazvan/agent-colony` — confirm preview version matches [Releases](https://github.com/SavinRazvan/agent-colony/releases).
3. Prefer **`/update-agent-colony`** or Pattern A command below.
4. Version gate:
   - **same / newer installed** → light heal (`.gitignore`, `STARTER-001`, missing `.venv`, leftover `.local/agents-control-center/` cleanup)
   - **`available > installed`** → one full scaffold refresh (payload `scaffold.py`; no `--force` unless `--check` lists deltas)
   - **`--force`** → full overwrite even when versions match, or when accepting kit-managed delta overwrites
5. **Verify:** `.kit-version`, `manifest.yaml` `kit_version`, and `python3 -m agent_colony update --check --directory .` `installed`/`available` all match.
6. After upgrade: `health` + `mcp validate`.

## Commands (copy/paste)

Give the user **full commands**, not flags alone. Run in **their app**, after plugin refresh.

**Happy path:**

```bash
cd ~/Projects/your-app
source .venv/bin/activate
python3 -m agent_colony update --check --directory .
python3 -m agent_colony update --directory .
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```

**Cleanup only** (no version bump):

```bash
cd ~/Projects/your-app
source .venv/bin/activate
python3 -m agent_colony update --directory . --clean-only
```

**Overwrite kit-managed deltas** (only if `--check` lists files they accept losing):

```bash
cd ~/Projects/your-app
source .venv/bin/activate
python3 -m agent_colony update --check --directory .
python3 -m agent_colony update --directory . --force
```

**Lite → full kit:**

```bash
cd ~/Projects/your-app
source .venv/bin/activate
python3 -m agent_colony update --force --profile with_mcp --directory .
```

**Stay on lite** after a kit bump:

```bash
cd ~/Projects/your-app
source .venv/bin/activate
python3 -m agent_colony update --profile consumer_lite --force --directory .
```

Debug — skip pre/post cleanup: `python3 -m agent_colony update --directory . --no-clean`.

> **Warning — plain `update` upgrades lite to full.** `update --directory .` (no `--profile`) uses default **`with_mcp`**. On version bump it restores 16 skills and 8 agents. To **preserve lite**, pass `--profile consumer_lite` on update or re-run activate with that profile.

| Command (after `cd` + `source .venv/bin/activate`) | Profile used | Lite tree after version upgrade |
|---------|--------------|--------------------------------|
| `python3 -m agent_colony update --directory .` | `with_mcp` (default) | **Full kit** (16 skills, 8 agents) |
| `python3 -m agent_colony update --profile consumer_lite --force --directory .` | `consumer_lite` | **Lite** (6 skills, 6 agents) |
| `python3 -m agent_colony update --force --profile with_mcp --directory .` | `with_mcp` | **Full kit** (explicit upgrade) |

See [consumer-lite-profile.md](../../.ai_infra/docs/operations/consumer-lite-profile.md).

**Token-efficient verify:**

```bash
python3 -m agent_colony health --summary
python3 -m agent_colony drift validate --profile consumer --summary
```

**Source resolution:** `WORKFLOW_KIT_PAYLOAD` → `./payload/` → kit/plugin `payload/` (highest `kit_version` complete tree) → `--source`.

## What update does

| Condition | Action |
|-----------|--------|
| No `.ai_infra/` or missing `.kit-version` | Fail — run `/workflow-activate` |
| `installed == available` (not `--force`) | Light heal only |
| `available > installed` or `--force` | Full scaffold refresh |

**Auto-clean (0.6.7+):** pre/post cleanup removes runtime noise (`__pycache__/`, `*.pyc`) and kit-managed orphans on heal and upgrade.

**`update --check`:** compares payload files to your workspace. **Fails** only on byte diffs for paths present in both trees (real local edits). **Warns** on integrator extra agents and orphan files left from older kits (`__pycache__/`, `.kit-version`, and target-only paths are ignored). When `action=heal` and versions match, exit **0** unless kit files were edited.

**`--clean-only`:** run cleanup + check report without scaffold (no version bump).

**Preserved:** `AGENTS.md` (if present), `mcp.user.json`, `.local/user_settings/`, trackers.

**Overwritten on upgrade:** `.cursor/agents|rules|skills`, `.ai_infra/scripts`, `agent_colony/` CLI, `.kit-version`.

## Post-update

```bash
cd ~/Projects/your-app
source .venv/bin/activate
cat .ai_infra/.kit-version
grep kit_version .ai_infra/manifest.yaml
python3 -m agent_colony update --check --directory .
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```

Optional: `integrate validate`, `canvas doctor`. Breaking renames: [upgrade-kit.md](../../.ai_infra/docs/operations/upgrade-kit.md).

## Anti-patterns

- Run `update --force` when `action=upgrade` and `--check` exits 0 — one plain `update` is enough.
- Re-run plain `/workflow-activate` expecting agents/skills refresh — heals only when planes ready.
- Overwrite consumer `user_settings` or invent second Status writer under `board_only`.
- Run `update --force` in **kit-dev repo** — fails (`forbidden in slim install`). Kit-dev: edit sources → `make sync-plugin` → commit.
