<!--
File: install-dry-run.md
Path: .ai_infra/docs/operations/install-dry-run.md
Role: Manual install verification checklist for consuming the MAS Workflow Kit in a fresh project.
Used By:
 - README.md Quick install
Depends On:
 - .ai_infra/docs/maintainer/local-anchoring-patterns.md
 - .ai_infra/templates/local-workspace/
Notes:
 - Automated: `python -m cursor_workflow install` and `make install-dry-run`.
 - Entry doc: `.ai_infra/docs/operations/consumer-quickstart.md`.
-->

# Install dry-run (manual or automated)

Verify the kit installs into an empty or greenfield project **without** product-specific rule contamination in core `.cursor/rules/`.

**Consumer path:** [`consumer-quickstart.md`](consumer-quickstart.md) — recommended first read.

## Automated (recommended)

From the **MAS Workflow Kit** repo:

```bash
make install-dry-run
# or:
python -m cursor_workflow install \
  --target /path/to/new-project \
  --with-venv \
  --with-mcp-json \
  --verify
# Kit dev only (full tests tree):
python -m cursor_workflow install \
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

See [`scripts/install/README.md`](../../scripts/install/README.md).

## Manual steps

Use the sections below if you prefer hand-copying or need to debug scaffold behavior.

## Prerequisites

- Python 3.11+ with `venv`
- Git
- Cursor IDE (for agents + optional MCP)

## 1. Copy core (manual)

```bash
TARGET=/tmp/workflow-kit-dry-run
mkdir -p "$TARGET" && cd "$TARGET"
git init

# From mas-workflow-kit root (adjust SOURCE):
SOURCE=/path/to/mas-workflow-kit
cp -r "$SOURCE/.cursor" "$SOURCE/.agents" "$TARGET/"
cp -r "$SOURCE/scripts/pr" "$SOURCE/scripts/architecture" "$TARGET/scripts/"
cp -r "$SOURCE/workflow_mcp" "$SOURCE/schemas" "$TARGET/"
cp "$SOURCE/requirements-mcp.txt" "$TARGET/"
cp "$SOURCE/AGENTS.md" "$SOURCE/README.md" "$TARGET/"
mkdir -p "$TARGET/docs"
cp -r "$SOURCE/docs/governance" "$SOURCE/docs/operations" "$SOURCE/docs/roadmap" "$TARGET/docs/"
cp -r "$SOURCE/docs/templates" "$TARGET/docs/"
cp -r "$SOURCE/overlays" "$SOURCE/project-rules" "$TARGET/"
```

## 2. Scaffold `.local/`

```bash
mkdir -p "$TARGET/.local/index-and-planning/current"
mkdir -p "$TARGET/.local/index-and-planning/history"
mkdir -p "$TARGET/.local/workflow-artifacts/pr"

cp "$SOURCE/docs/templates/local-workspace/exemplars/"*.md \
   "$TARGET/.local/index-and-planning/current/"
cp "$SOURCE/.local/agents-control-center/config/pages.json" \
   "$TARGET/.local/agents-control-center/config/" 2>/dev/null || true
```

Edit `session-pointer.md` and `plan.md` for the target project name.

## 3. Python environment

```bash
cd "$TARGET"
python3 -m venv .venv
.venv/bin/pip install pytest
.venv/bin/pip install -r requirements-mcp.txt
```

Copy kit tests only for kit-dev installs (`--with-tests`). Consumer default scaffolds `tests/modules/smoke/test_kit_installed.py`:

```bash
# Default consumer install — no copy needed (scaffold writes smoke test)
# Kit dev:
cp -r "$SOURCE/tests" "$TARGET/"
```

## 4. Customize once

- [ ] `project.config.yaml` — copy from `project.config.yaml.example` (optional metadata)
- [ ] `.ai_infra/scripts/pr/prepare.py` — `GATES` (default 2 gates OK)
- [ ] `.ai_infra/scripts/pr/local_workflow_paths.py` — `DEFAULT_GITHUB_USER`
- [ ] `AGENTS.md` — project first-reads
- [ ] Optional: overlay rules via `cp overlays/rules/*.mdc .cursor/rules/`

## 5. Verification gates

```bash
cd "$TARGET"
.venv/bin/python .ai_infra/scripts/pr/check_testing_artifacts.py
.venv/bin/python -m pytest -q
.venv/bin/python scripts/architecture/check_governance_consistency.py
```

Expected: all PASS (governance may skip CI workflow if `.github/` absent).

## 6. MCP smoke (optional)

```bash
cp .cursor/mcp.json.kit.example .cursor/mcp.json
# or: cursor-workflow install --with-mcp-json (merges kit + mcp.user.json)
# Edit python path to $TARGET/.venv/bin/python
WORKFLOW_KIT_ROOT="$TARGET" .venv/bin/python -m workflow_mcp
```

In Cursor: enable MCP server; call `workflow_list_agents` and `workflow_gate_count`.

## 7. Cursor agents

- [ ] Five agent files under `.cursor/agents/` (no mapper)
- [ ] Six universal rules under `.cursor/rules/*.mdc`
- [ ] Maintainer skills under `.agents/skills/`

## Success criteria

| Check | Pass |
|-------|------|
| `prepare.py` has 2 default gates | |
| No product overlay rules in core `.cursor/rules/` (6 universal only) | |
| `.local/current/session-pointer.md` exists | |
| `pytest -q` green | |
| `workflow_mcp` imports and `workflow_gate_count` → `2` | |

## Cleanup

```bash
rm -rf /tmp/workflow-kit-dry-run
```
