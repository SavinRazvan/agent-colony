<!--
File: evidence-first.md
Path: .ai_infra/docs/operations/evidence-first.md
Role: Universal doctrine — facts, evidence, responsible action before claims of done.
Used By:
 - .cursor/rules/implementation-workflow-governance.mdc
 - .cursor/skills/evidence-first/SKILL.md
 - AGENTS.md
 - .cursor/agents/*.md
Depends On:
 - docs/governance/workflow-source-owners.md
Notes:
 - Complements ASD-STE100 (writing) and verifier falsify (disproof). Not a substitute for gates or board SSOT.
-->

# Evidence-first (agent doctrine)

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

## Principle

**We always use facts, check for evidence, then take responsible action based on evidence.**

Do not tell the user a task is complete, a version is bumped everywhere, or a fix is shipped until **fresh evidence** supports the claim — or you label the gap explicitly (**Partial**, **Unknown**, **Not verified**).

## Three-step ladder

| Step | Action | Fail if |
|------|--------|---------|
| 1. **Facts** | Restate the claim in testable terms. List surfaces that must be true (repo paths, tags, releases, consumer cache, CLI output). | Claim is vague or untestable |
| 2. **Evidence** | Run commands or open files **now** (not from chat memory). Record path, command, and outcome. | No command output or path cited |
| 3. **Responsible action** | Act on evidence: fix gaps, downgrade the claim, or document deferrals with **owner** and **consequence_if_ignored** on P0/P1 audit findings. | Action contradicts evidence or hides known gaps |

## What counts as evidence

1. **Repository paths** — repo-relative; opened or searched in this session
2. **Command output** — exact command + outcome (exit code, key lines)
3. **External surfaces** — GitHub release/tag, plugin cache manifest, board CLI JSON (when relevant)
4. **User context** — label **`Context:`**; never treat as **Confirmed** for repo or shipped state

## Audit scope boundary

Schema-1 audit artifacts (`Audit-Schema: 1`) cover **repository workflow and kit-process accountability** only. They do **not** certify societal harm, legal compliance, production SLOs, or third-party LLM behavior. Every schema-1 artifact must include `## Audit limits` listing exclusions.

## Assurance stages (schema-1)

Paper §II names **four** audit process stages (Birhane et al., arXiv:2401.14462). Agent Colony adds a fifth **Action** stage for accountability outcomes the paper argues audits must drive.

| Stage | Paper name | Kit owner | Evidence surface |
|-------|------------|-----------|------------------|
| Discovery | Harms Discovery | board / drift-guard | Board cards, drift validate, goal pulse |
| Standards | Standards Identification | Acceptance, CHK-*, DRIFT-* | Criteria in card Acceptance and audit schemas |
| Evaluation | Performance Analysis | auditor / verifier | CHK-* tables, disproof checks, validator output |
| Communication | Audit Communication and Advocacy | Notes + `.local` artifacts | Artifact paths in board Notes; alignment/drift/EA files |
| Action | *(kit extension — accountability outcome)* | owner + `due_slice` + `consequence_if_ignored` + prepare gate | P0/P1 rows in todos; `check_audit_artifacts.py` on schema-1 files |

Do not claim the paper defined five process stages — **Action** is kit-process accountability only.

## Assurance-Level labels (validator)

Schema-1 frontmatter may declare `Assurance-Level: high | reasonable | limited | very_limited`. These are **labels only** — they do not fail merge by themselves. The validator may WARN when P0/P1 evidence is thin under `high`/`reasonable`; empty evidence on P0/P1 is a **hard error**. See `audit_artifact_schema.py` and [alignment-audit-schema.md](../roadmap/alignment-audit-schema.md).

## Labels (shared vocabulary)

| Label | Meaning |
|-------|---------|
| **Verified** | Evidence supports the claim for all required surfaces |
| **Partial** | Some surfaces verified; known gaps listed |
| **Not verified** | Claim not supported or evidence missing |
| **Unknown** | Not inspected — say so; do not guess |
| **Confirmed / Probable / Unknown** | Drift and audit artifacts (see specialized skills) |

## Anti-patterns (mandatory avoid)

- **Repo vs shipped conflation** — Bumping SSOT in `main` ≠ tag, GitHub Release, or Cursor plugin cache updated. Check all three when the user cares about “version shipped”.
- **Memory claims** — “Tests passed earlier” without re-run when challenged or before merge/release.
- **Complete without surfaces** — “Bump everywhere” must match [marketplace-publish.md](../handoff/marketplace-publish.md) Versioning table + publish path when release is in scope.
- **Chat-only approval** — Written deliverables (audits, PR artifacts, alignment) need paths or commands, not opinion.

## Role pointers

| Role | Canon |
|------|--------|
| All agents | This doc + `.cursor/skills/evidence-first/SKILL.md` |
| `verifier` | Disproof loop — `.cursor/agents/verifier.md` § Work |
| `auditor` | Falsify column — `auditor-protocol` § Evidence contract |
| `drift-guard` | Script output + labels — `drift-audit` § Evidence contract |
| `integrator` | Path/command cites — `integrator-protocol` |
| `implementer` | Lifecycle step `evidence` before “done” — `implementation-workflow-governance.mdc` |

## Related

- [token-efficiency.md](token-efficiency.md) — what to read/write; prefer CLI digests
- [marketplace-publish.md](../handoff/marketplace-publish.md) — version SSOT + release checklist
- [workflow-source-owners.md](../governance/workflow-source-owners.md) — executable behavior wins over prose
