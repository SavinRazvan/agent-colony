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
3. `make sync-plugin` — rebuild `plugin/` + `payload/`
4. `make check-plugin` — bundle parity green
5. `.venv/bin/python .ai_infra/scripts/architecture/check_debrand.py`
6. Bump **all version SSOT fields together** (see [Versioning](#versioning) below)
7. Add `assets/logo.png` (1:1, background plate) — see `assets/README.md`

## Versioning

**Current release:** `0.3.0` (git tag `v0.3.0`).

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
| `.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md` | header + kit version row |
| `tests/modules/install/test_install_contract.py` | `.kit-version` assertion |
| `tests/modules/install/test_editable_install.py` | `__version__` assertion |
| `tests/modules/install/test_cursor_workflow.py` | `__version__` assertion |

**Consumer installs** receive version via `.ai_infra/.kit-version` (written from manifest `kit_version` at scaffold/activate). **Not versioned with kit:** `workflow_mcp.__version__` (MCP server package semver).

After bump: `make sync-plugin && make check-plugin`, tag `vX.Y.Z`, optional GitHub Release notes.

## Bundle layout

```text
.cursor-plugin/plugin.json
assets/logo.png    # Marketplace logotype (commit before publisher submit)
plugin/            # Cursor-loaded agents, skills, rules
payload/           # ADR-001 install source (.ai_infra + cursor_workflow shim)
```

## Local smoke (`/add-plugin` from repo path)

### Consumer trial (maintainer — separate project, not the kit repo)

```bash
export KIT=~/Projects/mas-workflow-kit
export TARGET=~/Projects/mas-consumer-trial
mkdir -p "$TARGET"

# 1. Plugin in Cursor: /add-plugin → "$KIT" (repo root with .cursor-plugin/plugin.json)
# 2. Open "$TARGET" as the workspace in Cursor (File → Open Folder)

"$KIT/.venv/bin/python" "$KIT/payload/cursor_workflow" activate \
  --directory "$TARGET" \
  --source "$KIT/payload"

cd "$TARGET"
# Edit .local/user_settings/github.collaboration.yaml (placeholders → your name / @handle)
python3 -m cursor_workflow contributors validate
python3 -m cursor_workflow integrate validate
python3 -m cursor_workflow gates
```

Pass: `VERIFY PASS` on activate; `contributors validate: PASS` (after editing placeholders); `integrate validate` P0 = 0 (plugin parity skipped on consumer); `gates` green.

### Quick plugin smoke (from kit repo)

1. Run `make sync-plugin`
2. In Cursor: `/add-plugin` → kit repo root
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
