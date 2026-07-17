<!--
File: marketplace-publish.md
Path: .ai_infra/docs/handoff/marketplace-publish.md
Role: Checklist for building and publishing the MAS Workflow Kit Cursor plugin.
Used By:
 - REFACTOR-006
Depends On:
 - .ai_infra/scripts/release/sync_plugin_bundle.py
 - .cursor-plugin/plugin.json
Notes:
 - ADR-001 Option B: payload + workflow-activate skill.
-->

# Marketplace publish checklist

**Product:** MAS Workflow Kit · **Plugin id:** `mas-workflow-kit`

## Pre-publish (kit repo)

Use the kit venv interpreter (`.venv/bin/python`) or `python3` — bare `python` is not guaranteed on Linux/WSL.

1. `make gates` — kit repo green
2. `make install-dry-run` — consumer install green
3. `make smoke-consumer` — Track A + Track B PASS (see [Automated smoke](#automated-smoke-kit-repo)); record findings under `.local/workflow-artifacts/release/`
4. `make sync-plugin` — rebuild `agents/`, `rules/`, `skills/`, `payload/` (commit the result)
5. `make check-plugin` — bundle parity green
6. `.venv/bin/python .ai_infra/scripts/architecture/check_debrand.py`
7. [x] Bump **all version SSOT fields together** (see [Versioning](#versioning) below) — **done** 0.3.0 → 0.4.0 (2026-07-02)
8. [x] `assets/logo.png` (1:1, background plate) — see `assets/README.md` — **present** (commit `1f16af1`, 1024×1024 PNG RGBA, ~1.5 MB; verified 2026-07-02)
9. [x] Manual `/workflow-activate` UI smoke (Cursor chat `/` menu, real project) — **PASS 2026-07-08**
   on **Smart-Notes** (`~/Projects/Smart-Notes`): chat activate + terminal matrix green. Evidence:
   `.local/workflow-artifacts/release/smoke-consumer-smart-notes-2026-07-08.md`,
   `workflow-activate-ui-smoke.md`, `workflow-activate-live-ui-runbook.md` (Phases B–C filled).
   CLI-equivalent path double-verified 2026-07-02. Optional: empty-folder rerun (`mas-ui-smoke-test`).

## Versioning

**Current release:** `0.4.0` (git tag `v0.4.0`).

**Superseded:** `v0.3.0` (`1f16af1`) predates `PLUGIN-FLATTEN` (#15) — its tagged tree has **zero**
files under `agents/`, `rules/`, `skills/`, `payload/` (the gitignore bug #15 fixed). Do not
reference `v0.3.0` as an installable release; `v0.4.0` is the first tag with a functional plugin
bundle committed.

On every release, bump **in lockstep**:

| File | Field |
|------|--------|
| `.cursor-plugin/plugin.json` | `version` |
| `pyproject.toml` | `version` |
| `cursor_workflow/__init__.py` | `__version__` |
| `cursor_workflow/cli.py` | `__version__` |
| `.ai_infra/install/cursor_workflow/__init__.py` | `__version__` |
| `.ai_infra/install/cursor_workflow/cli.py` | `--version` string |
| `.ai_infra/__init__.py` | `__version__` |
| `.ai_infra/manifest.yaml` | `kit_version` |
| `.ai_infra/.kit-version` | raw version string (kit-dev repo's own checked-in copy — see note below) |
| `.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md` | header + kit version row |
| `tests/modules/install/test_install_contract.py` | `.kit-version` assertion |
| `tests/modules/install/test_editable_install.py` | `__version__` assertion |
| `tests/modules/install/test_cursor_workflow.py` | `__version__` assertion |

**Consumer installs** receive version via `.ai_infra/.kit-version` (written fresh from manifest `kit_version` at scaffold/activate — no manual action needed there). **The kit-dev repo's own `.ai_infra/.kit-version` is git-tracked** and is *not* regenerated automatically (scaffold only runs on install targets), so it must be bumped by hand in this table too — `python3 -m cursor_workflow health` in this repo reads it directly and will report a stale version if it's missed (caught in v0.4.0: file was left at `0.3.0` after the version bump). **Not versioned with kit:** `workflow_mcp.__version__` (MCP server package semver).

After bump: `make sync-plugin && make check-plugin`, tag `vX.Y.Z`, optional GitHub Release notes.

## Bundle layout

```text
.cursor-plugin/plugin.json   # no path-override fields — spec-exact discovery
assets/logo.png    # Marketplace logotype (commit before publisher submit)
agents/            # Cursor-loaded — sibling of .cursor-plugin/, matches cursor/plugin-template
rules/             # Cursor-loaded — sibling of .cursor-plugin/
skills/            # Cursor-loaded — sibling of .cursor-plugin/
payload/           # ADR-001 install source (.ai_infra + cursor_workflow shim)
```

**All four generated trees (`agents/`, `rules/`, `skills/`, `payload/`) are committed to git** — Cursor Marketplace reads the repository directly, so nothing gitignored is visible to a reviewer or a third-party installer. `make sync-plugin` regenerates them from `.cursor/` + `.agents/skills/`; `make check-plugin` fails the build on drift. Layout and discovery match the official [`cursor/plugin-template`](https://github.com/cursor/plugin-template) starters exactly — verified by running the upstream `scripts/validate-template.mjs` directly against this repo (0 errors, see `.local/workflow-artifacts/release/cursor-plugin-template-compliance-2026-07-02.md`).

## Local smoke (`/add-plugin` from repo path)

### Consumer trial (GitHub plugin — recommended until Marketplace)

```bash
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"
```

1. **Agent chat** (not terminal): `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit` — click the **MAS Workflow Kit** card in the preview ([screenshot](../../../assets/mas-workflow-kit-install.png) · [README](https://github.com/SavinRazvan/mas-workflow-kit#1-install-the-plugin-cursor-chat--not-the-terminal))
2. **File → Open Folder** → `"$TARGET"` (your app — not the kit repo)
3. **Agent chat:** `/workflow-activate` → wait for **VERIFY PASS**
4. Edit `.local/user_settings/github.collaboration.yaml` → `python3 -m cursor_workflow contributors validate`

**Alternative — local path** (if GitHub URL fails in your Cursor build):

```text
/add-plugin /home/you/Projects/mas-workflow-kit
```

(clone the repo first if needed)

### Consumer trial (terminal activate, no plugin UI)

```bash
export KIT=~/Projects/mas-workflow-kit
export TARGET=~/Projects/my-app
mkdir -p "$TARGET"

"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" \
  --source "$KIT/payload"

cd "$TARGET"
# Edit .local/user_settings/github.collaboration.yaml (placeholders → your name / @handle)
python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow integrate validate
python3 -m cursor_workflow gates
```

Pass: `VERIFY PASS` on activate; `contributors validate: PASS` (after editing placeholders); `integrate validate` P0 = 0 (plugin parity skipped on consumer); `gates` green. Kit smoke alone: `pytest -q tests/modules/smoke/` → **1 passed**; full `gates` runs **your app tests + smoke** (e.g. 120 on Smart-Notes).

**Drift on consumer apps:** auto profile may read `kit-dev` unless `work-tracker.md` contains `STARTER-001`. Use explicit consumer profile (no agent required):

```bash
python3 -m cursor_workflow drift validate --directory . --profile consumer
```

**DRIFT-005 on consumer:** If you see `DRIFT-005 FAIL: IMPLEMENTATION-STATUS missing **Tests:** count` — that is a **kit bug (not your app)**: false positive because `IMPLEMENTATION-STATUS.md` is maintainer-only and is not shipped to consumers. Fixed on kit `main` (skip when absent → PASS). Until your consumer project picks up the fix, ignore DRIFT-005 or upgrade the kit payload.

**MCP validate:** use `python3 -m cursor_workflow mcp validate` — not bare `mcp validate` (different CLI).

### Quick plugin smoke (from kit repo)

1. Run `make sync-plugin`
2. In Agent chat: `/add-plugin https://github.com/SavinRazvan/mas-workflow-kit`
3. Confirm agents: `implementer`, `enterprise-auditor`, maintainer slash skills
4. Run **`/workflow-activate`** in Agent chat with a **non-kit** project folder open

```bash
cd "$TARGET"
python3 -m cursor_workflow activate --directory .
```

Or from kit repo without opening target in Cursor:

```bash
"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" --source "$KIT/payload"
```

5. In target: `python3 -m cursor_workflow gates --directory "$TARGET"`

### Automated smoke (kit repo)

Full Track A (direct install) + Track B (payload activate) with dashboard path checks and idempotency:

```bash
make smoke-consumer
# or:
bash .ai_infra/scripts/install/smoke_marketplace.sh
```

**Pass criteria (2026-07-01 evidence):**

| Check | Track A (kit install) | Track B (payload activate) |
|-------|----------------------|----------------------------|
| `install --verify` / `activate --verify` | `VERIFY PASS` | `VERIFY PASS` |
| `check_consumer_purity.py` | PASS | PASS |
| No `ci/kit-dev` in templates | PASS | PASS |
| Tier-1 `pages.json` paths | All PASS | (same layout) |
| `gates` / governance | PASS | PASS |
| `integrate validate` | P0 = 0 (kit-dev) | P0 = 0; INT-009/011 skipped on consumer |
| `user_settings` idempotency | PASS (valid exemplar + re-install) | N/A |
| `contributors validate` | N/A until personalized | **FAIL expected** until placeholders replaced |

**Operator notes:**

- Export `KIT` is not required when using `make smoke-consumer` (script resolves kit root).
- Idempotency test must patch the **full** exemplar YAML (`sed` on `Your Full Name`), not a minimal invalid stub.
- Pre-activate `cursor_contract: missing` on an empty target is **no longer shown** — activate prints `Pre-activate: planes not installed yet` then scaffolds.
- `payload/.cursor/skills/` must not duplicate `.agents/skills/` folder names (see `PLUGIN-ARCHITECTURE.md` skill merge table).

## Publisher application (Cursor Marketplace)

Pre-filled values for [Become a plugin publisher](https://cursor.com/marketplace/publish) (verify before submit).

| Field | Value |
|-------|--------|
| Organization name | Savin Ionuț Răzvan |
| Organization handle | `savin-razvan` (or `mas-workflow-kit`) |
| Contact email | razvan.i.savin@gmail.com |
| Logotype URL | `https://raw.githubusercontent.com/SavinRazvan/mas-workflow-kit/main/assets/logo.png` |
| Description | MAS Workflow Kit installs multi-agent workflow infrastructure into any Cursor project: agents, skills, rules, PR lifecycle scripts, `.local/` trackers, and optional MCP. Run **`/workflow-activate`** once to scaffold three planes. Pattern A: one script per maintainer action. For teams using agents, audits, and PR-first governance. |
| GitHub repository | https://github.com/SavinRazvan/mas-workflow-kit |
| Owner | Individual · razvan.i.savin@gmail.com |
| Website URL | https://razvansavin.com/ |

**Manifest:** `.cursor-plugin/plugin.json` — `author`, `homepage`, `repository`, `logo` aligned with the table above.

**Listing copy review (2026-07-07):** Verified `plugin.json` `description`, the Description row above, and README consumer sections (`What you get`, agent/skill/rule counts) against `IMPLEMENTATION-STATUS.md` on `main` — 633 tests (post DRIFT-005 slice), DOC-006 PASS, coverage scope 3588 stmts / 100% on `--cov=.ai_infra --cov=cursor_workflow`. No stale test or coverage numbers in marketplace-facing copy; feature counts (7 agents, 10 skills, 5 PR skills, 6 rules) match shipped inventory.

**Consumer smoke (2026-07-08):** Real app **Smart-Notes** — `/add-plugin` + chat **`/workflow-activate`**, `health`/`gates`/`integrate`/`mcp validate` PASS, kit smoke **1** of **120** pytest during gates. Record: `.local/workflow-artifacts/release/smoke-consumer-smart-notes-2026-07-08.md`.

## Publish

- Document target channel (Cursor Marketplace vs local `/add-plugin` only) before first publish
- Attach release notes: ADR index, activation flow, MCP optional profile
- After publish: enterprise re-audit (Phase 7 EA-506)

### Live marketplace (EA-v4-002 — manual when channel ready)

Local pre-publish evidence: `.local/workflow-artifacts/enterprise-architecture-audit/marketplace-dry-run-2026-06-29.md` (PASS on kit tree).

**Not yet exercised:** upload/publish to the live Cursor Marketplace channel. When credentials and channel are available:

1. Complete **Pre-publish** steps above on a release tag
2. Follow Cursor Marketplace maintainer docs for your account tier
3. Record publish URL + version in `.local/workflow-artifacts/enterprise-architecture-audit/` (no secrets in git)
4. Re-run `enterprise-auditor` focused pass on deployability category

Until live publish, **deployability score remains capped** at local dry-run evidence (see enterprise audit v5 §7 EA-v4-002).

## Rollback

- Re-publish previous plugin version
- Consumers: reinstall prior `kit_version` via `cursor_workflow install` from tagged kit release
