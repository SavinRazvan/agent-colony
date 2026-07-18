# AGENTS.md

## Project intent

**MAS Workflow Kit — Project SSOT** (`mas-workflow-kit-project-ssot`) — this repository **is** the product: installable multi-agent workflow infrastructure with a **GitHub Project** as the **only writable SSOT** for backlog, Status, and multi-agent continuation when `project_ssot.enabled` and `sync_policy: board_only`. **Local artifacts** (PR Pattern A, audits, gates, secrets) stay on disk as evidence — never a second Status writer under `board_only`. Agents call **one script command** per maintainer action; `GATES` live in `.ai_infra/scripts/pr/prepare.py`.

**Continuation:** Entry reads the board (`python3 -m cursor_workflow project status`); Exit updates Status and Notes (see `.cursor/skills/project-board-ssot/SKILL.md` § Collaboration, ADR-008, `overlays/rules/project-ssot-precedence.mdc`). Ops: `.ai_infra/docs/operations/project-board-collaboration.md`. Offline fallback trackers only when board unavailable. Rate-limit: EXIT_QUEUED (6) → `project outbox` (local buffer, not a second SSOT). **STANDALONE:** permanently decoupled from upstream `mas-workflow-kit` (lineage only — do not merge doctrine back). Read [`HANDOFF.md`](HANDOFF.md) first.

## First reads (onboarding)

1. [`README.md`](README.md) — install, Pattern A, overlay model, `.local/` anchoring
2. [`.ai_infra/docs/README.md`](.ai_infra/docs/README.md) — docs index (linked navigation)
3. [`.ai_infra/docs/handoff/repository-map.md`](.ai_infra/docs/handoff/repository-map.md) — **kit repo only** — SSOT vs generated vs consumer install (not shipped to consumers)
4. [`.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md`](.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md) — plugin bundle, install profiles
5. [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) — shipped vs spec
6. [`.ai_infra/docs/architecture/workflow-architecture.md`](.ai_infra/docs/architecture/workflow-architecture.md) — three planes
7. [`.ai_infra/docs/decisions/README.md`](.ai_infra/docs/decisions/README.md) — ADR index
8. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — `.local/` contract (**Artifact tiers**: base scaffold vs runtime artifacts)
9. [`.ai_infra/docs/governance/workflow-source-owners.md`](.ai_infra/docs/governance/workflow-source-owners.md) — scripts win over prose

**Optional product overlays:** copy rules from [`overlays/rules/`](overlays/README.md) into the target `.cursor/rules/` at install.

Abbreviations: [`.ai_infra/docs/operations/abbreviations-notepad.md`](.ai_infra/docs/operations/abbreviations-notepad.md)

## Rules (always applied in Cursor)

| Rule | Topic |
|------|--------|
| `.cursor/rules/implementation-workflow-governance.mdc` | Slice lifecycle, `.local/.../current` trackers, tests |
| `.cursor/rules/pr-workflow-enforcement.mdc` | PR-first, artifacts, branch safety |
| `.cursor/rules/commit-trailer-format.mdc` | Commit trailers + optional `Assisted-by` (AI) |
| `.cursor/rules/file-docstring-header-relations.mdc` | File headers |
| `.cursor/rules/local-artifact-protection.mdc` | Protected local paths (`.coverage`, `.env`) |
| `.cursor/rules/advisory-audit-alignment-enforcement.mdc` | Architecture-impacting audits → **`enterprise-auditor`** + alignment artifacts |
| `.cursor/rules/project-ssot-precedence.mdc` | Board SSOT precedes local trackers when `project_ssot.enabled` (ADR-008) |

**Product rules** belong in **`overlays/rules/`** at install — see [`overlays/README.md`](overlays/README.md). **Do not duplicate gate lists** in chat or `updates-log.md` — say *prepare gates green* or paste failing command output only.

## Execution workflow

**Resume every session:**

1. If `project_ssot.enabled` → `python -m cursor_workflow project status` → board list/claim (`.cursor/skills/project-board-ssot/SKILL.md` § Continuation contract). Read card Notes for prior handoffs.
2. Else → `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`.

**After every agent part:** update board Status (`in_review` / `done` / Notes + next agent) so continuation is indexed on the Project — not chat-only. Notes attribution: `@owner.github_user/<agent> · <ISO-8601-UTC> · …` (CLI stamps UTC). Local `history/continuity-index.md` rolls ≥3 days; board Notes keep full card lifetime. Ops: `.ai_infra/docs/operations/project-board-collaboration.md`.

Token contract: [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md).

Sequence: `plan → interfaces → implementation → tests → evidence → docs update` (plan lives on the **board card body** when SSOT enabled).

Full handoff checklist: [`.ai_infra/docs/operations/workflow-complete.md`](.ai_infra/docs/operations/workflow-complete.md) (esp. §F).

## Quality gates (single source of truth)

**Default merge gate order** is `resolve_gates()` in **`.ai_infra/scripts/pr/prepare.py`** — **two** subprocesses in universal core (`check_testing_artifacts.py`, `pytest -q`). Kit-dev repos auto-append drift validate + doc facts (**four** total). Append gates at consumer install as needed. `prepare.py` does **not** run governance consistency by default.

**Additionally** run **`python3 .ai_infra/scripts/architecture/check_governance_consistency.py`** and **`python3 .ai_infra/scripts/architecture/check_debrand.py`** when changing governance, workflows, `.cursor/`, `.agents/`, or tracked policy docs.

When adding or changing agents, skills, pipelines, or integration templates, also run **`python3 -m cursor_workflow integrate validate`** (included in governance consistency on kit dev repo).

At slice closure, run **`python3 -m cursor_workflow drift validate`** (or `make drift-validate`) and hand off to **`workflow-drift-guard`** when P0/P1 findings need artifacts.

After doc or agent roster changes, run **`make doc-validate`** (included in **`make gates`**). Before full audits, run **`make verify-all`** — see `.cursor/skills/audit-orchestration/SKILL.md`.

## Commits

Required in every commit message (see **`.cursor/rules/commit-trailer-format.mdc`**):

- `Author: <Your Name>`
- `GitHub-User: @<handle>`

**Render from config:** `.local/user_settings/github.collaboration.yaml` via  
`python3 -m cursor_workflow contributors commit-trailers`.

**AI-assisted work:** optional `Assisted-by:` when AI materially shaped the change. Do **not** add **`Made-with:`** (redundant). You stay accountable for the result.

**PR workflow artifacts** use `Action-By` / `GitHub-User` / `Agent/s` — resolved from the same YAML when scripts run with `--pipeline` (see **`.agents/skills/pr-workflow/SKILL.md`**).

## Skills and agents (Cursor contract)

| Root | Role |
|------|------|
| `.cursor/agents/` | Subagent cards (8) — Task delegation; **`model: auto`**; audit agents write `.local/` artifacts only |
| `.cursor/skills/` | **Canonical protocols** (11 folders: audit, drift, implement loop, activate, project-board, …) |
| `.agents/skills/` | **Maintainer slash skills** (5 folders: `review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`, `audit-alignment` stub → `enterprise-auditor`) — additive in plugin sync |
| `.cursor/rules/` | **7** `alwaysApply` rules in this product repo (6 kit + `project-ssot-precedence`) — high context cost by design |

**Plugin sync:** `.cursor/skills/` wins; `.agents/skills/` never overwrites same folder name (`sync_plugin_bundle.py`).

Do not duplicate skill folder names across `.cursor/skills/` and `.agents/skills/`.

## Branching

Use `feature/`, `fix/`, or `chore/` branches; keep `main` merge-ready. After merge: sync `main` with `origin/main`, remove local + remote feature branch.

## Skills and agents (where to look)

| Role | Entry |
|------|--------|
| Plugin activation | [PLUGIN-USER-GUIDE.md](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md) or `workflow-activate` skill / `python3 -m cursor_workflow activate --directory .` |
| Implement | `.cursor/agents/implementer.md` + `.cursor/skills/implementation-execution-loop/SKILL.md` |
| Project board SSOT | `.cursor/agents/project-board.md` + `.cursor/skills/project-board-ssot/SKILL.md` — `python -m cursor_workflow project …` |
| Integrate infrastructure | `.cursor/agents/integrator-mas-agent.md` + `.cursor/skills/mas-infrastructure-integration/SKILL.md` — validate with `python3 -m cursor_workflow integrate validate` |
| Tests / coverage | `.cursor/agents/test-runner.md` + `.cursor/skills/test-module-coverage/SKILL.md` |
| Verify claims | `.cursor/agents/verifier.md` |
| Operational drift | **`workflow-drift-guard`** — `.cursor/agents/workflow-drift-guard.md` + `.cursor/skills/workflow-drift-audit/SKILL.md` — validate with `python3 -m cursor_workflow drift validate` |
| Audits (canonical) | **`enterprise-auditor`** — `.cursor/agents/enterprise-auditor.md` + `.cursor/skills/enterprise-architecture-audit/SKILL.md` |
| Audit orchestration | `.cursor/skills/audit-orchestration/SKILL.md` — parent runs verify-all + Task delegation (no dedicated agent) |
| Audit module map | `.cursor/skills/audit-module-map/SKILL.md` — optional deep map; invoke via **`enterprise-auditor`** |
| Maintainer PR | `.agents/skills/pr-workflow/SKILL.md` → `review-pr` → `prepare-pr` → `merge-pr` |
| Research corpus (optional) | `.cursor/agents/researcher.md` — off by default |
| MCP | `.ai_infra/mcp_servers/workflow_mcp/` — `python -m workflow_mcp`; [`.cursor/mcp.json.kit.example`](.cursor/mcp.json.kit.example) + [connect-external-mcp](.ai_infra/docs/operations/connect-external-mcp.md) |

Scripts:

- `python .ai_infra/scripts/pr/verify_publish.py --branch <branch>`
- `python .ai_infra/scripts/pr/review.py|prepare.py|merge.py --pr <id|url> --actor "<name>" --agents "<pipeline>"`
- Architecture-impacting PRs: run **`enterprise-auditor`** before `/prepare-pr` when required

## Next work

See `.local/index-and-planning/current/plan.md` and [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md).
