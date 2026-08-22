# Upgrade Agent Colony

Re-run install from a **newer kit source** (git tag, plugin payload, or local clone) into the same consumer project.

## Breaking change (0.6.0)

Kit **0.6.0** renames the Python CLI module and console script:


| Before (removed)            | After                             |
| --------------------------- | --------------------------------- |
| `python -m cursor_workflow` | `python -m agent_colony`          |
| Console script `cursor-workflow` | `agent-colony`               |
| Root package dir `cursor_workflow/` | `agent_colony/`             |
| Install package `.ai_infra/install/cursor_workflow/` | `.ai_infra/install/agent_colony/` |


**Cold cut** — old names are not aliased. After upgrading:

1. Re-run `/workflow-activate` or `python -m agent_colony activate --directory .`
2. Reinstall editable tooling: `pip install -e ".[dev,mcp]"` (kit-dev) so the `agent-colony` console script is on PATH
3. Update any local scripts/CI that still call the old module or console script



## Breaking change (0.6.1)

Kit **0.6.1** renames the MCP Python package (Cursor server id unchanged):


| Before (removed)            | After                                     |
| --------------------------- | ----------------------------------------- |
| `python -m workflow_mcp`    | `python -m agent_colony_mcp`              |
| Package dir `.ai_infra/mcp_servers/workflow_mcp/` | `.ai_infra/mcp_servers/agent_colony_mcp/` |
| Cursor server id            | `agent-colony-mcp` (**unchanged**)        |


Update `.cursor/mcp.json` `args` to `["-m", "agent_colony_mcp"]` (or re-run activate / `mcp seed`). MCP **tool** names such as `workflow_`* are unchanged.

## Changes in 0.6.2

Kit **0.6.2** hardens board Status + Tier-1 completeness (no rename):

- `create-from-template` defaults Status to `ready`; Size/Estimate writes FAIL when `field_id` is configured
- `validate-item` / `doctor` flag empty Status and incomplete Tier-1 (no early-return skip)
- `project heal-cards --check|--apply|--fill-tier1` inventories and repairs CLOSED+non-Done / empty Status cards
- `close-linked-issue` requires board Status=`done` before closing the GitHub Issue
- merge board sync queues `set-status` / Notes on queueable GraphQL failures (EXIT_QUEUED / outbox)
- Consumer activate no longer leaves `tests/modules/smoke/test_kit_installed.py` by default (`--keep-smoke-test` opt-in)

Consumers: `python3 -m agent_colony update` after the plugin marketplace refreshes to **0.6.2**.

## Changes in 0.6.3

Kit **0.6.3** adds agent-written **End date** (mirror of Start date):

- Auto-set UTC End date when Status becomes **Done** if empty (`conventions.set_end_date_on_done`, default true)
- Wired on `set-status` / `handoff` / merge board sync / `heal-cards --apply` / outbox flush
- `validate-item` / `doctor` / `heal-cards --check` flag missing End date on Done cards
- Board shell Tier-1: End date required field + visible on Status board / Prioritized backlog

Consumers: `python3 -m agent_colony update` after the plugin marketplace refreshes to **0.6.3**. Show **End date** on Status board and Prioritized backlog if `board-bootstrap --check` fails on columns.

## Changes in 0.6.4

Kit **0.6.4** ships token-efficient agent prose and board Entry reliability (no rename):

- ASD-STE100-inspired banners on agents, skills, and rules; governance fails CI if agent/skill banners missing
- Token-efficiency read contract (`project entry --digest`, thin skills index)
- `project entry`: retry GraphQL rate-limit probe once; prefer conserve over false offline when snapshot exists
- `--last` rejects corrupt/placeholder `PVTI_` ids; `project guide` prints `(invalid — recreate)`
- Day-0 / Day-N heal-cards playbook: Done missing End date = hygiene; Ready empty = create/claim

Consumers: `python3 -m agent_colony update` after the plugin refreshes to **0.6.4**.

## Changes in 0.7.0

Kit **0.7.0** ships the **Token Efficiency Program** and optional **`consumer_lite`** install profile (no rename):

- **`consumer_lite` profile** — 6 agents, 6 skills, `AGENTS.stub-lite.md`; marker `.local/generated-data/install-profile.json`; no `board-shell` skill (first-run inline in `board.md`)
- **Rules tiering** — 7 rule files: **4** `alwaysApply: true` + **3** requestable (`commit-trailer-format`, `file-docstring-header-relations`, `advisory-audit-alignment-enforcement`)
- **Token-efficient CLI** — `doc skill-section`, `doc validate-thin-index --summary`, `health --summary`, `drift validate --summary`, `project doctor --digest`, `project entry --digest`
- **MCP** — `workflow://skills/{skill_id}/{section_slug}` resource; `workflow_run_prepare(..., summary=True)`
- **DRIFT-014/015/016** — thin-index, agent card size, lite profile markers (profile-aware)
- **GOV-TOKEN-001/002, GOV-RULES-001** — governance checks for token program

Consumers: refresh plugin → `python3 -m agent_colony update --check` → `update --directory .`. New lite installs:

```bash
python3 -m agent_colony activate --directory . --profile consumer_lite
```

Upgrade lite → full: `python3 -m agent_colony update --force --profile with_mcp --directory .`

**Verify:** `python3 -m agent_colony health --summary` · `drift validate --profile consumer --summary`

## Changes in 0.7.1

Kit **0.7.1** extends **`consumer_lite`** (no rename):

- **`agents_skill_allowlist`** — lite keeps PR slash skills only (`review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `full-pr-workflow`); prunes `audit-alignment` and legacy root MD files
- **Plain `update` behavior documented** — default `--profile with_mcp` upgrades lite → full on version bump; use `--profile consumer_lite` to stay lite

Consumers on lite: read [consumer-lite-profile.md](consumer-lite-profile.md) § Upgrade before running plain `update`.

## Changes in 0.6.7

Kit **0.6.7** ships consumer update reliability (no rename):

- **`kit_cleanup.py`** — pre/post cleanup on heal and upgrade: removes `__pycache__/` and `*.pyc` under `.ai_infra/` and `agent_colony/`; prunes kit-managed orphan files not in payload
- **`update --clean-only`** — cleanup + `--check` report without scaffold (useful on existing installs before full upgrade)
- **`update --no-clean`** — skip pre/post cleanup (debug escape hatch)
- **`discover_cursor_plugin_payload`** — picks highest `kit_version` complete payload (cache > marketplaces > local); rejects incomplete marketplace checkouts
- **`update --check`** — ignores `.kit-version`, `__pycache__/`, `*.pyc`; orphans warn only; exit **0** on heal when versions match
- **`project list --status "In progress"`** — space normalization fix

Consumers: refresh plugin → `python3 -m agent_colony update --check` → `update --directory .` after **0.6.7** is available.

**Verify after upgrade:** `.kit-version`, `manifest.yaml` `kit_version`, and `update --check` `installed` / `available` must all match. One `update --directory .` is enough — no second run or `--force` for normal version bumps.

## Changes in 0.6.6

Kit **0.6.6** ships multi-consumer isolation (Model A):

- SSOT doc [multi-consumer-isolation.md](multi-consumer-isolation.md) — preserve vs overwrite, hard rules, consumer CI template
- **DRIFT-013** — P1 fail when git tracks `.local/`, `.venv/`, `.env`, or `mcp.user.json` (consumer exit code enforced)
- **DRIFT-011b** — P2 advisory for extra integrator agents
- **`update --check`** — diffs `kit_managed_globs` from install-contract; fails on heal or upgrade when kit-managed files differ
- Overlay collision WARN on activate; `product-*.mdc` naming in `overlays/README.md`
- **`update` uses payload `scaffold.py`** — upgrades from older kits no longer run the consumer's stale install script; `.kit-version` is reconciled to `available` after scaffold

Consumers: refresh plugin → `python3 -m agent_colony update --check` → `update --directory .` after **0.6.6** is on Marketplace.

**Verify after upgrade:** `.kit-version`, `manifest.yaml` `kit_version`, and `update --check` `installed` / `available` must all match. If `.kit-version` lags (e.g. stamp `0.6.4` but manifest `0.6.6`), run `update --directory .` again — do not assume `--force` is required when `action=upgrade`.

## Changes in 0.6.5

Kit **0.6.5** fixes consumer `update` leaving a stale `.kit-version` stamp (no rename):

- `scaffold.py` loads profile and `kit_version` from **source** manifest (not pre-copy target manifest)
- `update_cli.py` `ensure_kit_version_stamp()` repairs stamp after successful upgrade when scaffold skipped write
- Regression tests: consumer-context subprocess scaffold + stale-stamp update path

Consumers: `python3 -m agent_colony update` after the plugin refreshes to **0.6.5**. If `.kit-version` lags `manifest.yaml` on 0.6.4, run update once or `echo <kit_version> > .ai_infra/.kit-version`.

## Consumer heal (activate hardening on main → next tag)

If an older activate left only MCP secret lines in `.gitignore`, or omitted the consumer `STARTER-001` drift marker:

1. Re-run `source .venv/bin/activate && python3 -m agent_colony update --directory .`  
   (when up to date: heals `.gitignore` for `.local/` + `.venv/`, seeds `STARTER-001`, creates missing `.venv`; when source newer: full kit refresh). Plain `activate` also heals when planes are ready.
2. If `.venv/` or `.local/` were already committed: keep the healed `.gitignore`, then  
   `git rm -r --cached .venv .local` and commit app sources (`src/`, `pyproject.toml`, …) instead.
3. MCP tool rename: `workflow_mcp_connection_guide` → `workflow_agent_colony_mcp_connection_guide` (re-copy exemplar `mcp.agents.yaml` tools_hint or edit locally).

## Before upgrade

1. Note current version: `cat .ai_infra/.kit-version`
2. **Refresh the Cursor plugin** (Agent chat): `/add-plugin agent-colony@https://github.com/SavinRazvan/agent-colony` — confirm preview version matches [Releases](https://github.com/SavinRazvan/agent-colony/releases)
3. Commit or stash local changes (especially `.cursor/`, `.ai_infra/`, `.local/`)
4. Back up custom overlays under `overlays/rules/` and any `mcp.user.json` secrets



## Upgrade command

**Preferred (version-gated):**

```bash
cd ~/Projects/my-app    # your activated project
source .venv/bin/activate
python3 -m agent_colony update --check --directory .
python3 -m agent_colony update --directory .
# or Agent chat: /update-agent-colony
```

**Verify:** `cat .ai_infra/.kit-version` and `grep kit_version .ai_infra/manifest.yaml` must match; `update --check` should show `installed` == `available` (exit **0**, `action=heal`). One `update` is enough when `action=upgrade` and `--check` exits 0 — reserve `--force` for kit-managed deltas you choose to overwrite.

```bash
python3 -m agent_colony health
python3 -m agent_colony drift validate --profile consumer
```

**Optional (0.6.7+):** `python3 -m agent_colony update --clean-only --directory .` — cleanup `__pycache__` and kit orphans without scaffold. **`--no-clean`** skips auto cleanup (debug only).

Compares `.ai_infra/.kit-version` to the activate source `manifest.yaml` `kit_version`:

| Result | Action |
|--------|--------|
| Up to date | Light heal — dashboards, runtime `.gitignore`, `STARTER-001`, missing `.venv` |
| Source newer | Full kit-managed refresh (agents/rules/skills/scripts) |
| `--check` | Report only (no writes) |
| `--force` | Full refresh even when versions match |

Same as Agent chat **`/update-agent-colony`**. See [update-agent-colony skill](../../.cursor/skills/update-agent-colony/SKILL.md).

**Kit-dev product repo:** do not run `update --force` here (scaffold is consumer-only and will refuse). Sync mirrors with `make sync-plugin` instead. Light `update` / heal on kit-dev refreshes dashboards only and does not overwrite authoring `install/` from `payload/`.

**Plan orphans:** only `*.plan.md` files (via `plan snapshot`) are indexed under `.local/plans/`. Plain `.md` files in that folder are ignored by `plan list` — delete them or re-snapshot with `--from`.

**Advanced aliases** (same underlying scaffold paths):

```bash
# Light heal only (no version compare) — also what plain re-activate does when planes are ready
python3 -m agent_colony activate --directory .

# Full reinstall without version gate
python3 -m agent_colony activate --directory . --force
```

**Kit clone / advanced** — from kit repo:

```bash
export TARGET=~/Projects/my-app
.venv/bin/python -m agent_colony install \
  --target "$TARGET" \
  --source . \
  --profile with_mcp \
  --with-mcp-json \
  --verify
```

Use `--source payload` when running from the distribution root (see `workflow-activate` skill).

## What install updates


| Area                            | Behavior                                                                           |
| ------------------------------- | ---------------------------------------------------------------------------------- |
| `.ai_infra/scripts/`            | Overwritten from manifest profile                                                  |
| `.cursor/agents`, rules, skills | Overwritten from kit                                                               |
| `.local/` exemplars             | Re-copied on `--force` only; light re-activate refreshes dashboards + `pages.json` |
| Dashboard HTML / `pages.json`   | Refreshed on every `activate` (idempotent)                                         |
| `AGENTS.md`                     | **Not** overwritten if present — delete to refresh from stub, or merge manually    |
| `mcp.user.json`                 | **Not** overwritten — merge via `python3 -m agent_colony mcp validate`             |
| `.kit-version`                  | Updated from **source** manifest `kit_version` (not pre-copy target manifest)      |




## After upgrade

```bash
cd ~/Projects/my-app
python3 -m agent_colony gates
python3 -m agent_colony health
python3 -m agent_colony mcp validate
```



## Rollback

1. Restore project from git to pre-upgrade commit
2. Or reinstall from previous kit tag/payload matching old `.kit-version`

Document intentional divergences in `.local/index-and-planning/current/updates-log.md`.