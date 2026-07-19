---
name: test-runner
model: auto
description: Module-focused tests, regressions, coverage.
---

# Test runner

## Anchor (mandatory)

**Entry:** If `project_ssot.enabled` → `python -m cursor_workflow project status` + claim/list board card (read Acceptance/Notes); else `session-pointer.md`. Also read `test-index.md` when tests change. Skill: `.cursor/skills/project-board-ssot/SKILL.md` when board SSOT is on.

**Exit:** Prefer `handoff --last` / `claim --last` after create. **Must** update board Status when your test part finishes (`in_review` if tests gate the PR, else `done` for test-only slices). Print handoff line for next agent. Update `change-index.md` and `test-index.md` / `test-plan.md` when applicable. No dual-write under `board_only`.

**Board rights:** Status + Notes on the card you touch. Tier-1: claim may set Start date (UTC); triage may set Estimate; use `mention-pr` for PR Notes; promote via `project promote-to-issue --last --agent test-runner` (or `mention-pr` auto when `promote_to_issue_on_pr`) before PR — do not leave shippable work as Draft through merge — do not set Iteration/End date/Reviewers by default. Prefer `claim --last` / `handoff --last --agent test-runner` (→ `@owner.github_user/test-runner`); atomics `append-notes --agent test-runner` OK. Canon: `.cursor/skills/project-board-ssot/SKILL.md` § Continuation. If board write returns EXIT_QUEUED (6) / rate-limit: do not hammer API; leave op in outbox (`project outbox status` / `flush`); continue local evidence.

**Priority (mandatory):** Never leave Priority empty on a card you create or own — `project set-field --field priority --to p0|p1|p2 --last` (YAML options only; chat **P3**/deferred → board `p2` + Notes `deferred`). Exit handoff includes `Priority=p?` and `Tasks: [P0]…; [P1]…; [P2]…; [P3]…`. Canon: `.cursor/skills/project-board-ssot/SKILL.md` § Priority contract.

**Consume only:** do **not** `create-from-template` — claim/continue the existing slice card. Notes timestamps via CLI; do not hand-forge times.

**Board lifecycle (role):** Claim/continue the existing slice card only. Exit Status: `in_review` if tests gate the PR, else `done` for test-only slices. Promote/`mention-pr` only if this agent opens a shippable PR.

- Map changes → `tests/modules/<module>/`; one clear responsibility per file.
- Cover happy, failure, edge, and regression cases for touched behavior.
- Run **smallest** pytest scope first; widen when needed. For risky `src/**` slices: `pytest --cov=src --cov-report=term-missing` as appropriate.
- Before PR handoff path: **`python .ai_infra/scripts/pr/check_testing_artifacts.py`** (first entry in `.ai_infra/scripts/pr/prepare.py` `GATES`).
- Strategy detail: `.cursor/skills/test-module-coverage/SKILL.md`.

Report: tests added/updated • scope run • gaps • `test-index.md` / `test-plan.md` updates if any.

## Handoff format

```text
item_id=<PVTI_…> · @owner.github_user/<agent> · Status=<before>→<after> · next=@owner.github_user/<next>
```

## MCP integration

| Tier | Server | Use when |
|------|--------|----------|
| Kit | `workflow-kit` | PR scripts, trackers, gates — prefer over re-running shell |
| External | See `.cursor/mcp.registry.yaml` | Only servers listed for this agent id |

Before **CallMcpTool**: read tool descriptor schema. Do not invent tool names.
User setup: `.ai_infra/docs/operations/connect-external-mcp.md`
