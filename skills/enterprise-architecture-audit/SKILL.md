---
name: enterprise-architecture-audit
description: Phased, evidence-only enterprise architecture audit for Python repos with weighted scorecard; writes .local workflow artifacts for downstream agents.
---
<!--
File: SKILL.md
Path: .cursor/skills/enterprise-architecture-audit/SKILL.md
Role: Enterprise-grade, evidence-only repository architecture audit protocol and workflow hooks.
Used By:
 - .cursor/agents/enterprise-auditor.md
Depends On:
 - .ai_infra/docs/roadmap/alignment-audit-schema.md
 - .ai_infra/docs/operations/local-workspace-layout.md
Notes:
 - Advisory-only: no auto-remediation during the audit pass unless the user explicitly asks for edits.
-->

# Enterprise Architecture Audit (Python, audit-grade)

## Goal

Produce a **step-by-step, facts-first** enterprise architecture and engineering assessment of **this** repository, suitable for senior technical and executive decisions. **No invented architecture.** Every significant claim is tied to repository evidence or labeled **Unknown**.

## Evidence contract (mandatory)

Audits are **evidence-backed** or they fail the contract. Chat-only opinions without traceable repo pointers are not acceptable in the written deliverables.

**What counts as evidence (in priority order)**

1. **Repository paths** — repo-relative file or directory paths you actually opened or searched (e.g. `src/core/foo.py`, `pyproject.toml`, `.github/workflows/`).
2. **Quoted fragments** — short, faithful quotes from files (configs, docstrings, key symbols) when the claim is non-obvious; add line reference when practical (e.g. `path:42-48` or “see `symbol` in `path`”).
3. **Command output** — only when run during the audit (e.g. `pytest`, `rg`, `python scripts/...`); record the **exact command** and **outcome** in §2 Audit Method, not vague “tests pass.”
4. **User context** — label as **`Context:`** (field name); use for business/deployment intent **only**; never treat as **Confirmed** for claims about what the **code** does.

**Per classification**

| Label | Requirement |
|--------|-------------|
| **Confirmed** | At least one repo path (or command + output) that directly supports the statement. |
| **Probable risk** | (a) **Observed:** path + fact; (b) **Inference:** explicitly labeled; (c) **Falsify:** what evidence would confirm or refute. |
| **Unknown** | State **what was not inspected** or **why** the repo cannot answer (e.g. no deployment manifests in tree, secrets not in repo). |

**Scorecard (§9)** — For **each** category, the **Evidence** subsection must be a **bulleted list of paths** (and optional line/symbol refs) representing what was actually reviewed for that score. If the list is empty or only generic (“reviewed the codebase”), **cap the score at 3** and set scoring confidence to **Low** unless the gap is explicitly **Unknown**.

**Findings (§7) and actions file** — **Evidence** is mandatory. If you cannot cite a path or command output, rephrase as **Unknown** or omit the finding.

**§2 Audit Method** — Must list: **sources read** (paths), **searches or scans** (e.g. patterns, tools), **commands run** (if any), and **scope limits** (what was out of scope or time-boxed). Readers must be able to **reproduce** how conclusions were reached.

**Contradictions** — When docs and code disagree, cite **both** sides (paths) and state the conflict before recommending.

## When to use

- Pre- or post-major refactor, platform review, or diligence-style read of the codebase.
- When documentation and implementation may diverge (challenge documented architecture with code and config evidence).
- When you need **module-level** findings, a **weighted scorecard**, and a **prioritized action list** for implementers.

## Project workflow integration

**Read (do not load all of `.local/` blindly):**

- `.local/index-and-planning/current/plan.md`, `work-tracker.md` — current slice context (if missing, say so).
- `test-plan.md`, `test-index.md` when assessing test architecture.
- Project `docs/architecture/`, `AGENTS.md`, `README.md` for stated intent vs implementation.
- Overlay rules (`overlays/rules/*.mdc`) when installed.
- `.ai_infra/scripts/pr/prepare.py` (`GATES`) for quality-gate reality.

**Write — create directory if needed:**

| Output | Path |
|--------|------|
| Full audit (all sections below) | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-architecture-audit.md` |
| Prioritized actions for implementers | `.local/workflow-artifacts/enterprise-architecture-audit/enterprise-audit-actions.md` |

**Report frontmatter (top of `enterprise-architecture-audit.md`):**

```text
Audit-Type: enterprise-architecture-python
Audited-By: <agent name or human>
Action-By: <name>
GitHub-User: <handle>
Date: <ISO-8601 date>
Evidence-Standard: repository + user context only
```

**Downstream agents:**

- **Implementer:** consume `enterprise-audit-actions.md`; move agreed items into `work-tracker.md` (one primary `in_progress` task). Follow `.cursor/skills/implementation-execution-loop/SKILL.md`.
- **Alignment / maintainer:** if findings are doc-policy-roadmap drift, also record P0/P1 items per `.ai_infra/docs/roadmap/alignment-audit-schema.md` in `.local/workflow-artifacts/alignment/alignment-audit.md` and `alignment-todos.md` (advisory).
- **Module map depth:** optionally run `.cursor/skills/audit-module-map/SKILL.md` for `module-map` / HTML export; cite those paths as evidence in the enterprise report.

**After the audit:** add a brief entry to `.local/index-and-planning/history/updates-log.md` (artifacts written, no gate laundry lists).

### Focused alignment pass (architecture-impacting PRs)

When the **maintainer workflow** requires alignment files for `--arch-impacting` but a **full** `enterprise-architecture-audit.md` is not requested:

- Stay on **`enterprise-auditor`** and keep the **Evidence contract** (paths for every Confirmed finding; §2 Audit Method lists what you read/searched).
- **Write only** (unless the user also wants the full report):
  - `.local/workflow-artifacts/alignment/alignment-audit.md`
  - `.local/workflow-artifacts/alignment/alignment-todos.md`
- Use **`.ai_infra/docs/roadmap/alignment-audit-schema.md`** for finding shape and P0/P1/P2 handling.
- Scope: compare **touched** roadmap/plan/strategy docs, rules/skills/agents, `src/` + `tests/modules/` relevant to the PR — not a whole-repo scorecard.
- **Optional:** note in `alignment-audit.md` that a full enterprise scorecard was deferred.

---

## Context block (required from user — paste at start of engagement)

```text
Context:
- Business type:
- Product type:
- Current users/customers:
- Expected growth over next 12–24 months:
- Team size and structure:
- Deployment platform:
- Compliance/security requirements:
- Uptime/SLA expectations:
- Main business goals:
- Main roadmap items:
- Main engineering goals:
- Main pain points today:
- Known constraints:
- Intended future architecture direction:
- Known incidents or operational failures:
- Performance concerns already suspected:
- Areas we especially want challenged:
```

If the user leaves fields blank, label gaps **Unknown – not provided in context** and lower scoring confidence.

---

## Operating mode (non-negotiable)

```text
Do not jump to recommendations before completing repository inventory and implemented architecture assessment.

Facts-first rule:
- First describe what exists
- Then assess quality
- Then identify risks
- Then recommend changes
- Never reverse that order

Strict mode: ON
Evidence-only mode: ON
No speculation mode: ON
Step-by-step mode: ON
Python-specific analysis mode: ON
```

**Rules:**

- Do not invent facts. If not verifiable from the repo (and provided context), say: **Unknown – not verifiable from repository evidence**.
- Separate **Confirmed** / **Probable risk** / **Unknown** for material statements.
- Do not describe architecture as confirmed unless supported by evidence (paths, configs, imports, entrypoints).
- Be critical and precise. Prefer **insufficient evidence** over assumptions.
- If evidence conflicts (e.g. docs vs code), call out the conflict.

**Anti-hallucination:** Do not use vague likelihood language (“likely”, “probably intended”) unless framed as an explicit **hypothesis** with the **evidence gap** stated.

**Challenge assumptions:** Actively look for contradictions between folder structure, import graph, runtime entrypoints, and deployment clues. **Documented architecture is not assumed to be real architecture** without verification.

**Review discipline:**

1. Inventory before judgment  
2. Evidence before interpretation  
3. Interpretation before recommendation  
4. Recommendation before roadmap  
5. Unknowns explicitly called out  

---

## Mandatory phases (execute in order; show phase boundaries in the written report)

### PHASE 1 — Repository inventory (descriptive only)

Establish facts: Python version(s), dependency tooling, frameworks, entry points, main packages, workers/jobs, APIs/CLI/scripts, data stores, messaging, infra/deployment clues, test layout, docs/ADRs/config.  
**Output:** inventory table, architecture map sketch (text), confirmed technologies, unknowns.

### PHASE 2 — Implemented architecture

Infer **actual** style (monolith, layered monolith, modular monolith, services, event-driven, hybrid, etc.), boundaries, dependency direction, layering, shared core, framework leakage, god modules/cycles.  
**Output:** detected profile, boundary analysis, layering assessment, risks visible from structure.

### PHASE 3 — Python engineering and runtime

Assess: packaging/layout, import discipline, typing and contracts, data access/ORM patterns, async/concurrency/jobs, config/secrets, performance/scaling clues, reliability/operability, security.  
**Output:** evidence-backed findings only; label Confirmed / Probable risk / Unknown.

### PHASE 4 — Module-by-module audit

For each **major** module/package under `src/` (and analogous roots): name, purpose, evidence of responsibility, public surfaces, dependencies, boundary quality (Clear / Blurred / Violated), coupling/cohesion, layer placement, framework leakage, data ownership clues, perf/security/ops concerns, test clues, recommendation (Keep / Refactor / Split / Merge / Extract / Defer), why, effort, priority (Now / Next / Later).  
Use **Unknown** where needed. **Do not skip** module-level sections for major roots.

### PHASE 5 — Goal and plan alignment

For each stated goal/roadmap/architecture intent found in repo docs: alignment (Strong / Partial / Weak), evidence, gaps, risks, recommended action (Preserve / Improve / Simplify / Postpone / Redesign). Tie to evidence, not generic advice.

### PHASE 6 — Recommended direction

Acceptable for now; what breaks under growth; fix immediately vs intentional deferral; target direction; evolution vs redesign; migration risks; **top 5 highest-ROI** improvements (30–60 days), each repo-specific.

---

## Recommendation standard

Every meaningful recommendation must include: **Problem**, **Evidence**, **Why it matters**, **Recommendation**, **Tradeoffs**, **Implementation approach**, **Effort estimate**, **Priority**, **Affected modules**.  
Avoid generic bullets (“improve modularity”, “add observability”) without repo ties.

**Migration difficulty** (for each major recommendation): Low / Moderate / High / Very High.

**Optional:** **Top 10 modules by architectural risk** (ranked, with evidence).

**Optional closing section — “Potential dissent from a second architect”:** what a reviewer might dispute, weak evidence, decisions needing human validation.

---

## Scoring framework

**Scoring rules:**

- Do not assign scores from intuition alone.  
- Every score references concrete evidence.  
- If evidence is limited, **lower confidence**.  
- **High scores require positive evidence**, not absence of problems.  
- **Lack of evidence is not evidence of quality.**  
- Do not reward absence of visible issues with high scores.

**Categories (1–5):** 1 = materially inadequate for enterprise; 2 = weak/high-risk; 3 = workable/moderate risk; 4 = strong with manageable gaps; 5 = enterprise-strong/low risk.

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

For **each** category: Score, Why, Evidence, What is needed to reach the next level.  
Then: **weighted overall score**, **enterprise readiness level** (Early-stage / Growing / Scaling / Enterprise-capable), **scoring confidence** (High / Medium / Low).

---

## Required report structure

Write `enterprise-architecture-audit.md` with these sections:

1. Executive Summary  
2. Audit Method (must satisfy the **Evidence contract**: sources, searches, commands, scope limits)  
3. Repository Inventory  
4. Detected Architecture Profile  
5. Python-Specific Engineering Assessment  
6. Module-by-Module Deep Dive  
7. Findings by Severity (Critical / High / Medium / Low — each with Classification, Confidence, Why it matters, Evidence, Recommendation, Tradeoffs, Effort, Priority, Affected areas)  
8. Performance & Scalability Risk Table  
9. Architecture Scorecard (+ weighted overall + readiness + confidence)  
10. Goal and Plan Alignment  
11. Current vs Target Gap Analysis  
12. Recommended Architectural Direction  
13. Top 5 Highest-ROI Changes  
14. Risks, Unknowns, and Assumptions  
15. Human Validation Required  
16. Final Verdict (Acceptable / Acceptable with Risks / Major Redesign Recommended) — rationale, biggest blocker, executive takeaway  

**Closing quality bar:**

```text
Do not summarize vaguely. Be concrete at module level.
If evidence is incomplete, lower confidence instead of inventing certainty.
The review should help a senior engineering leader decide:
- what is fine now
- what becomes dangerous at scale
- what to fix first
- what architecture direction best supports the business plan
```

---

## `enterprise-audit-actions.md` format

Structured backlog for implementers:

- **ID** (e.g. `EA-001`)  
- **Title**  
- **Severity** (map enterprise Critical/High to P0/P1 where appropriate for internal tracking)  
- **Classification:** Confirmed / Probable risk / Unknown  
- **Evidence** (paths)  
- **Recommendation** (one concrete step)  
- **Effort** / **Migration difficulty** / **Priority**  
- **Suggested owner role** (optional)  
- **Link** to section in `enterprise-architecture-audit.md`  

---

## Shorter invocation prompt (when full skill context is already loaded)

```text
Audit this Python repository as a Principal Enterprise Architect.

Work step by step. Facts only. No guessing.

Process:
1. Inventory the repo
2. Identify the actual implemented architecture
3. Assess Python-specific engineering quality
4. Audit each major module/package
5. Assess risks, scalability, security, reliability, and operability
6. Compare current architecture to goals and target direction (from docs + context)
7. Recommend a practical transition path

Rules:
- Every major claim must include repository evidence (paths)
- If not verifiable, say "Unknown – not verifiable from repository evidence"
- Distinguish Confirmed / Probable risk / Unknown
- Do not jump to recommendations before inventory and architecture assessment
- Do not provide generic advice
- Use the weighted scorecard; high scores require positive evidence

Deliverables: full report + enterprise-audit-actions.md under .local/workflow-artifacts/enterprise-architecture-audit/
```

## Exit criteria

- Phases 1–6 completed in order in the written report; no early recommendation dump.  
- **Evidence contract** satisfied: §2 lists reproducible sources/commands; Confirmed claims and scorecard categories cite paths; no finding in §7 or actions file without **Evidence** paths (or explicit **Unknown**).  
- Scorecard populated with evidence and confidence; no score without justification.  
- `enterprise-audit-actions.md` exists with prioritized, repo-tied items.  
- Unknowns and human-validation items explicitly listed.
