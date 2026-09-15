<!--
File: logging-and-errors.md
Path: .ai_infra/docs/operations/logging-and-errors.md
Role: Canonical logging and error-handling contract for kit scripts and consumer projects.
Used By:
 - Implementer orientation
 - .cursor/skills/debug-observability-standard/SKILL.md
 - .cursor/skills/debug-error-surface/SKILL.md
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .cursor/rules/local-artifact-protection.mdc
Notes:
 - Framework-neutral SSOT. Preserve the project's selected logging implementation.
 - Debugger may apply Acceptance-authorized semantics-preserving standardization only.
-->

# Logging and error handling (Agent Colony)

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)

This document is the **canonical logging and error-handling contract**. Skills enforce it. Do not invent a competing observability SSOT.

## Kit scripts

- PR workflow scripts (`prepare.py`, `merge.py`, etc.) return non-zero exit codes on failure.
- Capture stderr from gate subprocesses; do not swallow failures in agent handoffs.
- Use `python .ai_infra/scripts/architecture/check_governance_consistency.py` after policy edits.

## Consumer projects

- Add structured logging in **your application code** — not in universal agent prose.
- Protect secrets: `.env` per `local-artifact-protection.mdc`.
- For product overlays, follow overlay-specific observability docs when installed under `overlays/docs/`.
- Preserve the project's selected logger/framework. Do not inject a new logging dependency or global configuration without an implementation card.

## Structured event contract (framework-neutral)

Prefer events with:

| Field | Purpose |
|-------|---------|
| `timestamp` | UTC ISO-8601 |
| `level` | `debug` \| `info` \| `warning` \| `error` \| `critical` |
| `event` | Stable machine name (`module.action.result`) |
| `message` | Human-readable summary |
| `correlation_id` / `trace_id` | Cross-boundary request or campaign correlation |
| `module` / `component` | Owning package or service |
| `duration_ms` | Optional timing for lifecycle events |

Lifecycle and boundary events: start, success, failure, timeout, retry, cleanup. Prefer structured fields over free-form dumps.

## Log vs raise

- Log operational facts that operators need without failing the call.
- Raise (or return a typed error) when the caller must decide or the contract is broken.
- Do not swallow exceptions at module edges. Catch, enrich, rethrow or translate once at the boundary.
- Chain exceptions (`raise ... from`) when translating.
- Retries and timeouts need budget, backoff, and a terminal failure path.
- Cleanup paths must run on success and failure when resources were acquired.

## Secrets

- Never log tokens, passwords, cookies, private keys, authorization headers, or secret-valued environment values.
- Redact before persistence. Gitignore is not a confidentiality boundary.

## Standards gaps (`SG-*`)

- Gaps against this contract become `SG-*` findings for debugger campaigns.
- Mechanical, semantics-preserving fixes may land only when Acceptance names them in `standardize` mode.
- Behavior-changing error handling, public API changes, and exception-flow changes route to implementer child cards.
- Proposed new contract rules are `queued_with_owner` for integrator/implementer; the debugger does not rewrite this document from inside a campaign.

## Measurement (performance / memory)

When claims involve performance, leaks, or concurrency:

- Record baseline and treatment.
- Record environment, warm-up, sample count, uncertainty, and regression threshold.
- Prefer deterministic controls; label confidence honestly.

## Language overlays

Python and TypeScript examples are overlays, not universal mandates. Prefer the project's existing logger APIs (`logging`, `structlog`, OpenTelemetry, etc.).

## Agent handoffs

- Report *prepare gates green* or paste **failing command + stderr** only.
- Do not duplicate full gate output in `updates-log.md`.
- Debugger campaigns cite `vault_ref` and publish Signals — do not paste full vault logs into chat.
