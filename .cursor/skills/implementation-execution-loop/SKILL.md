---
name: implementation-execution-loop
description: Disciplined implementation slices with board SSOT continuation and Pattern A gates.
---

# Implementation execution loop

## When

New or continued `feature/` | `fix/` | `chore/` work; recovery from blocked slices.

## Inputs

- **When `project_ssot.enabled`:** `.local/user_settings/github.collaboration.yaml` + `.cursor/skills/project-board-ssot/SKILL.md` (§ Continuation contract) + board card (Acceptance/Rollback/Notes in body)
- **Fallback:** `.local/index-and-planning/current/plan.md`, `work-tracker.md`, `session-pointer.md`
- Project `docs/architecture/` (stub under `.local/.../current/` if present)
- Test trackers when tests change: `test-plan.md`, `test-index.md`
- Closure detail: `.ai_infra/docs/operations/workflow-complete.md` §F
- Boundaries: `overlays/rules/*.mdc` when installed; universal rules in `.cursor/rules/`; ADR-008
- If Notes/user cite `_research_results/sources/<slug>/AGENT_BRIEF.md`, read it before implementing

## Steps

0. **First-run (board shell) — when `project_ssot.enabled`:** run `python3 -m cursor_workflow project board-bootstrap --check` against `board-shell.schema.yaml` (six Playground views + Tier-1 columns on Status board / Prioritized backlog). On FAIL or primary-view Priority/Start date WARNs: do **not** claim work — hand the human to **`/project-board`** + `.cursor/skills/board-shell-onboard/SKILL.md` + `views-setup.md`. **`/enterprise-auditor`** is not day-0.
1. **SSOT select:** `python -m cursor_workflow project status`. If operational → list/claim board card (`claim --last` after create, or claim Ready). When creating: `create-from-template --template slice|bug --priority p0|p1|p2 --size … --estimate …` (see skill § Size↔Estimate; defaults `s`/`1` + Notes if guessed), then `claim --last --agent implementer`. Confirm Status + **Start date** from claim (also set on `set-status`/`handoff` → `in_progress` if empty). Else read plan + tracker; one task `in_progress` locally; tag tasks `[P0]`…`[P3]` in the plan note.
2. Document acceptance + rollback on **card body** (or `plan.md` if fallback): pass `--acceptance` / `--rollback` on `create-from-template`, or after claim run `project set-section --section acceptance|rollback --text '…' --last --agent implementer`. Mid-slice handoffs go in card **Notes** + handoff line (`Priority=p? · Size=? · Estimate=?` + `Tasks: [P…]…`). `handoff` / `set-status` to `in_review`|`done` **exit 5** while Acceptance/Rollback remain `(TBD)`.
3. Implement: contracts → code → tests. **New Python/sources:** module header per `.cursor/rules/file-docstring-header-relations.mdc`.
4. **Gates:** run `python .ai_infra/scripts/pr/prepare.py` (executes `resolve_gates()`; `GATES` is the 2-gate back-compat alias). Add `check_governance_consistency.py` when governance changes. Prefer scoped `pytest` with a short reason.
5. **Commits:** trailers per `.cursor/rules/commit-trailer-format.mdc` (`Author`, `GitHub-User`; `Assisted-by:` when applicable; no `Made-with:`).
6. **Close (board-indexed):** when a PR exists → `mention-pr --pr N`; ensure Assignee via claim/`set-assignee --login` (Issue-at-create); `set-status --to in_review|done`; print `item_id=… · Status=… · Priority=p? · Size=? · Estimate=? · next=…` and `Tasks: [P…]…`. Do **not** dual-write `work-tracker.md` under `board_only`. Fallback: close tracker + `updates-log.md`. Run **`make drift-validate`**; invoke **`workflow-drift-guard`** when P0/P1 findings need artifacts (drift-guard also reads/updates the board).

## Output

Slice • item_id • Status before→after • Priority · Size · Estimate • modules/files • gates outcome • blockers • next agent · Tasks `[P…]`
