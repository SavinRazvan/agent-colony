# Alignment audit artifacts

**Tier 2 runtime** outputs for architecture-impacting PRs (focused alignment pass).

| File | Writer |
|------|--------|
| `alignment-audit.md` | `auditor` agent |
| `alignment-todos.md` | `auditor` agent |

These stubs are **not** stamped with live `Audit-Schema: 1` (commented skeleton only) so leftover copies do not fail ordinary prepare. Real passes must add Schema-1 frontmatter + Accountability summary + Audit limits.

Schema: `.ai_infra/docs/roadmap/alignment-audit-schema.md`. See `.ai_infra/docs/operations/local-workspace-layout.md`.
