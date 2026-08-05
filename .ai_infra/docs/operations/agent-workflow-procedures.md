<!--
File: agent-workflow-procedures.md
Path: .ai_infra/docs/operations/agent-workflow-procedures.md
Role: Canonical procedures for audits and workflow deduplication.
Used By:
 - .ai_infra/docs/operations/workflow-complete.md
Depends On:
 - .cursor/agents/auditor.md
 - .ai_infra/scripts/pr/prepare.py
Notes:
 - Do not copy gate command lists; reference prepare.py `resolve_gates()` (`GATES` = alias).
-->

# Agent workflow procedures (canonical)

## 1) Architecture-impacting advisory audit (alignment artifacts)

**When:** Module boundaries, workflow policy, test layout, or maintainer calls for alignment before prepare/merge. **Not** consumer day-0 onboarding — complete board shell (`/board` + `board-bootstrap --check`) first; use this for architecture-impacting / pre-merge work.

**Canonical agent:** **`auditor`** with **`.cursor/skills/auditor-protocol/SKILL.md`**.

**Procedure (advisory-only):**

1. Run a **focused alignment pass** unless a full enterprise audit is in scope.
2. Use **`.ai_infra/docs/roadmap/alignment-audit-schema.md`** for severity and finding shape.
3. Write outputs to `.local/workflow-artifacts/alignment/alignment-audit.md` and `alignment-todos.md`.
4. Block **`/prepare-pr`** on open **P0** unless accepted with rationale.

**Rule of law:** `.cursor/rules/advisory-audit-alignment-enforcement.mdc` + **`python .ai_infra/scripts/pr/merge.py --arch-impacting`**.

---

## 2) Maintainer PR workflow (phases)

**Order (staged):** `review-pr` → `prepare-pr` → `merge-pr`.

**Order (full):** `review-pr` → `prepare-pr` → `merge-pr` → **`finalize.py`** (via `full-pr-workflow`).

**Canonical narrative:** **`.agents/skills/pr-workflow/SKILL.md`** (staged; redirect stub: `PR_WORKFLOW.md`) + **`full-pr-workflow`** (full cleanup).
**Executable stubs:** **`.ai_infra/scripts/pr/`** (`prepare.py`, `merge.py`, `review.py`, `finalize.py`, `verify_publish.py`)

---

## 3) Merge / prepare gate commands — single source of truth

**Authoritative list:** `.ai_infra/scripts/pr/prepare.py` → **`resolve_gates()`** (kit-dev auto-appends drift + doc facts when `IMPLEMENTATION-STATUS.md` exists). **`GATES`** is the universal 2-gate back-compat alias only — do not cite it as the SSOT. Do not duplicate gate commands in rules, skills, or chat.

**Optional:** `python .ai_infra/scripts/architecture/check_governance_consistency.py` when changing governance, workflows, `.cursor/`, `.agents/`, or tracked policy docs.

**Project overlays:** extra gates belong in overlay packs — wire into `prepare.py` `resolve_gates()` at install time.

---

## 3b) Commit message provenance (git, not PR artifacts)

**Git commits** use **`.cursor/rules/commit-trailer-format.mdc`**: required `Author:` + `GitHub-User:`; optional `Assisted-by:` when disclosure applies. No **`Made-with:`**.

**PR phase markdown** uses `Action-By` / `GitHub-User` / `Agent/s` per **`.agents/skills/pr-workflow/SKILL.md`**.

When trailer policy changes, sync: **`AGENTS.md`**, **`README.md`**, **`.cursor/rules/pr-workflow-enforcement.mdc`**, **`.cursor/agents/implementer.md`**, **`.agents/skills/pr-workflow/SKILL.md`**, **`PR_WORKFLOW.md`** (redirect), **`workflow-source-owners.md`**, **`rules-overlap-matrix.md`**, and this §3b.

---

## 4) Anti-duplication rule

When **`resolve_gates()`** / **`GATES`** in `prepare.py` change, update in the **same slice**:

| Surface | Location |
|--------|-----------|
| Always-applied rule | `.cursor/rules/pr-workflow-enforcement.mdc` |
| Onboarding | `README.md`, `AGENTS.md` |
| Checklist | `.ai_infra/docs/operations/workflow-complete.md` |
| Canvas / plan artifacts | `.cursor/skills/canvas-artifacts/SKILL.md` (ADR-010) |
| Maintainer skills | `.agents/skills/pr-workflow/SKILL.md`, `prepare-pr/SKILL.md`, `review-pr/SKILL.md`, `merge-pr/SKILL.md`, `full-pr-workflow/SKILL.md` |
| Post-merge cleanup | `.ai_infra/scripts/pr/finalize.py` (via `full-pr-workflow`) |

Do not paste full gate blocks into **`updates-log.md`** — log *gate list synced per §4*.

---

## 5) After documentation refreshes

1. Run **documentation-maintenance-checklist.md** as applicable.
2. Append one line to **`.local/index-and-planning/history/updates-log.md`**.
