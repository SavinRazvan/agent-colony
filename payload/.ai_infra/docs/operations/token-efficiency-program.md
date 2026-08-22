<!--
File: token-efficiency-program.md
Path: .ai_infra/docs/operations/token-efficiency-program.md
Role: Program overview for Agent Colony token efficiency — goals, locked decisions, workflows.
Used By:
 - AGENTS.md
 - .cursor/agents/*.md
 - consumer-lite-profile.md
Depends On:
 - token-efficiency.md
 - token-efficiency-enforcement.md
 - ADR-011-consumer-lite-profile.md
Notes:
 - Shipped to consumers via copy_ai_infra docs/operations.
 - Use ASD-STE100: see asd-ste100-prose.md.
-->

# Token efficiency program

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

Program to close the gap between **documented** token contracts ([token-efficiency.md](token-efficiency.md)) and **machine-enforced** behavior. Target release: kit **0.7.0**.

## Goals (G1–G6)

| ID | Goal | Done when | Primary paths |
|----|------|-----------|---------------|
| **G1** | Machine-backed thin index | `doc skill-section` + MCP section URI + DRIFT-016 parity | [doc_cli.py](../../install/agent_colony/doc_cli.py) · [resources.py](../../mcp_servers/agent_colony_mcp/resources.py) · [drift_checks.py](../../scripts/workflow/drift_checks.py) |
| **G2** | Validator digests | `--summary` on health, drift, doctor, doc validate; MCP prepare passes `--summary` | [cli.py](../../install/agent_colony/cli.py) · [check_drift.py](../../scripts/workflow/check_drift.py) · [project_handlers.py](../../install/agent_colony/project_handlers.py) |
| **G3** | Enforcement layer | DRIFT-014–016 + GOV-TOKEN-001/002 + GOV-RULES-001 | [drift_checks.py](../../scripts/workflow/drift_checks.py) · [check_governance_consistency.py](../../scripts/architecture/check_governance_consistency.py) · [token-efficiency-enforcement.md](token-efficiency-enforcement.md) |
| **G4** | Rules tiering | 4 `alwaysApply` + 3 requestable | [.cursor/rules/](../../../.cursor/rules/) · [rules-overlap-matrix.md](../governance/rules-overlap-matrix.md) |
| **G5** | `consumer_lite` profile | End-to-end activate/update/install-contract + profile marker | [manifest.yaml](../../manifest.yaml) · [scaffold.py](../../scripts/install/scaffold.py) · [consumer-lite-profile.md](consumer-lite-profile.md) |
| **G6** | Role-owned documentation | Program + enforcement docs; agent role pointers; ADR-011 | This file · [ADR-011](../decisions/ADR-011-consumer-lite-profile.md) · `.cursor/agents/*.md` |

## Locked decisions (quality-preserving)

| # | Choice | Quality | Tokens |
|---|--------|---------|--------|
| 1 | **6 skills, no 7th `board-shell`** + inline first-run in `board.md` | Lite has no `board-shell/` dir; skill-section would FAIL | Saves ~8 KB skill on disk |
| 2 | **Defer `.agents/skills` prune (Phase 2)** | Keeps `/review-pr`, `/prepare-pr`, `/merge-pr` on disk | ~12 KB vs ~79 KB `.cursor/skills` pruned |
| 3 | **Keep all 7 rule files + global 4+3 tiering** | Upgrade `lite → with_mcp` restores from payload | Drops ~3 KB always-on overhead per turn |

## Consumer workflow

1. **Fresh chat per handoff** — board Notes + `change-index.md` carry state; do not marathon one thread across agents.
2. **Entry digests** — `python3 -m agent_colony project entry --digest` at session start when board SSOT on.
3. **Thin-index reads** — `python3 -m agent_colony doc skill-section --skill <id> --section "<heading>"` instead of full SKILL.md.
4. **Never paste** — green pytest, full gate lists, `updates-log.md` tail (see [token-efficiency.md](token-efficiency.md) § Never paste).
5. **Optional lite profile** — `activate --profile consumer_lite` for smaller fixed overhead ([consumer-lite-profile.md](consumer-lite-profile.md)).

## Kit-dev workflow

1. **Disable duplicate plugin** — when working inside the kit repo, workspace `.cursor/` is SSOT; disable agent-colony marketplace plugin to avoid DRIFT-015 duplication.
2. **Baseline measurement** — record byte totals for rules, skills, `AGENTS.md` before/after slices.
3. **Sync discipline** — edit `.cursor/` SSOT → `make sync-plugin` → `make check-plugin` before push.

## Requestable rules (load on trigger)

| Rule | Load when |
|------|-----------|
| `commit-trailer-format.mdc` | implementer before `git commit` |
| `file-docstring-header-relations.mdc` | implementer/integrator on new source files |
| `advisory-audit-alignment-enforcement.mdc` | before architecture-impacting `/prepare-pr` |

## Phase 2 backlog

- `.agents/skills` allowlist for lite profile (if catalog bloat proven)
- Token instrumentation (if Cursor exposes metering APIs)

## Upgrade paths

| From | To | Command |
|------|-----|---------|
| `consumer_lite` | full kit | `python3 -m agent_colony update --force --profile with_mcp --directory .` |
| any | latest kit | `python3 -m agent_colony update --check --directory .` then `update` |

Profile marker: `.local/generated-data/install-profile.json` (`profile`, `kit_version`).

## Measurement appendix (optional)

1. Record Cursor usage for one slice **before** (marathon chat).
2. Repeat same slice **after** (fresh chat + `consumer_lite` + digests).
3. Compare provider billing or Cursor dashboard.

Honest label: **Partial** unless user supplies billing data. Realistic ceiling: ~35–45% for disciplined `consumer_lite` consumer.

## Related docs

- [token-efficiency.md](token-efficiency.md) — agent read/write contract
- [token-efficiency-enforcement.md](token-efficiency-enforcement.md) — verifier/drift-guard disproof checklist
- [consumer-lite-profile.md](consumer-lite-profile.md) — lite install spec
