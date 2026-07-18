<!--
File: README.md
Path: .ai_infra/templates/research-corpus/README.md
Role: Index for research corpus pack templates and CLI enablement.
Used By:
 - .ai_infra/install/cursor_workflow/research_cli.py
 - .cursor/skills/research-corpus-execution/SKILL.md
 - .cursor/agents/researcher.md
Depends On:
 - INDEX.schema.json
Notes:
 - Corpus output lives under gitignored `_research_results/`; these files are the shipped scaffold.
-->

# Research corpus templates

Copy into `_research_results/` via:

```bash
python3 -m cursor_workflow research init --slug <slug> [--brief path/to/brief.md]
python3 -m cursor_workflow research fetch --slug <slug> --source path:/abs/or/rel
# or: --source github:owner/repo[@ref]
python3 -m cursor_workflow research validate --slug <slug>
```

| File | Role |
|------|------|
| `RESEARCH_BOUNDARIES.md` | Hard stop + enable rules (copied to corpus root on first init) |
| `BRIEF.template.md` | Intake contract |
| `SOURCE.template.md` | Pin: url/path, SHA/ref, fetched_at |
| `MAP.template.md` | Tree / entrypoints |
| `CURATED.template.md` | Verified evidence rows |
| `AGENT_BRIEF.template.md` | Handoff for implementer / integrator |
| `findings/_LENS.template.md` | Per-lens finding shell |
| `INDEX.schema.json` | Machine index schema |

Pack layout: `_research_results/sources/<slug>/` (+ optional `cache/<slug>/` for clones).
