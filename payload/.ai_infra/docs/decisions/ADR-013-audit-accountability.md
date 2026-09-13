# ADR-013: Audit accountability (kit-process)

**Status:** accepted  
**Date:** 2026-09-13

## Context

Agent Colony audits (alignment, drift, enterprise architecture) produce scores and TODOs that can be ignored. Birhane et al. (arXiv:2401.14462) argue an audit is an independent assessment of a **named target** against expectations for **accountability outcomes** — not a scorecard. Marketplace positioning claims discipline and evidence; without owner, deadline, and consequence, those claims are weak.

Related: [ADR-007](ADR-007-workflow-drift-guard.md), [alignment-audit-schema.md](../roadmap/alignment-audit-schema.md), [evidence-first.md](../operations/evidence-first.md).

## Decision

1. **Kit-process accountability** — Kit audits target Agent Colony workflow surfaces (agents, skills, gates, board contracts). They are not societal-harm, legal-compliance, fairness, or product-ML model audits.
2. **Named target + limits** — Schema-1 artifacts (`Audit-Schema: 1`) require `Audit-Scope`, `Named-Target`, and `## Audit limits`. Default scope is `kit` (enum: `kit | product | model | dataset | ecosystem | meta`).
3. **P0/P1 consequence** — Findings at P0/P1 require `owner`, `due_slice` (or `deadline`), and non-placeholder `consequence_if_ignored`.
4. **Machine gate (kit-dev)** — `check_audit_artifacts.py` is the 6th `resolve_gates()` append on kit-dev. Files without `Audit-Schema: 1` skip. Consumer universal gates stay at two.
5. **Independence** — Role contracts (auditor ≠ implementer) plus DRIFT-017 WARN when `Audited-By` equals `Commissioned-By`. No agent sandbox.
6. **Assurance labels** — ICO-style `high | reasonable | limited | very_limited` are labels only; no merge FAIL on `very_limited`.

## Consequences

- Schema and skills stamp accountability frontmatter on new audits.
- Architecture-impacting merges require schema-1 alignment artifacts.
- Paper reference: `assets/other/paper-arxiv-2401.14462v1.txt`.

## Alternatives rejected

| Alternative | Why rejected |
|-------------|--------------|
| Soften marketplace copy without teeth | Undoes differentiation |
| Sandbox / MCP agent-id lock | Out of scope; Cursor agents are not sandboxed |
| Fourth audit agent | Overlaps auditor + drift-guard + verifier |
| Fail ordinary PRs on legacy `.local` audits | Use `Audit-Schema: 1` opt-in instead |

## References

- Birhane et al., “AI auditing: The Broken Bus on the Road to AI Accountability,” arXiv:2401.14462
- [gate-matrix.md](../operations/gate-matrix.md)
- [check_audit_artifacts.py](../../scripts/workflow/check_audit_artifacts.py)
