<!--
File: token-efficiency.md
Path: .ai_infra/docs/operations/token-efficiency.md
Role: Token-saving contract for agents — what to read, write, and never paste.
Used By:
 - AGENTS.md, .cursor/agents/*.md, agent-workflow-procedures.md
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - docs/governance/workflow-source-owners.md
Notes:
 - Pair with session-pointer.md + change-index.md for resume-without-chat.
-->

# Token efficiency (agent contract)

## Read set (default)

| Order | Path | When |
|-------|------|------|
| 1 | `.local/index-and-planning/current/session-pointer.md` | **Every session start** |
| 2 | `plan.md`, `work-tracker.md` | Every implement/verify turn |
| 3 | `change-index.md` | When resuming mid-slice |
| 4 | `test-plan.md`, `test-index.md` | When tests change |
| 5 | `workflow-artifacts/pr/*.md` | Only when phase = review \| prepare \| merge |

**Skip:** `.local/generated-data/**`, `history/archive/**`, full `updates-log.md` body, root handoff megadocs unless explicitly tasked.

## Write set (slice close)

1. `change-index.md` — one row per batch  
2. `session-pointer.md` — phase, next agent, blockers  
3. `work-tracker.md` / `plan.md` — if status changed  
4. `history/updates-log.md` — **one line** (no gate dumps)

## Never paste in chat

- Full `GATES` list — say *prepare gates green* or paste **failing command stderr only**
- Entire `pytest` output when green
- `updates-log.md` history tail
- Duplicate procedure text already in `prepare.py`

## One command rule (Pattern A)

| Action | Command |
|--------|---------|
| Full prepare | `python .ai_infra/scripts/pr/prepare.py --pr … --actor … --agents …` |
| Governance drift | `python .ai_infra/scripts/architecture/check_governance_consistency.py` |
| Operational drift | `make drift-validate` or `python -m cursor_workflow drift validate` |
| Infrastructure parity | `make integrate-validate` or `python -m cursor_workflow integrate validate` |
| Test artifacts guard | (inside prepare) `check_testing_artifacts.py` |

Do **not** run individual gates in chat when `prepare.py` exists unless `verifier` needs a targeted disproof.

## Maintainer lane

Use slash skills (`/review-pr`, `/prepare-pr`, `/merge-pr`) — `disable-model-invocation: true` — not subagents.

## Gate source of truth

**Only** `.ai_infra/scripts/pr/prepare.py` → `GATES`. All prose points there; see `agent-workflow-procedures.md` §3.
