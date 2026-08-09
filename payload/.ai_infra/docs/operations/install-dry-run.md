<!--
File: install-dry-run.md
Path: .ai_infra/docs/operations/install-dry-run.md
Role: Manual install verification checklist for consuming the Agent Colony in a fresh project.
Used By:
 - README.md Quick install
Depends On:
 - .ai_infra/docs/maintainer/local-anchoring-patterns.md
 - .ai_infra/templates/local-workspace/
Notes:
 - Automated: `python -m agent_colony install` and `make install-dry-run`.
 - Entry doc: `.ai_infra/docs/operations/consumer-quickstart.md`.
-->

# Install dry-run (manual or automated)

Verify the kit installs into an empty or greenfield project **without** product-specific rule contamination in core `.cursor/rules/`.

**Consumer path:** [`consumer-quickstart.md`](consumer-quickstart.md) — recommended first read.

## Automated (recommended)

From the **Agent Colony** repo:

```bash
make install-dry-run
# or:
python -m agent_colony install \
  --target /path/to/new-project \
  --with-venv \
  --with-mcp-json \
  --verify
# Kit dev only (full tests tree):
python -m agent_colony install \
  --target /path/to/new-project \
  --with-tests \
  --with-venv \
  --verify
# legacy:
python .ai_infra/scripts/install/scaffold.py \
  --target /path/to/new-project \
  --with-venv \
  --with-mcp-json \
  --verify
```

See [`.ai_infra/scripts/install/README.md`](../../scripts/install/README.md).

**Marketplace / plugin smoke (Track A + B):** this product repo [`marketplace-publish.md`](https://github.com/SavinRazvan/agent-colony/blob/main/.ai_infra/docs/handoff/marketplace-publish.md) § Automated smoke, or `make smoke-consumer` from this repo.

## Manual steps

Use the sections below if you prefer hand-copying or need to debug scaffold behavior.

## Prerequisites

- Python 3.11+ with `venv`
- Git
- Cursor IDE (for agents + optional MCP)

## 1. Copy core (manual — deprecated)

> **Prefer the [Automated](#automated-recommended) section above.** Hand-copy paths drift from `manifest.yaml` and `agent_colony install`. Do **not** copy deprecated `project-rules/` — use `overlays/rules/` only.

If you must debug scaffold behavior, install from **`payload/`** (not repo root):

```bash
TARGET=/tmp/agent-colony-dry-run
SOURCE=/path/to/agent-colony/payload
python3 -m agent_colony install --target "$TARGET" --source "$SOURCE" --dry-run
```

## 2. Scaffold `.local/` (prefer automated)

**Recommended:** use `scaffold.py` / `agent_colony install` — do not hand-mkdir buckets.

```bash
python -m agent_colony install --target "$TARGET" --source "$SOURCE"
```

Tier 1 base layout created by scaffold (see [local-workspace-layout.md](local-workspace-layout.md) § Artifact tiers):

| Path | Created |
|------|---------|
| `.local/index-and-planning/current/` | Exemplar trackers (if missing), including `coverage-index.md` |
| `.local/index-and-planning/history/` | `updates-log.md` (if missing) |
| `.local/workflow-artifacts/{pr,alignment,drift,auditor-protocol,release,audit}/` | Dirs + README stubs (if missing) |
| `.local/agents-control-center/config/pages.json` | Cockpit tabs (if missing) |
| `.local/agents-control-center/dashboards/` | Optional HTML/CSS (if missing) |
| `AGENTS.md` | From `.ai_infra/templates/AGENTS.stub.md` (if missing) |

Re-activate is idempotent: existing trackers, `AGENTS.md`, and `pages.json` are not overwritten.

Edit `session-pointer.md` and `plan.md` for the target project name after first install.

## 3. Python environment

```bash
cd "$TARGET"
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/pip install -r requirements-mcp.txt
```

Copy kit tests only for kit-dev installs (`--with-tests`). Consumer default does **not** write a smoke pytest file — layout is checked in-process at CHECK/VERIFY (`--keep-smoke-test` to opt in):

```bash
# Default consumer install — no tests/modules/smoke/ left in the app
# Optional: --keep-smoke-test
# Kit dev:
cp -r "$SOURCE/tests" "$TARGET/"
```

## 4. Customize once

- [ ] `project.config.yaml` — copy from `project.config.yaml.example` (optional metadata)
- [ ] `.ai_infra/scripts/pr/prepare.py` — `resolve_gates()` (default 2 gates OK; `GATES` = back-compat alias)
- [ ] `.ai_infra/scripts/pr/local_workflow_paths.py` — `DEFAULT_GITHUB_USER`
- [ ] `AGENTS.md` — project first-reads
- [ ] Optional: overlay rules via `cp overlays/rules/*.mdc .cursor/rules/`

## 5. Verification gates

```bash
cd "$TARGET"
.venv/bin/python .ai_infra/scripts/pr/check_testing_artifacts.py
.venv/bin/python -m pytest -q
.venv/bin/python .ai_infra/scripts/architecture/check_governance_consistency.py
```

Expected: all PASS (governance may skip CI workflow if `.github/` absent).

## 6. MCP smoke (optional)

```bash
cp .cursor/mcp.json.kit.example .cursor/mcp.json
# or: agent-colony install --with-mcp-json (merges kit + mcp.user.json)
# Edit python path to $TARGET/.venv/bin/python
AGENT_COLONY_ROOT="$TARGET" .venv/bin/python -m agent_colony_mcp
```

In Cursor: enable MCP server; call `workflow_list_agents` and `workflow_gate_count`.

## 7. Cursor agents

- [ ] Eight agent files under `.cursor/agents/` (no mapper)
- [ ] Twelve canonical skills under `.cursor/skills/` (includes `board-shell`)
- [ ] Seven rules under `.cursor/rules/*.mdc` (6 kit + `project-ssot-precedence`)
- [ ] Maintainer skills under `.agents/skills/`
- [ ] When `project_ssot.enabled`: `python3 -m agent_colony project board-bootstrap --check` (default Playground shell)

## Success criteria

| Check | Consumer | Kit-dev |
|-------|----------|---------|
| `prepare.py` / `resolve_gates()` count | **2** universal | **5** (auto-appends drift + doc facts + check-plugin) |
| `.cursor/rules/*.mdc` | **7** shipped (6 kit + `project-ssot-precedence`); extra overlays optional | same |
| `.local/index-and-planning/current/session-pointer.md` exists | yes | yes |
| All six `workflow-artifacts/*/README.md` stubs (recommended_paths) | yes | yes |
| `AGENTS.md` present | yes | yes |
| `pytest -q` green | yes | yes |
| `agent_colony_mcp` / `workflow_gate_count` (`load_gates` → `resolve_gates()`) | **2** | **5** |

## Cleanup

```bash
rm -rf /tmp/agent-colony-dry-run
```
