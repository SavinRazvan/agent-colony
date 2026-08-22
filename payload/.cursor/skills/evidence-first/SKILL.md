---
name: evidence-first
description: Universal facts → evidence → responsible action doctrine; shared labels; role extensions for all Agent Colony agents.
---
<!--
File: SKILL.md
Path: .cursor/skills/evidence-first/SKILL.md
Role: Procedural SSOT for evidence-first agent behavior across all kit agents.
Used By:
 - .cursor/agents/*.md
 - .cursor/rules/implementation-workflow-governance.mdc
Depends On:
 - .ai_infra/docs/operations/evidence-first.md
Notes:
 - Specialized skills link here; do not duplicate full contract blocks elsewhere.
-->

# Evidence-first

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

**Doctrine:** `.ai_infra/docs/operations/evidence-first.md`

## When (every agent)

- Before claiming **done**, **complete**, **green**, **shipped**, or **bumped everywhere**
- When the user challenges a prior answer (“I still see X”)
- Before merge prep, release tag, or “consumer can upgrade now”
- When writing `.local/workflow-artifacts/**` (PR, drift, alignment, audit)

## Universal contract

1. **Restate** the claim in testable terms.
2. **Gather** fresh evidence (paths + commands). Prefer smallest disproof first.
3. **Label** outcome: Verified | Partial | Not verified. List gaps with severity.
4. **Act** on evidence — fix, defer with owner, or correct the claim. Never hide a known gap.

**Not inspected → Unknown.** Do not infer from chat history alone.

## Evidence checklist (version / release example)

When scope includes **version bump** or **release**:

| Surface | Example check |
|---------|----------------|
| Repo SSOT | `grep` / read paths in marketplace-publish § Versioning |
| Payload mirror | `make check-plugin` |
| Git tag | `git tag -l 'v*'` · `gh release view vX.Y.Z` |
| Published artifact | GitHub **Latest** release; plugin cache `manifest.yaml` |
| Consumer | `update --check` on a real consumer app |

**Partial** is honest: e.g. repo at 0.6.5 but release still 0.6.4.

## Role extensions

| Agent | Extension |
|-------|-----------|
| **verifier** | Canonical disproof executor — try to disprove; smallest checks first; no code fixes |
| **auditor** | Confirmed / Probable + **Falsify** column — `auditor-protocol` |
| **drift-guard** | Confirmed / Probable / Unknown from `drift validate` output — `drift-audit` |
| **integrator** | Every integration claim cites path or command — `integrator-protocol` |
| **board** | Cite CLI or `gh project` JSON — `board-ssot` § Evidence contract |
| **implementer** | Slice closes with evidence step before docs; say *prepare gates green* only after run |
| **test-runner** | Cite pytest command + pass/fail counts from this run |
| **researcher** | Pack rows need source refs — `research-corpus` |

## Token-efficiency extensions

| Agent | Extension |
|-------|-----------|
| **implementer** | `project entry --digest`; `doc skill-section`; never paste green pytest/gates |
| **verifier** | Disprove full-skill reads; prefer `--summary` validators |
| **drift-guard** | DRIFT-014–016; one export per wave |
| **auditor** | CHK-TOKEN; category `token_contract` |
| **board** | Lite first-run via `board.md` § First-run lite |
| **integrator** | Lite profile docs; no gate duplication |
| **test-runner** | Pass/fail counts from this run only |
| **researcher** | Source refs in packs; not on lite profile |

Program: `.ai_infra/docs/operations/token-efficiency-program.md`.

## Handoff line (optional)

```text
Evidence: Verified | Partial | Not verified — <one-line gap or next check>
```
