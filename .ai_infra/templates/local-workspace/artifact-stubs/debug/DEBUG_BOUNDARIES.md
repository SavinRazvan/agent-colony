<!--
File: DEBUG_BOUNDARIES.md
Path: .ai_infra/templates/local-workspace/artifact-stubs/debug/DEBUG_BOUNDARIES.md
Role: Hard-stop and retention rules for debugger campaigns under workflow-artifacts/debug/.
Used By:
 - .cursor/agents/debugger.md
 - .ai_infra/install/agent_colony/debug_cli.py
Depends On:
 - .cursor/rules/local-artifact-protection.mdc
Notes:
 - Scaffold copies this once to .local/workflow-artifacts/debug/DEBUG_BOUNDARIES.md.
-->

# Debug campaign boundaries

## Hard stop

1. Write campaign evidence only under `.local/workflow-artifacts/debug/<slug>/`.
2. Vault content is redacted evidence. Never store intentional secrets.
3. Do not delete, overwrite, unlock-repair, archive, or purge `vault/**` without listing targets and receiving explicit human approval.
4. Capture is not a sandbox. It runs with caller privileges (`shell=False`, bounded time/output).
5. Behavioral product fixes, API changes, and exception-flow changes belong on implementer child cards — not inside the forensic debug card.
6. `.gitignore` keeps `.local/` out of git. That is not a confidentiality boundary.

## Retention

- Closed campaigns are immutable. A later investigation creates a new campaign with `supersedes`.
- Enforce run, campaign, and debug-root size budgets. Refuse init/capture when budgets or free-space floors fail.
- No automatic deletion.
