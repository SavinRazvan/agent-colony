<!--
File: repository-map.md
Path: .ai_infra/docs/handoff/repository-map.md
Role: Kit-maintainer repository map — SSOT vs generated trees, consumer install surface, deprecated paths.
Used By:
 - AGENTS.md (kit dev onboarding)
 - README.md § Developing the kit repo only
Depends On:
 - .ai_infra/manifest.yaml
 - .ai_infra/scripts/release/sync_plugin_bundle.py
 - .ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md
Notes:
 - **Kit-dev only** — not in manifest copy_ai_infra; never shipped to consumer projects.
 - Consumer orientation: workflow-architecture.md, PLUGIN-USER-GUIDE.md, folder-charter.md.
-->

# Repository map (kit maintainers)

**Audience:** People working in **this product repo** (`agent-colony`) — not consumer app projects.

**Not shipped to consumers.** This file lives under `docs/handoff/` (excluded from `manifest.yaml` `copy_ai_infra`). Do not link it from consumer quickstart or PLUGIN-USER-GUIDE body text.

---

## How to read this doc

| Column | Meaning |
|--------|---------|
| **SSOT** | Edit here; other trees are generated or copied |
| **Generated** | Run `make sync-plugin`; commit the diff |
| **Consumer** | Lands on disk after `agent_colony activate` in an app project |
| **Kit-dev only** | Stays in this repo; not in consumer `payload/` |

---

## Product repository (`agent-colony`)

```text
agent-colony/
├── .cursor/                    SSOT — agents, rules, canonical skills
├── .agents/skills/             SSOT — maintainer slash skills (+ deprecated stubs)
├── agents/                     Generated → Marketplace plugin surface (mirror of .cursor/agents)
├── rules/                      Generated → Marketplace plugin surface (mirror of .cursor/rules)
├── skills/                     Generated → Marketplace merge (.cursor/skills + additive .agents/skills)
├── payload/                    Generated → activate/install source tree (ADR-001)
├── .cursor-plugin/plugin.json  SSOT — Marketplace manifest
├── .ai_infra/                  SSOT — scripts, docs, templates, MCP, workflows, manifest.yaml
├── assets/                     Marketplace logo (`agent-colony-logo.png`)
├── .github/                    CI workflows (kit-dev only)
├── agent_colony/            SSOT — thin CLI shim (also copied to consumer)
├── schemas/                    Legacy gate.json stub (`resolve_gates()` in prepare.py; `GATES` = alias)
├── .local/                     Kit-dev runtime (gitignored); CI seed fixture — not consumer exemplars
├── tests/                      Kit-dev only — full pytest suite (1487; see IMPLEMENTATION-STATUS)
├── Makefile, pyproject.toml    Kit-dev only
├── overlays/                   Optional product rules source (`overlays/rules/project-ssot-precedence.mdc`); this product payload ships **7** rules (6 kit + SSOT precedence)
├── project-rules/              Deprecated alias → use overlays/rules/
└── AGENTS.md                   Kit-dev router (consumers get AGENTS.stub.md)
```

**Regenerate committed bundles:** `make sync-plugin` then `make check-plugin`.

Deep dive: [PLUGIN-ARCHITECTURE.md](PLUGIN-ARCHITECTURE.md).

---

## Source of truth vs generated (do not edit generated directly)

| Path | Role | Edit where |
|------|------|------------|
| `.cursor/agents/*.md` | 8 agent cards | **Here** |
| `.cursor/rules/*.mdc` | 7 kit-dev rules | **Here** |
| `.cursor/skills/*/` | 14 canonical protocols | **Here** |
| `.agents/skills/*/` | Maintainer slash skills | **Here** |
| `agents/`, `rules/`, `skills/` (repo root) | Marketplace discovery (20 skill folders = 14 canonical + 6 maintainer PR slash skills, incl. `full-pr-workflow`) | `make sync-plugin` from `.cursor/` + `.agents/skills/` |
| `payload/` | Consumer install bundle | `make sync-plugin` from above + manifest |
| `skills/audit-alignment/` | Deprecated stub in merged `skills/` | `.agents/skills/audit-alignment/` |

---

## Consumer project after activate (default profile)

What **`/workflow-activate`** copies into **your app** (e.g. Smart-Notes):

```text
my-app/
├── AGENTS.md                       Stub router (from template)
├── .cursor/
│   ├── agents/                     8 agents (from payload; incl. board)
│   ├── rules/                      7 rules (6 kit + project-ssot-precedence)
│   └── skills/                     14 canonical skills only (no repo-root skills/ merge)
├── .agents/skills/                 6 maintainer slash folders (incl. full-pr-workflow; + audit-alignment stub)
├── .ai_infra/                      Slim bundle (manifest copy_ai_infra only)
│   ├── scripts/pr|architecture|integration|workflow|install/
│   ├── install/agent_colony/
│   ├── docs/operations|governance|roadmap|decisions|architecture/
│   ├── templates/local-workspace|user-settings|agent-integration|project-board|research-corpus/
│   ├── workflows/                  PR lane hub (shipped — see workflows/README.md)
│   └── mcp_servers/agent_colony_mcp/   (with_mcp profile)
├── agent_colony/                CLI entrypoint
└── .local/                         Scaffolded trackers + artifact buckets (gitignored)
```

**Not installed:** kit `tests/modules/` (1487; see IMPLEMENTATION-STATUS), `Makefile`, `docs/handoff/`, `docs/maintainer/`, `.ai_infra/scripts/ci/`, `.ai_infra/scripts/release/`, this `repository-map.md`, `IMPLEMENTATION-STATUS.md`, repo-root `agents/rules/skills/`.

Consumer tree detail: [PLUGIN-ARCHITECTURE.md § Installed consumer project](PLUGIN-ARCHITECTURE.md).

---

## `.ai_infra/docs/` — what copies where

| Subtree | Consumer `.ai_infra/docs/`? | Purpose |
|---------|:---------------------------:|---------|
| `operations/` | **Yes** (minus filtered files) | Quickstart, PLUGIN-USER-GUIDE, gate-matrix, local-workspace-layout |
| `governance/` | **Yes** | folder-charter, drift-prevention, module boundaries |
| `architecture/` | **Yes** | workflow-architecture.md (consumer-facing) |
| `decisions/` | **Yes** | ADR index |
| `roadmap/` | **Yes** | alignment-audit-schema |
| **`handoff/`** | **No** | IMPLEMENTATION-STATUS, PLUGIN-ARCHITECTURE, marketplace-publish, **this file** |
| **`maintainer/`** | **No** | Heavy megadocs, local anchoring patterns |

Filter SSOT: `.ai_infra/scripts/architecture/consumer_bundle_paths.py` (e.g. excludes `documentation-maintenance-checklist.md` from consumer ops copy).

---

## Agents (8) — all active

| Agent | `.cursor/agents/` | Consumer | Invoke |
|-------|:-----------------:|:--------:|--------|
| `implementer` | Yes | Yes | `/implementer` |
| `test-runner` | Yes | Yes | `/test-runner` |
| `verifier` | Yes | Yes | `/verifier` |
| `auditor` | Yes | Yes | `/auditor` |
| `integrator` | Yes | Yes | `/integrator` |
| `drift-guard` | Yes | Yes | `/drift-guard` |
| `board` | Yes | Yes | `/board` |
| `researcher` | Yes | Yes (opt-in packs after `research init`) | `/researcher` (adaptive Brief + HTTPS; shipped/proven) |

**Deprecated agents:** none.

---

## Skills

### Canonical — `.cursor/skills/` (14) → consumer `.cursor/skills/`

| Skill | Paired agent |
|-------|----------------|
| `auditor-protocol` | `auditor` (full audit + **focused alignment pass**) |
| `audit-module-map` | `auditor` (depth tool) |
| `audit-orchestration` | Parent orchestration |
| `drift-audit` | `drift-guard` |
| `implementer-loop` | `implementer` |
| `test-coverage` | `test-runner` |
| `integrator-protocol` | `integrator` |
| `board-ssot` | `board` (board Entry/Exit; ADR-008) |
| `board-shell` | `board` (first-run shell coach) |
| `canvas-artifacts` | Canvas/plan Pattern A CLI (ADR-010) |
| `workflow-activate` | Install / first activate |
| `update-agent-colony` | Version-gated consumer upgrade |
| `mcp-connect` | MCP setup |
| `research-corpus` | `researcher` |

### Maintainer slash — `.agents/skills/` → consumer `.agents/skills/`

| Skill | Status | Notes |
|-------|--------|-------|
| `pr-workflow` | Active | Umbrella |
| `review-pr` | Active | |
| `prepare-pr` | Active | |
| `merge-pr` | Active | |
| `full-pr-workflow` | Active | Optional cleanup path: `pr-workflow` + `finalize.py` (branch cleanup, `finalize.md`) |
| **`audit-alignment`** | **Deprecated stub** | Redirect → `auditor`; outputs unchanged (`alignment-audit.md`, `alignment-todos.md`) |

Also under `.agents/skills/`: `README.md`, `PR_WORKFLOW.md` (legacy redirect), `RESEARCH_WORKFLOW.md` (research hub pointer).

### Repo-root `skills/` — Marketplace plugin mirror only

Cursor loads repo-root `agents/`, `rules/`, and `skills/` from the GitHub plugin URL. Those trees are **generated mirrors** of `.cursor/` + `.agents/skills/` (via `sync_plugin_bundle.py`) — **not** a second authoring SSOT. Edit canonical `.cursor/skills/` (14) and `.agents/skills/` (6); then `make sync-plugin`. Consumers receive skills under `.cursor/skills/` and `.agents/skills/` via `payload/` after activate — never as a single root `skills/` tree on disk.

---

## Rules — consumer `.cursor/rules/` (7 in this product payload) · kit-dev repo (7)

| Rule | alwaysApply | Kit-dev `.cursor/rules/` |
|------|:-----------:|:------------------------:|
| `implementation-workflow-governance.mdc` | Yes | Yes |
| `pr-workflow-enforcement.mdc` | Yes | Yes |
| `commit-trailer-format.mdc` | Yes | Yes |
| `file-docstring-header-relations.mdc` | Yes | Yes |
| `local-artifact-protection.mdc` | Yes | Yes |
| `advisory-audit-alignment-enforcement.mdc` | Yes | Yes |
| `project-ssot-precedence.mdc` | Yes | Yes (product SSOT; in payload for this kit) |

Product overlays: `overlays/rules/*.mdc` remains the source for domain overlays; **this product** also ships `project-ssot-precedence` in `payload/.cursor/rules/` (7 total).

---

## Deprecated / legacy / aliases

| Path | Status | Use instead |
|------|--------|-------------|
| `.agents/skills/audit-alignment/` | Deprecated stub | `auditor` + `auditor-protocol` |
| `skills/audit-alignment/` (repo root) | Same stub (generated) | Same |
| `.agents/skills/PR_WORKFLOW.md` | Legacy redirect | `pr-workflow/SKILL.md` |
| `project-rules/` | Deprecated alias | `overlays/rules/` |
| Repo-root `agents/`, `rules/`, `skills/` | Generated mirrors | Edit `.cursor/` + `.agents/skills/` |
| `.cursor/settings.json` | Kit-dev IDE prefs | Not in consumer bundle |

---

## `.local/` (runtime — gitignored)

| Subtree | Tier | Writer |
|---------|------|--------|
| `index-and-planning/current/` | 1 base + 2 runtime | scaffold + agents |
| `index-and-planning/history/` | 2 | agents — `updates-log.md`; `continuity-index.md` (rolling ≥3-day UTC rows; board Notes = full lifetime) |
| `workflow-artifacts/pr/` | 2 | review/prepare/merge scripts |
| `workflow-artifacts/alignment/` | 2 | `auditor` |
| `workflow-artifacts/drift/` | 2 | `drift-guard` |
| `workflow-artifacts/enterprise-architecture-audit/` | 2 | `auditor` |
| `agents-control-center/` | 1 + refresh | scaffold / activate |
| `user_settings/` | 1 | human (gitignored) |
| `canvases/` | 2 | agents — `canvas save` session evidence (ADR-010) |
| `plans/` | 2 | agents — `plan snapshot` history only; live plan on board / `plan.md` (DRIFT-012) |
| `generated-data/` | 2 | pytest / CI |

**Kit repo `.local/`** is a CI seed fixture — not what consumers receive. Consumers get neutral exemplars from `templates/local-workspace/exemplars/`.

Contract: [local-workspace-layout.md](../operations/local-workspace-layout.md) · [folder-charter.md](../governance/folder-charter.md).

---

## Kit-dev-only paths (quick reference)

| Path | Why kit-dev only |
|------|------------------|
| `tests/modules/` | Full kit test suite |
| `.ai_infra/docs/handoff/` | Maintainer status, plugin arch, this map |
| `.ai_infra/docs/maintainer/` | Megadocs |
| `.ai_infra/scripts/ci/`, `.ai_infra/scripts/release/` | CI and plugin sync |
| `.ai_infra/templates/local-workspace/ci/kit-dev/` | CI tracker fixtures |
| `Makefile`, `pyproject.toml`, `.github/` | Kit repo hygiene |
| Repo-root `agents/`, `rules/`, `skills/` | Marketplace surface |

---

## Related docs (by audience)

| Audience | Start here |
|----------|------------|
| **Kit maintainer** | This file → [PLUGIN-ARCHITECTURE.md](PLUGIN-ARCHITECTURE.md) → [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) → [AGENTS.md](../../AGENTS.md) |
| **Consumer app dev** | [consumer-quickstart.md](../operations/consumer-quickstart.md) → [PLUGIN-USER-GUIDE.md](../operations/PLUGIN-USER-GUIDE.md) → [workflow-architecture.md](../architecture/workflow-architecture.md) |
| **`.local/` layout** | [local-workspace-layout.md](../operations/local-workspace-layout.md) (shipped — universal) |
| **Three planes** | [folder-charter.md](../governance/folder-charter.md) (shipped — universal) |
| **Marketplace publish** | [marketplace-publish.md](marketplace-publish.md) |

---

## Maintenance

When adding agents, skills, manifest paths, or deprecated redirects:

1. Update SSOT under `.cursor/` or `.agents/skills/`
2. Run `make sync-plugin && make check-plugin`
3. Update this file and [IMPLEMENTATION-STATUS.md](IMPLEMENTATION-STATUS.md) counts
4. Do **not** add kit-repo-only tables to consumer quickstart or PLUGIN-USER-GUIDE
