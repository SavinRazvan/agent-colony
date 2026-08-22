<!--
File: token-efficiency-enforcement.md
Path: .ai_infra/docs/operations/token-efficiency-enforcement.md
Role: Verifier and drift-guard disproof checklist for token-efficiency claims.
Used By:
 - .cursor/agents/verifier.md
 - .cursor/agents/drift-guard.md
 - .cursor/agents/auditor.md
Depends On:
 - token-efficiency-program.md
 - drift_checks.py
 - check_governance_consistency.py
Notes:
 - Shipped to consumers via copy_ai_infra docs/operations.
-->

# Token efficiency enforcement

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

Verifier-owned disproof checklist. Label each claim: **Verified** | **Partial** | **Not verified**. P0 claims must be Verified before merge prep.

## Disproof checklist

| # | Claim | Disproof command | PR | Severity |
|---|-------|------------------|-----|----------|
| 1 | Thin-index machine-backed | `python3 -m agent_colony doc validate-thin-index` PASS; byte compare per thin-index row via `doc skill-section` | PR-2 | P0 |
| 2 | Lite reduces footprint | `make install-dry-run-lite`; `du -sb /tmp/agent-colony-dry-run-lite/.cursor` vs full dry-run | PR-4 | P0 |
| 3 | Rules tiering | `rg 'alwaysApply: true' .cursor/rules \| wc -l` = **4** | PR-4 | P0 |
| 4 | DRIFT anchors | Fixture agent missing `token-efficiency.md` anchor → DRIFT-014 FAIL | PR-3 | P0 |
| 5 | Profile marker | `activate --profile consumer_lite` → `.local/generated-data/install-profile.json` exists | PR-4 | P0 |
| 6 | Upgrade path | lite → `update --force --profile with_mcp` → 8 agents on disk | PR-4 | P1 |
| 7 | No gate list duplication | `python3 .ai_infra/scripts/architecture/check_governance_consistency.py` GOV-TOKEN-002 PASS | PR-3 | P1 |
| 8 | Validator summaries | `health --summary`, `drift validate --summary`, `project doctor --digest`, `doc validate --summary` emit one-line output | PR-2 | P1 |
| 9 | MCP section URI | `workflow://skills/board-ssot/continuation-contract` returns section only | PR-2 | P1 |
| 10 | Plugin dup WARN | DRIFT-015 WARN when plugin cache rules intersect workspace rules (kit-dev only) | PR-3 | P2 |

## Verification results (2026-08-22 closure)

| # | Label | Evidence |
|---|-------|----------|
| 1 | **Verified** | `doc validate-thin-index --summary` → PASS · checked=17 · fail=0 |
| 2 | **Verified** | `du -sb .cursor` after dry-run: lite **67,032 B** vs full **118,597 B** (~**43%** smaller). *Byte counts vary slightly by payload sync date; re-run `make install-dry-run*` before release audits.* |
| 3 | **Verified** | `rg 'alwaysApply: true' .cursor/rules \| wc -l` → **4** |
| 4 | **Verified** | `test_drift_token_efficiency.py` — missing anchor → DRIFT-014 FAIL |
| 5 | **Verified** | `test_scaffold_profile_prune.py` · marker `.local/generated-data/install-profile.json` |
| 6 | **Verified** | `test_update_profile_restore.py` — lite scaffold → with_mcp → 8 agents |
| 7 | **Verified** | `check_governance_consistency.py` PASS |
| 8 | **Verified** | `test_cmd_doctor_digest` + summary CLIs PASS |
| 9 | **Verified** | `test_read_skill_section_returns_h2_only` · MCP URI in `server.py` |
| 10 | **Verified** | DRIFT-015 PASS with WARN — 6 overlapping basenames (plugin cache ∩ workspace): `advisory-audit-alignment-enforcement.mdc`, `commit-trailer-format.mdc`, `file-docstring-header-relations.mdc`, `implementation-workflow-governance.mdc`, `local-artifact-protection.mdc`, `pr-workflow-enforcement.mdc`; informational P2 per § DRIFT-015 false positives |

## Byte-count disproof (thin-index)

For each row in [token-efficiency.md](token-efficiency.md) § Skill thin-index:

```bash
# Full skill size
wc -c .cursor/skills/<skill>/SKILL.md
# Section size
python3 -m agent_colony doc skill-section --skill <skill> --section "<Prefer column>"
```

Expect section output ≪ full file (example: `board-ssot` § Continuation ~88% smaller).

## DRIFT-014 / 015 / 016

| Check | Severity | kit-dev | consumer | consumer-board |
|-------|----------|---------|----------|----------------|
| DRIFT-014 | P1 | yes | yes | yes |
| DRIFT-015 | P2 | yes | skip | skip |
| DRIFT-016 | P1 | yes | yes | yes |

**Profile-aware DRIFT-016:** On `consumer_lite`, validate thin-index rows only for skills in `skill_allowlist`; skip absent skills with PASS (skip).

## DRIFT-015 false positives

Plugin cache path varies by install. If workspace rules are intentionally mirrored for testing, accept WARN as informational. Do not FAIL merge on DRIFT-015 alone (P2).

## Drift-guard cadence (after PR-3)

1. `python3 -m agent_colony project entry --digest`
2. `python3 -m agent_colony project export --reuse-if-fresh 900` (once per wave)
3. `python3 -m agent_colony drift validate --profile kit-dev --summary`
4. Write `.local/workflow-artifacts/drift/token-efficiency-pass.md`
5. Board Notes: `@user/drift-guard · <ISO-8601-UTC> · DRIFT-014–016 PASS`

## Auditor CHK-TOKEN

On governance-impacting PRs, category `token_contract` per [alignment-audit-schema.md](../roadmap/alignment-audit-schema.md).

## Lite first-run quality (PR-4)

- [x] `board.md` exists and § First-run lite contains CONSENT + TURN steps
- [x] `board-bootstrap --check` path documented (human UI still required)
- [x] `doc skill-section --skill board-shell` is **not** documented as lite default (file absent)
