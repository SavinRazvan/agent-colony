<!--
File: IMPLEMENTATION-STATUS.md
Path: .ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md
Role: Shipped vs spec — single source when maintainer megadocs lag the repo.
Used By:
 - README.md
 - auditor alignment passes
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/mcp_servers/agent_colony_mcp/
 - .ai_infra/scripts/install/scaffold.py
Notes:
 - Update this file each material slice; do not rewrite full maintainer megadocs for every change.
-->

# Implementation status (Agent Colony)

**Last updated:** 2026-08-07 (MCP package agent_colony_mcp; kit 0.6.1)
**Product:** `agent-colony` · CLI: `agent-colony` 0.6.1 · **Tests:** 1487

## Shipped (confirmed in repo)

| Area | Status | Location |
|------|--------|----------|
| Universal rules | 7 `.mdc` | `.cursor/rules/` **and** `payload/.cursor/rules/` (6 kit + `project-ssot-precedence`) |
| Agents | 8 core; `model: auto`; audit agents write `.local/` artifacts only (no `readonly`) | `.cursor/agents/` |
| Canonical skills | 14 folders | `.cursor/skills/` |
| Maintainer skills | 6 folders (additive plugin merge; includes `full-pr-workflow`) | `.agents/skills/` |
| Cursor skill merge | Canonical wins in plugin sync | `sync_plugin_bundle.py` |
| workflow-activate skill | Kit dev + plugin | `.cursor/skills/workflow-activate/` |
| PR scripts + prepare gates | Pattern A — **2** universal; **4** on kit-dev (drift + doc facts) | `.ai_infra/scripts/pr/prepare.py` |
| Governance + debrand scanners | CI-ready | `.ai_infra/scripts/architecture/` |
| Workflow drift validate | ADR-007 (+ DRIFT-004b, DRIFT-011 roster, DRIFT-012 plan snapshots) | `.ai_infra/scripts/workflow/check_drift.py` |
| Timestamped board Notes (CONT-TS) | `@user/agent · <ISO-8601-UTC> · …` via CLI (`claim`/`handoff`/`append-notes`) | `project_recipes.py` / `project_cli.py` + skill § Notes |
| Tier-1 Size/Estimate + Start date | Size↔Estimate **points** table in skill; Start date on claim / `set-status` / `handoff` → `in_progress`; `create-from-template --priority` required | `board-ssot` skill · `project_atomics.ensure_start_date_if_starting` · PR #70 |
| Local continuity-index | Rolling ≥3-day UTC rows; board Notes = full card lifetime | `history/continuity-index.md` (+ exemplar) |
| Board outbox (rate-limit) | `project queue` / `outbox status|flush`; EXIT_QUEUED=6; precheck + Forbidden/429 queue + dedupe; **77 mocked unit tests** | `project_outbox.py` + `project_atomics.py` / `project_cli.py` + `tests/modules/install/test_project_outbox.py` |
| Board shell schema + coach | `board-shell.schema.yaml` + `board-shell` skill; schema-aware `board-bootstrap --check`; opt-in `--ensure-fields` / `--apply-readme` | templates/project-board · project_handlers · board_shell.py |
| Board CLI subcommands | **23+** leaf commands (incl. `entry`; full table in ops doc) | [project-board-collaboration.md](../operations/project-board-collaboration.md) § Project CLI subcommands |
| GraphQL-efficient Entry | `project entry` live \| conserve \| offline_artifacts; `export --reuse-if-fresh` | `project_cli.py` · `project_ssot.efficiency` |
| EA-001 residual thin CLI | `project_cli.py` facade (~660 LOC) + parser/handlers split; board CLI modules under `.ai_infra/install/agent_colony/`: `project_cli.py`, `project_parser.py`, `project_handlers.py`, `project_atomics.py`, `gh_project_adapter.py`, `project_recipes.py`, `project_outbox.py` | PR #36 |
| Doc facts validate | DOC-001…008 | `.ai_infra/scripts/architecture/check_doc_facts.py` |
| Kit canvases | **16** files under `canvases/`; DOC-008 counts **11** roster/agent canvases (excludes concept hubs `board-ssot-vs-trackers.canvas.tsx`, `agents-artifacts-board.canvas.tsx`, `github-api-safety.canvas.tsx`, `naming-roster-audit.canvas.tsx`) | `canvases/` · `doc_facts_checks._canvas_paths` |
| Verify-all matrix | Maintainer preflight | `.ai_infra/scripts/architecture/verify_all.py` |
| Anchoring | session-pointer, change-index | `.local/.../current/` |
| MCP tools + resources | 20 tools + 6 resources | `.ai_infra/mcp_servers/agent_colony_mcp/` |
| Install scaffold + contract | `install-contract.json`; idempotent trackers/`AGENTS.md`/`pages.json` on re-activate | `.ai_infra/scripts/install/scaffold.py` |
| Local artifact tiers | Tier 1 scaffold: all `workflow-artifacts/*` buckets + README stubs; SSOT `local_workflow_paths.py` | `.ai_infra/templates/local-workspace/`, `pages.json` |
| Integrate validate | INT-001…014; INT-009/011 plugin parity **kit-dev only** | `.ai_infra/scripts/integration/validate.py` |
| Canvas / plan CLI | ADR-010 Pattern A — `canvas doctor|sync|save`, `plan snapshot|list|open` | `.ai_infra/install/agent_colony/canvas_cli.py`, `plan_cli.py` · `canvas-artifacts` skill |
| Install CLI | install, **activate**, gates, health, mcp, contributors, integrate, drift, doc, verify, **project**, **research**, **canvas**, **plan** | `.ai_infra/install/agent_colony/cli.py` |
| Editable install | `pyproject.toml` — `pip install -e ".[dev,mcp]"` | repo root |
| Three-plane activate | Idempotent plugin consumer setup | `.ai_infra/install/agent_colony/activate_cli.py`, `plane_status.py` |
| User MCP registry | ADR-004 | `.cursor/mcp.registry.yaml.example`, `mcp_manage.py` |
| Marketplace plugin | ADR-001 Option B | `.cursor-plugin/`, `sync_plugin_bundle.py` |
| Researcher agent (corpus) | **Shipped / proven** — adaptive Brief; anti-loop ≤6; CLI `research init\|fetch\|validate`; live E2E flexiai-toolsmith (18 curated, validate PASS) + verifier Claim A+B VERIFIED 2026-07-19; corpus **opt-in** after first `research init` | `.cursor/agents/researcher.md` · `research-corpus` · `canvases/agent-researcher.canvas.tsx` · Issue #74 |
| Kit version on install | `kit_version` 0.6.1 | `.ai_infra/manifest.yaml`, `.ai_infra/.kit-version` |
| Tests | 1487 collected (intentional live-smoke skips on full green run) | `tests/modules/` |

## Coverage scope (shipped source)

Two metrics (do not conflate):

| Metric | Command | As of 2026-08-06 |
|--------|---------|------------------|
| **(A) Install package** | `pytest tests/modules/ -q --cov=.ai_infra/install/agent_colony --cov-report=term-missing` | **5520 statements, 100.00%, Miss=0** (all modules) |
| **(B) Broader kit import surface** | `pytest --cov=.ai_infra --cov=agent_colony` | **8929 statements, 99% (99 miss)** — honest post-COV-CW; not claimed 100% when only install package is closed |

Metric (A) is the trust gate for Pattern A CLI (`project`, `mcp`, `canvas`, `plan`). Metric (B) tracks the installable kit import surface (CLI, scripts invoked in-process, MCP server). One import-order `sys.path` bootstrap in
`merge.py` is `# pragma: no cover` (justified — import-order bootstrap only).
Subprocess-only maintainer scanners (`check_governance_consistency.py`,
`check_debrand.py`, `check_consumer_purity.py`, `check_file_headers.py`) have
dedicated module tests but are excluded from metric (B) by design — they are
launched via `subprocess` / `make gates`, not imported by the coverage run.
Running `--cov=.` (tests included) reports higher because of order-dependent
branches in test-helper cleanup code; scope shipped source for readiness claims.

## Verification commands

```bash
pip install -e ".[dev,mcp]"
make gates
make drift-validate
make doc-validate
make verify-all
make install-dry-run
make check-plugin
agent-colony activate --directory .
agent-colony health
agent-colony mcp validate
pytest -m live tests/modules/agent_colony_mcp/test_agent_colony_mcp.py::test_agent_colony_mcp_stdio_initialize_smoke
agent-colony drift validate
```

| Command | Behavior |
|---------|----------|
| `make check-plugin` / CI (`kit-quality.yml`) | Regenerates mirrors to a temp tree and diffs against **committed** `agents/` / `rules/` / `skills/` / `payload/` — fails if stale (no prior sync) |
| `make verify-all` | Runs **sync-plugin first**, then `--check` — refreshes the working tree; does **not** by itself prove committed trees were already green |
| Kit-dev `prepare.py` | Includes the same strict `--check` as CI (see [gate-matrix.md](../operations/gate-matrix.md)) |

## Not yet shipped

| Item | Target |
|------|--------|
| Cursor Marketplace listing (EA-019) | deferred — consumers install from GitHub (`SavinRazvan/agent-colony`) until re-scheduled |
| PyPI publish (`agent-colony` on PyPI) | out of scope — editable install via `pyproject.toml` is shipped |

## Maintainer doc sync

When this file changes, skim-update related maintainer docs under `.ai_infra/docs/maintainer/` — do not full-rewrite megadocs per slice.
