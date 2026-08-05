<!--
File: abbreviations-notepad.md
Path: .ai_infra/docs/operations/abbreviations-notepad.md
Role: Glossary for MAS Workflow Kit workflow terminology.
Used By:
 - README.md
 - AGENTS.md
Depends On:
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
 - .ai_infra/docs/decisions/README.md
Notes:
 - Keep definitions short for newcomers.
 - Numbered catalogs (ADR-NNN, DRIFT-NNN, EA-NNN, INT-NNN, DOC-NNN) live in their index docs — list stems here only.
-->

# Abbreviations Notepad

Quick reference for reading `README.md`, `AGENTS.md`, and kit docs.

## MAS Workflow Kit flow (plain language)

1. Install kit via `cursor_workflow activate` (plugin) or `cursor_workflow install` (kit clone).
2. When `project_ssot.enabled` + `board_only`: Entry = board (`project status` / claim); Exit = Status + Notes. Local trackers = offline fallback only.
3. Else: agents read `.local/` trackers (`session-pointer.md` → `plan.md` → `work-tracker.md`).
4. Maintainer PR workflow runs via `.ai_infra/scripts/pr/*` (Pattern A + `prepare.py` `resolve_gates()`).
5. Optional MCP (`workflow-kit`) wraps the same scripts.

## Core abbreviations

| Abbreviation | Meaning |
|---|---|
| MAS | Multi-Agent System — this kit’s agent/skill/script workflow product |
| SSOT | Single Source of Truth — one authoritative place for a given concern |
| MCP | Model Context Protocol — Cursor tool server integration |
| CLI | Command-line interface — here mainly `python3 -m cursor_workflow …` and `gh` |
| PR | Pull request — maintainer merge workflow (Pattern A) |
| ADR | Architecture Decision Record — `.ai_infra/docs/decisions/` (ADR-001…008) |
| GATES | 2-gate back-compat alias in `.ai_infra/scripts/pr/prepare.py`; SSOT is `resolve_gates()` (kit-dev may append drift + doc facts) |
| Pattern A | Script-first workflow; agents invoke **one** command per maintainer action |
| YAML | Config format for `github.collaboration.yaml`, registries, manifests |
| UTC / ISO-8601 | Board Notes timestamps (`YYYY-MM-DDTHH:MM:SSZ`); CLI stamps UTC |
| CI / CD | Continuous integration / delivery — GitHub Actions + release evidence |
| RC | Release candidate — needs CI/CD evidence bundles before ship |
| UI | GitHub Project / settings UI (humans); agents prefer CLI |
| PAT | Personal Access Token — GitHub auth; fine-grained PATs need Projects + repo scopes |
| GraphQL | GitHub Projects API used by `gh project` / board CLI (rate-limited) |
| KISS | Keep It Simple — incremental, reversible slices |
| DCO | Developer Certificate of Origin — do **not** auto-insert DCO-style assertions |
| AI | Artificial intelligence — optional `Assisted-by:` trailer when AI materially shaped a change |
| TBD | To Be Determined — placeholder in file headers / relations |
| DAG | Directed Acyclic Graph — agent **handoff** edges (canvases); no cycles |
| ACC | Agents Control Center — `.local/agents-control-center/` (folder name) |
| ICC | Implementation Control Center — HTML dashboard under ACC (**deprecated**; prefer board + canvases) |
| HTML | Local dashboard pages served via `http.server` (not `file://`) |
| JSON | Machine artifacts (coverage, board export, registries, MCP config) |
| IDE | Editor host (Cursor) — canvases open via Open Canvas, not raw `file://` HTML |

## Board / Project SSOT

| Term | Meaning |
|---|---|
| `project_ssot` | YAML block in `github.collaboration.yaml` wiring the GitHub Project |
| `board_only` | `sync_policy` — board is the **only writable** backlog/Status/continuation SSOT |
| Tier-1 | Mandatory board fields: Status, Priority, Size, Estimate, Start date (on first In progress), Assignee, Linked PR when a PR exists |
| `PVT_` | GitHub Project v2 **project** node id (in YAML `project_id`) |
| `PVTI_` | GitHub Project v2 **item** id (card); Draft→Issue keeps the same `PVTI_` |
| outbox | Local rate-limit buffer (`.local/generated-data/board-outbox.jsonl`); not a second SSOT |
| EXIT_QUEUED | CLI exit code **6** — write queued to outbox; later `project outbox flush` |
| dual-write | Forbidden under `board_only`: writing competing Status into local trackers |
| Entry / Exit | Every agent: read board on Entry; update Status (+ Notes) on Exit |
| canvas | Cursor Canvas visualization (`canvases/*.canvas.tsx`) — prefer over deprecated ICC HTML |

## Drift, audit, and check ids

| Stem | Meaning | Where to look |
|---|---|---|
| DRIFT-NNN | Operational drift check id (plan/tracker/board coherence) | ADR-007; `drift validate` |
| INT-NNN | Integrate / registry parity check id | `integrate validate` |
| EA-NNN | Enterprise-architecture finding / backlog id | auditor artifacts / board |
| DOC-NNN | Documentation fact / validate check id | `make doc-validate` / doc facts |
| COV-NNN | Coverage readiness claim / slice label | IMPLEMENTATION-STATUS / coverage evidence |
| P0 / P1 / P2 / P3 | Priority — board uses `p0\|p1\|p2`; chat P3 → board `p2` + Notes `deferred` | `board-ssot` skill |
| xs…xl | Size options on the board (Tier-1) | Size↔Estimate table in skill |

High-signal drift ids you will see often: **DRIFT-009** (no competing tracker `in_progress` under `board_only`), **DRIFT-010** (board Status vs PRs / stale In progress; uses read-only `project export`), **DRIFT-011** (`.cursor/agents` basenames == eight live kit agent ids — goal/doctrine pulse), **DRIFT-012** (`.local/plans/` snapshot-only under `board_only`).

**Canvas / plan (ADR-010):** repo `canvases/` → `canvas sync` → IDE preview → optional `canvas save` → `.local/canvases/`; plan history in `.local/plans/` via `plan snapshot|list|open` (live plan on board card).

## Planes

| Term | Path |
|------|------|
| Cursor contract | `.cursor/`, `.agents/` |
| Infrastructure | `.ai_infra/` |
| Runtime | `.local/` (gitignored) |

## Agents (default kit)

| Agent | Role |
|-------|------|
| board | Board triage, Status, Tier-1 fields; hand off to implementer |
| implementer | Slice implementation |
| integrator | Extend agents/skills/MCP into kit infrastructure |
| test-runner | Module tests and coverage |
| verifier | Evidence-based verification |
| auditor | Architecture audits (alignment / scorecard artifacts) |
| drift-guard | Operational drift audit + board Exit for drift-pass cards |
| researcher | Brief-driven research packs; CLI `research init\|fetch\|validate` |

## Research (optional)

| Term | Meaning |
|------|---------|
| Brief | Intake contract for researcher (`BRIEF.md` / chat / board card) — source, question, lenses, consumers |
| Research pack | Indexed corpus under `_research_results/sources/<slug>/` (`INDEX.json`, `AGENT_BRIEF.md`, …) |
| AGENT_BRIEF | Consumer-facing brief inside a research pack for implementer/integrator |

## Related indexes (do not duplicate full catalogs here)

| Catalog | Index |
|---------|--------|
| ADRs | `.ai_infra/docs/decisions/README.md` |
| Drift checks | ADR-007 + `.cursor/skills/drift-audit/SKILL.md` |
| Board ops | `.ai_infra/docs/operations/project-board-collaboration.md` |
| Token / log discipline | `.ai_infra/docs/operations/token-efficiency.md` |
