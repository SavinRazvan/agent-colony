<!--
File: token-efficiency.md
Path: .ai_infra/docs/operations/token-efficiency.md
Role: Token-saving contract for agents — what to read, write, and never paste.
Used By:
 - AGENTS.md, .cursor/agents/*.md, agent-workflow-procedures.md
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - docs/governance/workflow-source-owners.md
 - asd-ste100-prose.md
Notes:
 - When project_ssot.enabled: pair with board Status + card Notes for resume-without-chat.
 - Else: session-pointer.md + change-index.md.
 - Use ASD-STE100: see asd-ste100-prose.md (free principles; no ASD dictionary).
 - AI and STE: asd-ste100-prose.md § AI and STE (assist; human reviews; no endorsement).
-->

# Token efficiency (agent contract)

**Use ASD-STE100** for agent-facing prose: [asd-ste100-prose.md](asd-ste100-prose.md). For AI-assisted writing limits, read [asd-ste100-prose.md § AI and STE](asd-ste100-prose.md#ai-and-ste).

## Skill thin-index (intent)

Load the section you need. Do not load whole skills by default.

| Skill | Read when | Prefer |
|-------|-----------|--------|
| `evidence-first` | Any done/complete/shipped claim; user challenges prior answer | Universal contract + role § |
| `board-ssot` | Mutating Status / Tier-1 | § Continuation · § Tier-1 |
| `board-shell` | First-run shell / bootstrap FAIL | § CONSENT GATE · § TURN PROTOCOL |
| `implementer-loop` | Implement slice | Full skill (short) |
| `integrator-protocol` | New agent/skill/MCP | Evidence contract + current phase |
| `drift-audit` | drift-guard pass | Steps 1–3 |
| `auditor-protocol` | Audit task | Evidence contract + current phase |
| `audit-orchestration` | Full audit closure | Phase 0 preflight + delegation rules |
| `audit-module-map` | Deep module topology | Constraints + output contract |
| `mcp-connect` | External MCP setup | Intents table + Pattern A CLI |
| `research-corpus` | Research pack work | Intake + anti-loop |
| `canvas-artifacts` | Canvas/plan snapshots | Tiers table + CLI |
| `test-coverage` | Tests / coverage slice | Procedure steps 1–7 |
| `update-agent-colony` | Consumer kit upgrade | Commands + version gate |
| `workflow-activate` | Consumer install | “When user just installed” |

## Read set (default)

**When `project_ssot.enabled`:**

| Order | Path / command | When |
|-------|----------------|------|
| 1 | `python -m agent_colony project entry` (+ `outbox status` if unsure of quota) | **Every session start** — prefer over unfiltered `list`/`export` |
| 2 | Board card body (Acceptance / Rollback / Notes) | Claimed / In progress card (`get` / claim) |
| 3 | `.cursor/skills/board-ssot/SKILL.md` § Continuation | When mutating Status |
| 4 | `change-index.md` | Resume mid-slice (thin cache) |
| 5 | `test-plan.md`, `test-index.md` | When tests change |
| 6 | `workflow-artifacts/pr/*.md` | Only when phase = review \| prepare \| merge |

**GraphQL tiers (Entry):** `live` (scoped list) → `conserve` (reuse snapshot) → `offline_artifacts` (snapshot + local_trackers pointers; queue writes). One `export --reuse-if-fresh` per parent wave when drift needs a snapshot.

**When disabled / offline fallback:**

| Order | Path | When |
|-------|------|------|
| 1 | `.local/index-and-planning/current/session-pointer.md` | **Every session start** |
| 2 | `plan.md`, `work-tracker.md` | Every implement/verify turn |
| 3 | `change-index.md` | When resuming mid-slice |
| 4 | `test-plan.md`, `test-index.md` | When tests change |
| 5 | `workflow-artifacts/pr/*.md` | Only when phase = review \| prepare \| merge |

**Skip:** `.local/generated-data/**`, `history/archive/**`, full `updates-log.md` body, full `AGENTS.md` unless explicitly tasked.

**Prefer CLI digests (token-efficient):**

| Need | Command |
|------|---------|
| Entry summary | `python -m agent_colony project entry --digest` (or `--json`) |
| Agent roster | `python -m agent_colony doc roster-digest` |
| Doc head | `python -m agent_colony doc summarize --path …` |
| Prepare gates | `python .ai_infra/scripts/pr/prepare.py … --summary` |

## Write set (slice close)

**When board SSOT enabled:**

1. Board Status via `agent_colony project set-status` (+ Notes / handoff line)
2. `change-index.md` — one row per batch  
3. `history/updates-log.md` — **one line** prefixed `YYYY-MM-DDTHH:MM:SSZ` (no gate dumps)
4. `history/continuity-index.md` — optional row when board item + local artifacts touched (keep ≥3 days)
5. Do **not** dual-write tracker `in_progress` under `board_only`

**Offline fallback:**

1. `change-index.md` — one row per batch  
2. `session-pointer.md` — phase, next agent, blockers  
3. `work-tracker.md` / `plan.md` — if status changed  
4. `history/updates-log.md` — **one line** prefixed `YYYY-MM-DDTHH:MM:SSZ` (no gate dumps)

## Never paste in chat

- Full `GATES` list — say *prepare gates green* or paste **failing command stderr only**
- Entire `pytest` output when green
- `updates-log.md` history tail
- Duplicate procedure text already in `prepare.py`

## One command rule (Pattern A)

### PR lane

| Action | Command |
|--------|---------|
| Full prepare | `python .ai_infra/scripts/pr/prepare.py --pr … --actor … --agents …` |
| Governance drift | `python .ai_infra/scripts/architecture/check_governance_consistency.py` |
| Operational drift | `make drift-validate` or `python -m agent_colony drift validate` |
| Infrastructure parity | `make integrate-validate` or `python -m agent_colony integrate validate` |
| Test artifacts guard | (inside prepare) `check_testing_artifacts.py` |

Do **not** run individual gates in chat when `prepare.py` exists unless `verifier` needs a targeted disproof.

### Board lane (when `project_ssot.enabled`)

| Action | Command |
|--------|---------|
| Health | `python -m agent_colony project doctor` |
| Entry (quota-aware) | `python -m agent_colony project entry` |
| Export reuse | `python -m agent_colony project export --reuse-if-fresh 900` |
| Create card | `python -m agent_colony project create-from-template --title "…" --template slice --priority p1 --size s --estimate 1` |
| Claim | `python -m agent_colony project claim --last --agent <name>` |
| Handoff | `python -m agent_colony project handoff --last --agent <name> --next <agent> [--to in_review]` |
| Outbox status | `python -m agent_colony project outbox status` |
| Queue (no live write) | `python -m agent_colony project queue --op … --last --agent <name>` |
| Flush outbox | `python -m agent_colony project outbox flush` |
| Safe recipes | `python -m agent_colony project guide` |

Prefer `--last` after `create-from-template`. Never paste docs placeholder ids. Never paste Project settings UI into the shell. On EXIT_QUEUED (6), do not retry — flush after GraphQL quota recovers.

## Maintainer lane

Use slash skills (`/review-pr`, `/prepare-pr`, `/merge-pr`) — `disable-model-invocation: true` — not subagents.

## Gate source of truth

**Only** `.ai_infra/scripts/pr/prepare.py` → `resolve_gates()` (`GATES` = 2-gate back-compat alias). All prose points there; see `agent-workflow-procedures.md` §3.
