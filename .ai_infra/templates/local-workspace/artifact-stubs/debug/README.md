# Debugger campaign artifacts

**Tier 1 bucket** for forensic investigation campaigns owned by `/debugger`.

| Path | Role |
|------|------|
| `DEBUG_BOUNDARIES.md` | Write and retention boundaries for this bucket |
| `<slug>/INDEX.json` | Campaign state machine + budgets |
| `<slug>/DEBUG-BRIEF.md` | Scope, lenses, Acceptance, human oversight |
| `<slug>/vault/` | Redacted personal evidence (protected) |
| `<slug>/publish/` | Curated handoff pack for peer agents |

Create campaigns with:

```bash
python3 -m agent_colony debug init --slug <slug> --mode incident
```

See `.ai_infra/docs/operations/local-workspace-layout.md` and skills under `.cursor/skills/debug-*/`.
