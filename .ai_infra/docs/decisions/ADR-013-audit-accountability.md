# ADR-013: Audit accountability (kit-process)

**Status:** accepted  
**Date:** 2026-09-13

## Context

Agent Colony audits (alignment, drift, enterprise architecture) produce scores and TODOs that can be ignored. Birhane et al. (arXiv:2401.14462) argue an audit is an independent assessment of a **named target** against expectations for **accountability outcomes** — not a scorecard. Marketplace positioning claims discipline and evidence; without owner, deadline, and consequence, those claims are weak.

The first program shipped doctrine and an opt-in 6th kit-dev gate. This decision also closes the enforcement gap: architecture-impacting merges must not treat Schema-0 stubs as sufficient.

Related: [ADR-007](ADR-007-workflow-drift-guard.md), [alignment-audit-schema.md](../roadmap/alignment-audit-schema.md), [evidence-first.md](../operations/evidence-first.md).

## Decision

1. **Kit-process accountability** — Kit audits target Agent Colony workflow surfaces (agents, skills, gates, board contracts). They are not societal-harm, legal-compliance, fairness, or product-ML model audits.
2. **Named target + limits** — Schema-1 artifacts (`Audit-Schema: 1`) require `Audit-Scope`, `Named-Target`, `## Accountability summary`, and `## Audit limits`. Default scope is `kit` (enum: `kit | product | model | dataset | ecosystem | meta`).
3. **P0/P1 consequence** — Findings at P0/P1 require `owner`, `due_slice` (or `deadline`), and non-placeholder `consequence_if_ignored`. Finding rows require severity `P0|P1|P2`.
4. **Machine gate (kit-dev)** — `check_audit_artifacts.py` is the 6th `resolve_gates()` append on kit-dev. Files without `Audit-Schema: 1` skip. Consumer universal gates stay at two.
5. **Architecture-impacting** — `check_audit_artifacts.py --arch-impacting` (via `merge.py`) requires `alignment-audit.md` and `alignment-todos.md` to **exist**, carry `Audit-Schema: 1`, and **pass** validation (no skip). Forced when CLI flag, pipeline `architecture_impacting` / `requires_alignment_artifacts`, or kit-dev path-trigger (rules/skills/agents/ADRs/arch docs/PR+audit scripts). Open P0/P1 `status` fails. Prepare refuses `--skip-gates` on architecture_impacting pipelines.
6. **Independence** — Role contracts (auditor ≠ implementer) plus DRIFT-017 WARN when `Commissioned-By` is missing/placeholder or `Audited-By` equals `Commissioned-By`. No agent sandbox.
7. **Assurance labels** — ICO-style `high | reasonable | limited | very_limited` are labels only; no merge FAIL on `very_limited`.

## Consequences

- Schema and skills stamp accountability frontmatter on new audits.
- Architecture-impacting merges require schema-1 alignment artifacts that pass the validator.
- Pipeline / path-trigger auto-enforcement at merge; ordinary prepare still skips unstamped leftovers.
- Default prepare scan still skips unstamped leftover `.local` files.
- Paper reference: `assets/other/paper-arxiv-2401.14462v1.txt`.

## Alternatives rejected

| Alternative | Why rejected |
|-------------|--------------|
| Soften marketplace copy without teeth | Undoes differentiation |
| Sandbox / MCP agent-id lock | Out of scope; Cursor agents are not sandboxed |
| Fourth audit agent | Overlaps auditor + drift-guard + verifier |
| Fail ordinary PRs on legacy `.local` audits | Use `Audit-Schema: 1` opt-in instead |
| Auto `--arch-impacting` on every prepare | Would brick ordinary PRs on leftover Schema-0 stubs |

## References

- Birhane et al., “AI auditing: The Broken Bus on the Road to AI Accountability,” arXiv:2401.14462
- [gate-matrix.md](../operations/gate-matrix.md)
- [check_audit_artifacts.py](../../scripts/workflow/check_audit_artifacts.py)
