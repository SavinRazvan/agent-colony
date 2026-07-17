# ADR-007: Workflow drift guard (operational drift detection)

**Status:** accepted  
**Date:** 2026-06-29

## Context

MAS Workflow Kit enforces infrastructure parity via `integrate validate`, governance scanners, and testing-artifact gates. Those tools do not cover **operational workflow drift**: plan ↔ tracker ↔ session-pointer incoherence, stale handoff docs, or slice-closure discipline gaps.

The **workflow-drift-guard** capability closes that gap without duplicating architecture audits (`enterprise-auditor`) or claim verification (`verifier`).

## Decision

Introduce a script-first drift validator and MAS-integrated agent per [ADR-006](ADR-006-agent-integration-model.md).

### Artifacts (locked)

| Artifact | Location |
|----------|----------|
| Agent id | `workflow-drift-guard` |
| CLI | `python -m cursor_workflow drift validate` |
| Script SSOT | `.ai_infra/scripts/workflow/check_drift.py` |
| Checks module | `.ai_infra/scripts/workflow/drift_checks.py` |
| Skill | `.cursor/skills/workflow-drift-audit/SKILL.md` |
| Local artifacts | `.local/workflow-artifacts/drift/drift-audit.md`, `drift-todos.md` |

### Profiles

| Profile | When | Checks |
|---------|------|--------|
| `kit-dev` | Default for mas-workflow-kit repo | DRIFT-001…008 (full set) |
| `consumer` | `work-tracker.md` contains exemplar `STARTER-001` | DRIFT-005, DRIFT-008 (relaxed tracker rules) |

Auto-detect profile from `work-tracker.md` unless `--profile` overrides.

### Check catalog

| ID | Severity | Profile | Check |
|----|----------|---------|-------|
| DRIFT-001 | P0 | kit-dev | `.local/index-and-planning/current/` exists |
| DRIFT-002 | P0 | kit-dev | At most one `in_progress` in work-tracker |
| DRIFT-003 | P1 | kit-dev | Active task token appears in plan Current focus |
| DRIFT-004 | P1 | kit-dev | session-pointer Phase/Next sanity vs plan |
| DRIFT-005 | P1 (kit-dev) / P2 skip (consumer) | both | IMPLEMENTATION-STATUS test count vs pytest collect; **PASS (skip)** when file absent (consumer install — not a consumer failure) |
| DRIFT-006 | P2 | kit-dev | test-index Owned tests paths resolve |
| DRIFT-007 | P2 | kit-dev | updates-log fresh when git tree dirty |
| DRIFT-008 | P2 | consumer | Scaffold trackers present |

**Exit policy:** exit code 1 on any P0 failure; P1/P2 advisory in output (same as `integrate validate`).

### Gate placement

| Surface | Includes drift? |
|---------|-----------------|
| `prepare.py` GATES | **Kit-dev only** — `resolve_gates()` appends drift + doc facts when `IMPLEMENTATION-STATUS.md` exists |
| `prepare.py` GATES (consumer) | **No** — universal 2-gate consumer contract |
| `make gates` | **No** — use `make drift-validate` |
| `cursor_workflow health` | Optional P0 warn (diagnostic, non-blocking) |
| Implementer slice closure | **Yes (recommended)** |
| `integrate validate` | INT-011/012 only (infrastructure parity) |

### Overlap boundaries (do NOT duplicate)

| Concern | Owner |
|---------|-------|
| Bare paths, brand terms | `check_governance_consistency.py`, `check_debrand.py` |
| Agent Anchor/MCP, registry parity | `integrate validate` INT-001…014 (incl. INT-011 drift-guard file, INT-012 drift P0 parity, INT-013 doc facts, INT-014 file-header rule anchors) |
| test-plan/index existence | `check_testing_artifacts.py` |
| Plugin/payload SHA drift | `sync_plugin_bundle.py --check` |
| Slice claim verification | `verifier` |
| Architecture scorecard | `enterprise-auditor` |

## Non-goals

- Real-time per-turn agent supervision
- Auto-remediation of drift (findings only)
- Merging drift into `integrate validate` as sole command
- Adding drift to universal 2-gate `prepare.py`

## Consequences

- Maintainers run `make drift-validate` at slice closure; agent writes advisory artifacts under `.local/workflow-artifacts/drift/`.
- ADR index updated in [README.md](README.md).
- Ops mirror: overlap row in [drift-prevention.md](../governance/drift-prevention.md).

## References

- `.local/workflow-artifacts/drift/workflow-drift-guard-plan.md`
- `.cursor/agents/workflow-drift-guard.md`
- `.cursor/skills/workflow-drift-audit/SKILL.md`
- [ADR-006-agent-integration-model.md](ADR-006-agent-integration-model.md)
