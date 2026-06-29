# AGENTS.md

## Project intent

**MAS Workflow Kit** (`mas-workflow-kit`) — universal, installable infrastructure for multi-agent development workflows. Agents call **one script command** per maintainer action; `GATES` are hardcoded in `.ai_infra/scripts/pr/prepare.py` (customize once at install). This is **not** a product application repo unless you add overlays.

## First reads (onboarding)

1. [`README.md`](README.md) — install, Pattern A, overlay model, `.local/` anchoring
2. [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) — shipped vs spec
3. [`.ai_infra/docs/architecture/workflow-architecture.md`](.ai_infra/docs/architecture/workflow-architecture.md) — three planes
4. [`.ai_infra/docs/decisions/README.md`](.ai_infra/docs/decisions/README.md) — ADR index
5. [`.ai_infra/docs/operations/local-workspace-layout.md`](.ai_infra/docs/operations/local-workspace-layout.md) — `.local/` contract
6. [`.ai_infra/docs/governance/workflow-source-owners.md`](.ai_infra/docs/governance/workflow-source-owners.md) — scripts win over prose

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

**Product rules** belong in **`overlays/rules/`** at install — see [`overlays/README.md`](overlays/README.md). **Do not duplicate gate lists** in chat or `updates-log.md` — say *prepare gates green* or paste failing command output only.

## Execution workflow

**Resume every session:** `.local/index-and-planning/current/session-pointer.md` → `plan.md` → `work-tracker.md`. Token contract: [`.ai_infra/docs/operations/token-efficiency.md`](.ai_infra/docs/operations/token-efficiency.md).

Sequence: `plan → interfaces → implementation → tests → evidence → docs update`.

Full handoff checklist: [`.ai_infra/docs/operations/workflow-complete.md`](.ai_infra/docs/operations/workflow-complete.md) (esp. §F).

## Quality gates (single source of truth)

**Default merge gate order** is the `GATES` list in **`.ai_infra/scripts/pr/prepare.py`** — **two** subprocesses in universal core (`check_testing_artifacts.py`, `pytest -q`). Append gates at install as needed. `prepare.py` does **not** run governance consistency by default.

**Additionally** run **`python .ai_infra/scripts/architecture/check_governance_consistency.py`** and **`python .ai_infra/scripts/architecture/check_debrand.py`** when changing governance, workflows, `.cursor/`, `.agents/`, or tracked policy docs.

When adding or changing agents, skills, pipelines, or integration templates, also run **`python -m cursor_workflow integrate validate`** (included in governance consistency on kit dev repo).

At slice closure, run **`python -m cursor_workflow drift validate`** (or `make drift-validate`) and hand off to **`workflow-drift-guard`** when P0/P1 findings need artifacts.

After doc or agent roster changes, run **`make doc-validate`** (included in **`make gates`**). Before full audits, run **`make verify-all`** — see `.cursor/skills/audit-orchestration/SKILL.md`.

## Commits

Required in every commit message (see **`.cursor/rules/commit-trailer-format.mdc`**):

- `Author: <Your Name>`
- `GitHub-User: @<handle>`

**Render from config:** `.local/user_settings/github.collaboration.yaml` via  
`python -m cursor_workflow contributors commit-trailers`.

**AI-assisted work:** optional `Assisted-by:` when AI materially shaped the change. Do **not** add **`Made-with:`** (redundant). You stay accountable for the result.

**PR workflow artifacts** use `Action-By` / `GitHub-User` / `Agent/s` — resolved from the same YAML when scripts run with `--pipeline` (see **`.agents/skills/pr-workflow/SKILL.md`**).

## Skills and agents (Cursor contract)

| Root | Role |
|------|------|
| `.cursor/agents/` | Subagent cards (7) — Task delegation, Anchor entry/exit |
| `.cursor/skills/` | **Canonical protocols** (audit, drift, implement loop, activate, …) |
| `.agents/skills/` | **Maintainer slash skills only** (`review-pr`, `prepare-pr`, `merge-pr`, `pr-workflow`) — additive in plugin sync |
| `.cursor/rules/` | Six universal `alwaysApply` rules — high context cost by design |

**Plugin sync:** `.cursor/skills/` wins; `.agents/skills/` never overwrites same folder name (`sync_plugin_bundle.py`).

Do not duplicate skill folder names across `.cursor/skills/` and `.agents/skills/`.

## Branching

Use `feature/`, `fix/`, or `chore/` branches; keep `main` merge-ready. After merge: sync `main` with `origin/main`, remove local + remote feature branch.

## Skills and agents (where to look)

| Role | Entry |
|------|--------|
| Plugin activation | `workflow-activate` skill or `python -m cursor_workflow activate --directory .` — see [PLUGIN-ARCHITECTURE.md](.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md) § Automated activation |
| Implement | `.cursor/agents/implementer.md` + `.cursor/skills/implementation-execution-loop/SKILL.md` |
| Integrate infrastructure | `.cursor/agents/integrator-mas-agent.md` + `.cursor/skills/mas-infrastructure-integration/SKILL.md` — validate with `python -m cursor_workflow integrate validate` |
| Tests / coverage | `.cursor/agents/test-runner.md` + `.cursor/skills/test-module-coverage/SKILL.md` |
| Verify claims | `.cursor/agents/verifier.md` |
| Operational drift | **`workflow-drift-guard`** — `.cursor/agents/workflow-drift-guard.md` + `.cursor/skills/workflow-drift-audit/SKILL.md` — validate with `python -m cursor_workflow drift validate` |
| Audits (canonical) | **`enterprise-auditor`** — `.cursor/agents/enterprise-auditor.md` + `.cursor/skills/enterprise-architecture-audit/SKILL.md` |
| Maintainer PR | `.agents/skills/pr-workflow/SKILL.md` → `review-pr` → `prepare-pr` → `merge-pr` |
| Research corpus (optional) | `.cursor/agents/researcher.md` — off by default |
| MCP | `.ai_infra/mcp_servers/workflow_mcp/` — `python -m workflow_mcp`; [`.cursor/mcp.json.kit.example`](.cursor/mcp.json.kit.example) + [connect-external-mcp](.ai_infra/docs/operations/connect-external-mcp.md) |

Scripts:

- `python .ai_infra/scripts/pr/verify_publish.py --branch <branch>`
- `python .ai_infra/scripts/pr/review.py|prepare.py|merge.py --pr <id|url> --actor "<name>" --agents "<pipeline>"`
- Architecture-impacting PRs: run **`enterprise-auditor`** before `/prepare-pr` when required

## Next work

See `.local/index-and-planning/current/plan.md` and [`.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md`](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md).
