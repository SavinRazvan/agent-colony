# AGENTS.md

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Project intent

**Agent Colony** (`agent-colony`) — installable multi-agent workflow with **GitHub Project** as the only writable SSOT when `project_ssot.enabled` and `sync_policy: board_only`.

| Surface | Role |
|---------|------|
| **GitHub Project** | Backlog, Status, Priority/Size, continuation. **Entry** = read board; **Exit** = Status + Notes. |
| **Local `.local/`** | Evidence only (PR Pattern A, audits, gates, secrets, outbox). Never a second Status writer under `board_only`. |

**Non-negotiables**

- No dual-write of Status to `work-tracker.md` / `session-pointer.md` when `board_only`.
- Shippable cards as **Issues** (`item_kind_default: issue`). Draft is scratch-only.
- Fill **Tier-1** fields: Status, Priority, Size/Estimate, Start/End dates, Assignee, Linked PR (`mention-pr`).
- EXIT_QUEUED (6) → `project outbox`; outbox is not SSOT.
- **Evidence-first:** use facts, check fresh evidence, then act — [evidence-first.md](.ai_infra/docs/operations/evidence-first.md) · skill `evidence-first`. Do not claim complete without evidence or explicit **Partial** gaps.

**Consumer install:** plugin + `/workflow-activate` — see [PLUGIN-USER-GUIDE](.ai_infra/docs/operations/PLUGIN-USER-GUIDE.md#product-promise).

## First reads

1. [`README.md`](README.md) · [`CONTRIBUTING.md`](CONTRIBUTING.md) · [consumer-quickstart](.ai_infra/docs/operations/consumer-quickstart.md)
2. [docs index](.ai_infra/docs/README.md) · [repository-map](.ai_infra/docs/handoff/repository-map.md) · [PLUGIN-ARCHITECTURE](.ai_infra/docs/handoff/PLUGIN-ARCHITECTURE.md)
3. [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md) · [workflow-architecture](.ai_infra/docs/architecture/workflow-architecture.md)
4. [ADR index](.ai_infra/docs/decisions/README.md) · [local-workspace-layout](.ai_infra/docs/operations/local-workspace-layout.md) · [multi-consumer-isolation](.ai_infra/docs/operations/multi-consumer-isolation.md) · [workflow-source-owners](.ai_infra/docs/governance/workflow-source-owners.md)

Token contract: [token-efficiency.md](.ai_infra/docs/operations/token-efficiency.md) · program: [token-efficiency-program.md](.ai_infra/docs/operations/token-efficiency-program.md).

## Rules (always applied)

**7 rules** — **4 always-on** + **3 requestable** (kit 0.7.0). See [token-efficiency-program.md](.ai_infra/docs/operations/token-efficiency-program.md).

| Rule | Topic |
|------|--------|
| `implementation-workflow-governance.mdc` | Slice lifecycle, trackers, tests |
| `pr-workflow-enforcement.mdc` | PR-first, artifacts, branch safety |
| `local-artifact-protection.mdc` | Protected `.coverage`, `.env` |
| `project-ssot-precedence.mdc` | Board SSOT (ADR-008) |
| `commit-trailer-format.mdc` | Commit trailers (requestable) |
| `file-docstring-header-relations.mdc` | File headers (requestable) |
| `advisory-audit-alignment-enforcement.mdc` | Alignment audits (requestable) |

Product rules: [`overlays/rules/`](overlays/README.md). Say *prepare gates green* — do not duplicate gate lists.

## Execution

**Resume:** `project_ssot.enabled` → `python3 -m agent_colony project entry`, claim one card (`.cursor/skills/board-ssot/SKILL.md`). First-run: `board-bootstrap --check` fail → `/board` + `board-shell`. Else: `session-pointer.md` → `plan.md` → `work-tracker.md`.

**After each agent:** update board Status/Notes. Tier-1 on owned cards — see board-ssot skill § Tier-1.

### Board Pattern A

| Step | Command | Notes |
|------|---------|--------|
| Entry | `project entry` | Quota-aware read |
| Claim | `project claim --last --agent <name>` | In progress; Start date |
| Done | `project set-status --to done` / `handoff --to done` | End date |
| Triage | `project set-field --field priority\|size\|estimate --to … --last` | Own/triage cards |
| Promote | `project promote-to-issue --last --agent <name>` | Draft→Issue |
| PR link | `project mention-pr --pr N --last --agent <name>` | Notes + auto-promote |
| Handoff | `project handoff --last --agent <name> --next <peer> --to in_review` | Status + Notes |

Do not leave shippable work as Draft. Handoff: [workflow-complete.md](.ai_infra/docs/operations/workflow-complete.md) §F.

Sequence: `plan → interfaces → implementation → tests → evidence → docs`.

## Quality gates

Merge gate order: `resolve_gates()` in `.ai_infra/scripts/pr/prepare.py` — **two** universal + **three** kit-dev append (**five** total). Also run `check_governance_consistency.py` and `check_debrand.py` when changing governance, `.cursor/`, `.agents/`, or policy docs.

Slice closure: `python3 -m agent_colony drift validate`; hand off `drift-guard` on P0/P1. Doc/agent changes: `make doc-validate`. Audits: `make verify-all` — see `audit-orchestration` skill.

## Commits

Required: `Author:` + `GitHub-User:` (see `commit-trailer-format.mdc`). Render: `python3 -m agent_colony contributors commit-trailers`. Optional `Assisted-by:` when AI materially shaped work; no `Made-with:`. Human author reviews and validates. AI assists; it does not replace review. See [asd-ste100-prose.md § AI and STE](.ai_infra/docs/operations/asd-ste100-prose.md#ai-and-ste).

PR artifacts: `Action-By` / `GitHub-User` / `Agent/s` via `--pipeline` (`.agents/skills/pr-workflow/SKILL.md`).

## Skills and agents

| Root | Role |
|------|------|
| `.cursor/agents/` | 8 agent cards — `auditor`, `board`, `drift-guard`, `implementer`, `integrator`, `researcher`, `test-runner`, `verifier` |
| `.cursor/skills/` | 15 canonical protocols — see [repository-map](.ai_infra/docs/handoff/repository-map.md) |
| `.agents/skills/` | 6 maintainer slash skills (PR workflow) |
| `.cursor/rules/` | 7 rules (4 always-on + 3 requestable) |

| Role | Entry |
|------|--------|
| Activate | `workflow-activate` / `python3 -m agent_colony activate --directory .` |
| Board SSOT | `board` + `board-ssot` skill |
| Implement | `implementer` + `implementer-loop` |
| Integrate | `integrator` + `integrator-protocol` |
| Tests | `test-runner` + `test-coverage` |
| Verify | `verifier` (evidence only) + `evidence-first` |
| Drift | `drift-guard` + `drift-audit` |
| Audit | `auditor` + `auditor-protocol` |
| Research | `researcher` + `research-corpus` |
| MCP | `agent_colony_mcp` + `mcp-connect` |
| Canvas | `canvas-artifacts` skill |

**Task `subagent_type`:** use on-disk ids (`integrator`, `auditor`, `drift-guard`, `board`); retire legacy names.

**Branching:** `feature/`, `fix/`, `chore/` → PR-first workflow. Optional cleanup: `/full-pr-workflow`.

## Next work

`.local/index-and-planning/current/plan.md` · [IMPLEMENTATION-STATUS](.ai_infra/docs/handoff/IMPLEMENTATION-STATUS.md)
