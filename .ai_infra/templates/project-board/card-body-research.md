<!--
  Do not edit ## headings. Fill via create-from-template CLI flags
  (--acceptance / --rollback / --notes). Brief table may be edited after create.
-->
## Acceptance

- Brief present (`source`, `question`, `lenses`); pack under `_research_results/sources/<slug>/`
- Rounds 1–6 complete (or blocked with gaps documented); `research validate --slug <slug>` PASS
- `AGENT_BRIEF.md` + `INDEX.json` ready for named consumers
- {{acceptance}}

## Rollback

- Discard pack under `_research_results/sources/<slug>/` (and cache if any); {{rollback}}

## Brief

| Field | Value |
|-------|-------|
| **source** | (TBD — `github:owner/repo@ref` or `path:/abs/or/rel`) |
| **question** | (TBD) |
| **lenses** | architecture, cli, agents, skills, tests, decisions, patterns |
| **slug** | (TBD) |
| **consumers** | implementer, integrator-mas-agent |

## Notes

<!-- agents: Notes lines are auto-timestamped by CLI -->

{{notes}}
