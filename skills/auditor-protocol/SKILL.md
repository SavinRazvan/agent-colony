---
name: auditor-protocol
description: Phased, evidence-only enterprise architecture audit for Python repos with weighted scorecard; writes .local workflow artifacts for downstream agents.
---
<!--
File: SKILL.md
Path: .cursor/skills/auditor-protocol/SKILL.md
Role: Enterprise-grade, evidence-only repository architecture audit protocol and workflow hooks.
Used By:
 - .cursor/agents/auditor.md
Depends On:
 - .ai_infra/docs/roadmap/alignment-audit-schema.md
 - .ai_infra/docs/operations/local-workspace-layout.md
Notes:
 - Advisory-only: no auto-remediation during the audit pass unless the user explicitly asks for edits.
-->

# Auditor protocol

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

## Goal

Produce a **step-by-step, facts-first** enterprise architecture assessment of **this** repository. **No invented architecture.** Every significant claim is tied to repository evidence or labeled **Unknown**.

## Evidence contract (mandatory)

**Universal canon:** `.cursor/skills/evidence-first/SKILL.md` · `.ai_infra/docs/operations/evidence-first.md`. Below adds **auditor-specific** labels and scorecard rules.

Audits are **evidence-backed** or they fail the contract. Chat-only opinions without traceable repo pointers are not acceptable in written deliverables.

**What counts as evidence (priority order)**

1. **Repository paths** — repo-relative paths actually opened or searched.
2. **Quoted fragments** — short faithful quotes when non-obvious; line ref when practical (`path:42-48`).
3. **Command output** — only when run during the audit; record **exact command** and **outcome** in §2 Audit Method.
4. **User context** — label **`Context:`**; never treat as **Confirmed** for what the **code** does.

**Per classification**

| Label | Requirement |
|--------|-------------|
| **Confirmed** | At least one repo path (or command + output) directly supports the statement. |
| **Probable risk** | (a) **Observed:** path + fact; (b) **Inference:** labeled; (c) **Falsify:** what would confirm/refute. |
| **Unknown** | What was not inspected or why the repo cannot answer. |

**Scorecard (§9)** — Each category **Evidence** = bulleted paths reviewed. Empty/generic list → **cap score at 3**, confidence **Low** unless explicitly **Unknown**.

**Findings (§7) and actions file** — **Evidence** mandatory; else rephrase as **Unknown** or omit.

**§2 Audit Method** — List: sources read, searches/scans, commands run, scope limits. Readers must reproduce how conclusions were reached.

**Contradictions** — When docs and code disagree, cite **both** paths and state the conflict.

## When to use

- Pre/post major refactor, platform review, diligence-style read.
- Docs vs implementation may diverge.
- Need module-level findings, weighted scorecard, prioritized actions.

## Project workflow integration

**Read (targeted, not all of `.local/`):** `plan.md`, `work-tracker.md`, `test-plan.md`, `test-index.md`, project `docs/architecture/`, `AGENTS.md`, `README.md`, overlay rules, `prepare.py` (`resolve_gates()`).

**Write:**

| Output | Path |
|--------|------|
| Full audit | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md` |
| Actions | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-audit-actions.md` |

**Frontmatter:**

```text
Audit-Type: enterprise-architecture-python
Audited-By: <agent or human>
Action-By: <name>
GitHub-User: <handle>
Date: <ISO-8601>
Evidence-Standard: repository + user context only
```

**Downstream:** **Implementer** → `enterprise-audit-actions.md`; board Ready cards when SSOT on. **Alignment** → `alignment-audit.md` + `alignment-todos.md` per schema. **Module map** → optional `audit-module-map` skill. Brief `updates-log.md` entry after audit.

### Focused alignment pass (architecture-impacting PRs)

When maintainer workflow requires alignment files but not full enterprise report:

- Stay on **`auditor`**; keep **Evidence contract**.
- **Write only:** `alignment-audit.md`, `alignment-todos.md` (schema: `.ai_infra/docs/roadmap/alignment-audit-schema.md`).
- Scope: **touched** roadmap/plan/rules/skills/agents + relevant `src/` / `tests/modules/` — not whole-repo scorecard.
- Short **CHK-*** tick table for PR-touching dimensions; N/A elsewhere.
- Plan/doctrine pulse remains **`drift-guard`** — do not duplicate DRIFT-011 here.

## Context block (paste at start)

```text
Context: Business type · Product · Users/growth · Team · Deployment · Compliance · SLA ·
Goals · Roadmap · Engineering goals · Pain points · Constraints · Future direction ·
Incidents · Performance concerns · Areas to challenge
```

Blank fields → **Unknown – not provided**; lower scoring confidence.

## Operating mode

Facts-first: inventory → quality → risks → recommendations (never reverse). **Strict / evidence-only / no speculation / step-by-step / Python-specific: ON.**

- No invented facts; label **Unknown – not verifiable from repository evidence** when needed.
- Separate **Confirmed** / **Probable risk** / **Unknown** for material statements.
- Challenge docs vs code; **documented architecture ≠ real** without verification.
- No vague likelihood unless explicit **hypothesis** + **evidence gap**.

## Mandatory phases (execute in order; show boundaries in report)

### CHK-* checklists

| Id | Phase | Must cite |
|----|-------|-----------|
| `CHK-ARCH` | 2 | Style, dependency direction, cycles |
| `CHK-GRANULARITY` | 2 / 4 | God modules vs module-boundaries.md or consumer `src/` |
| `CHK-PERF` | 3 | Hot paths; **Unknown** if none observable |
| `CHK-SEC-CODE` | 3 | Secrets, injection/trust boundaries in scope |
| `CHK-SEC-AGENT` | 1 / 3 | Agent write-scope, MCP allowlists — contract compliance |
| `CHK-INFRA-KIT` | 1 / 3 | Three planes, activate, `integrate validate` |
| `CHK-DOCS` | 5 | Goals vs docs; stale AGENTS / IMPLEMENTATION-STATUS |

Report includes **CHK tick table**: id · Pass/Gap/N/A/Unknown · evidence paths.

### PHASE 1 — Repository inventory

Facts only: Python version, deps, frameworks, entry points, packages, jobs, APIs/CLI, data stores, infra clues, tests, docs/ADRs. **Output:** inventory table, architecture sketch, confirmed tech, unknowns.

### PHASE 2 — Implemented architecture

Actual style, boundaries, dependency direction, layering, leakage, god modules/cycles. **CHK-ARCH**, start **CHK-GRANULARITY**. **Output:** profile, boundary analysis, structural risks.

### PHASE 3 — Python engineering and runtime

Packaging, imports, typing, data access, async/jobs, config/secrets, perf/scaling, reliability, security. **CHK-PERF**, **CHK-SEC-CODE**, **CHK-SEC-AGENT**, **CHK-INFRA-KIT**. **Output:** evidence-backed findings only.

### PHASE 4 — Module-by-module audit

Each **major** module: purpose, surfaces, dependencies, boundary (Clear/Blurred/Violated), coupling, layer, leakage, data ownership, perf/security/test clues, recommendation (Keep/Refactor/Split/Merge/Extract/Defer), effort, priority. Finish **CHK-GRANULARITY**. Do not skip major roots.

### PHASE 5 — Goal and plan alignment

Per stated goal in docs: alignment (Strong/Partial/Weak), evidence, gaps, action (Preserve/Improve/Simplify/Postpone/Redesign). **CHK-DOCS**. Plan pulse when plans change = **`drift-guard`** — reference drift artifacts; do not substitute DRIFT scripts here.

### PHASE 6 — Recommended direction

What holds now; what breaks at scale; fix now vs defer; target direction; migration risks; **top 5 highest-ROI** improvements (30–60 days), repo-specific.

## Recommendation standard

Each recommendation: **Problem**, **Evidence**, **Why it matters**, **Recommendation**, **Tradeoffs**, **Implementation**, **Effort**, **Priority**, **Affected modules**. Migration difficulty: Low / Moderate / High / Very High. No generic bullets without repo ties.

## Scoring framework

Scores need concrete evidence; limited evidence → lower confidence. High scores need **positive** evidence; lack of evidence ≠ quality.

**Categories (1–5):** 1 materially inadequate … 5 enterprise-strong.

| Category | Weight |
|----------|--------|
| Architecture clarity | 10% |
| Modularity and boundaries | 10% |
| Domain design | 8% |
| Python packaging and structure | 6% |
| Typing and contract discipline | 5% |
| Data architecture | 10% |
| Performance and scalability | 10% |
| Security architecture | 10% |
| Reliability and resilience | 8% |
| Observability and operability | 7% |
| Deployability and environment strategy | 6% |
| Test architecture and quality gates | 5% |
| Documentation and governance | 5% |
| Strategic alignment | 10% |

Per category: Score, Why, Evidence (paths), path to next level. Then weighted overall, enterprise readiness (Early-stage / Growing / Scaling / Enterprise-capable), confidence (High / Medium / Low).

## Required report structure

`enterprise-architecture-audit.md`:

1. Executive Summary  
2. Audit Method (Evidence contract: sources, searches, commands, scope)  
2b. CHK-* tick table  
3. Repository Inventory  
4. Detected Architecture Profile  
5. Python-Specific Engineering Assessment  
6. Module-by-Module Deep Dive  
7. Findings by Severity (each: Classification, Confidence, Evidence, Recommendation, Effort, Priority)  
8. Performance & Scalability Risk Table  
9. Architecture Scorecard (+ weighted overall + readiness + confidence)  
10. Goal and Plan Alignment  
11. Current vs Target Gap Analysis  
12. Recommended Architectural Direction  
13. Top 5 Highest-ROI Changes  
14. Risks, Unknowns, and Assumptions  
15. Human Validation Required  
16. Final Verdict (Acceptable / Acceptable with Risks / Major Redesign Recommended)

Quality bar: concrete at module level; lower confidence instead of inventing certainty.

## `enterprise-audit-actions.md`

Backlog: **ID** (e.g. `EA-001`), **Title**, **Severity** (P0/P1 mapping), **Classification**, **Evidence** (paths), **Recommendation**, **Effort**, **Migration difficulty**, **Priority**, optional owner, link to audit section.

## Shorter invocation (skill already loaded)

Audit as Principal Enterprise Architect: inventory → implemented architecture → Python quality → modules → risks → goals comparison → transition path. Facts only; weighted scorecard; deliverables under `.local/workflow-artifacts/enterprise-architecture-audit/`.

## Exit criteria

- Phases 1–6 in order; no early recommendation dump.  
- CHK-* tick table present (full or focused).  
- Evidence contract: §2 reproducible; Confirmed/scorecard cite paths; §7/actions have Evidence or **Unknown**.  
- Scorecard with justification; `enterprise-audit-actions.md` with repo-tied items (full audit).  
- Unknowns and human-validation items listed.
