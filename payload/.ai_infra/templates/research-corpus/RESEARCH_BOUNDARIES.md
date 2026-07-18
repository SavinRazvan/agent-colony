<!--
File: RESEARCH_BOUNDARIES.md
Path: .ai_infra/templates/research-corpus/RESEARCH_BOUNDARIES.md
Role: Hard-stop rules for the research corpus (copied to _research_results/ on enable).
Used By:
 - .cursor/agents/researcher.md
 - .cursor/skills/research-corpus-execution/SKILL.md
Depends On:
 - None
Notes:
 - Writes only under _research_results/; no product edits or git/PR from researcher.
-->

# Research boundaries

## Hard stop

1. **Write only** under `_research_results/` (gitignored) unless the user explicitly expands scope.
2. **Do not edit** product `src/`, `tests/`, `scripts/`, or root build files from the researcher.
3. **Do not** `git commit`, `git push`, or create PRs for research-only work.
4. **External runs require a Brief** (`sources/<slug>/BRIEF.md`) — no brief → refuse `mode: external`.
5. Pin every pack to a **path or commit SHA** in `SOURCE.md`; do not invent evidence.

## Modes

| Mode | When | Queue |
|------|------|-------|
| `external` | Brief present with `source:` | Multi-round pack under `sources/<slug>/` |
| `self` | Host corpus deepening | `DEPTH_BACKLOG.md` (optional; project-local) |

## Consumers

Other agents read `AGENT_BRIEF.md` + `INDEX.json` — not the whole foreign tree.
