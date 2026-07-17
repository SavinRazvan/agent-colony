---
name: review-pr
description: PR review phase — findings only, artifact stub + alignment when needed.
disable-model-invocation: true
---

# Review PR

**Goal:** Decide if the PR is ready for `/prepare-pr`.

## Steps

1. **Complete once:** `.local/user_settings/github.collaboration.yaml` (owner, pipelines). Validate:  
   `python -m cursor_workflow contributors validate`
2. Read PR diff and context. **Do not** land code in this phase.
3. Focus: correctness, boundary violations (project `overlays/` rules when installed), security, missing tests.
4. **Stub artifact** (owner from YAML; **Agent/s** merges trackers + `--pipeline`):  
   `python .ai_infra/scripts/pr/review.py --pr <id|url> --pipeline default`  
   Uses **`change-index.md`** + **`session-pointer.md`** for implementer/test-runner/etc., then appends PR phase agents.  
   Override: `--agents "custom | list"` or `--no-agents-from-session`.  
   Then **replace** `.local/workflow-artifacts/pr/review.md` with real findings and **READY FOR /prepare-pr** | **NEEDS WORK** | **NEEDS DISCUSSION**.
5. **Architecture-impacting:** use **`enterprise-auditor`** + `.cursor/skills/enterprise-architecture-audit/SKILL.md` (focused alignment pass); write `.local/workflow-artifacts/alignment/alignment-audit.md` + `alignment-todos.md` per `.ai_infra/docs/roadmap/alignment-audit-schema.md` (advisory only). Use `--pipeline architecture_impacting` on PR scripts when applicable.

**More context:** `.agents/skills/pr-workflow/SKILL.md`.
