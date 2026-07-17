# ADR-002: Path canon

**Status:** accepted  
**Date:** 2026-06-14

## Context

Legacy prose referenced `scripts/pr/` at repo root. Kit scripts live under `.ai_infra/scripts/`.

## Decision

- Canonical prepare gates: `python .ai_infra/scripts/pr/prepare.py`
- Canonical governance check: `python .ai_infra/scripts/architecture/check_governance_consistency.py`
- Path resolver: `.ai_infra/paths.py` (`pr_script`, `architecture_script`, `pr_script_rel`)
- Agent surfaces must not use bare `scripts/pr/` (enforced by drift scanner)

## Consequences

- MCP `runner.py` resolves `.ai_infra/` first, legacy `scripts/` second.
- Manifest copies `scripts/pr` and `scripts/architecture` under consumer `.ai_infra/`.
