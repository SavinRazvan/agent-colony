# `.agents/skills`

**Use ASD-STE100:** `.ai_infra/docs/operations/asd-ste100-prose.md`

Maintainer slash-command skills and workflow docs. **Canonical protocols** live under [`.cursor/skills/`](../.cursor/skills/) — Cursor discovers both roots; do not duplicate folder names here.

## Layout

Each skill: **`<skill-name>/SKILL.md`**.

## This repo

| Area | Where |
|------|--------|
| Implementation loop | `.cursor/skills/implementer-loop/`, `.cursor/agents/implementer.md` |
| **Project board SSOT** | `.cursor/skills/board-ssot/`, `.cursor/agents/board.md` |
| **Board shell first-run** | `.cursor/skills/board-shell/` (via `/board`) |
| Tests | `.cursor/skills/test-coverage/`, `.cursor/agents/test-runner.md` |
| **Maintainer PR** | **`pr-workflow/`** + `review-pr` / `prepare-pr` / `merge-pr` / `full-pr-workflow` (`PR_WORKFLOW.md` = legacy redirect) |
| **Research corpus** | `RESEARCH_WORKFLOW.md` + `.cursor/skills/research-corpus/` |
| **Enterprise audit** | `.cursor/skills/auditor-protocol/SKILL.md` + `.cursor/agents/auditor.md` |
| **Drift guard** | `.cursor/skills/drift-audit/SKILL.md` + `.cursor/agents/drift-guard.md` |
| **Audit orchestration** | `.cursor/skills/audit-orchestration/SKILL.md` |
| Deprecated redirect | `audit-alignment/` → use `auditor` |
| Scripts | `.ai_infra/scripts/pr/review.py`, `prepare.py`, `merge.py`, `finalize.py` |

Plugin sync: `.cursor/skills/` wins; maintainer skills here are **additive only** (see `sync_plugin_bundle.py`).
