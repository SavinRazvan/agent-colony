<!--
File: session-log.template.md
Path: .ai_infra/templates/debug-campaign/session-log.template.md
Role: Append-only debugger session log template.
Used By:
 - agent_colony debug note
Depends On:
 - vault/logs/events.jsonl
-->

# Session Log

- {{created_at}} · debugger: campaign initialized
# Session log — {{slug}}

<!-- Append-only UTC lines. Do not rewrite history. -->

- {{created_at}} · debugger · campaign init
