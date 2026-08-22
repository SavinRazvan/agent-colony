# Workflow drift scripts

Operational workflow drift detection per [ADR-007](../../docs/decisions/ADR-007-workflow-drift-guard.md).

## Commands

```bash
python .ai_infra/scripts/workflow/check_drift.py --directory .
python -m agent_colony drift validate --directory .
python -m agent_colony drift validate --profile kit-dev --summary
python -m agent_colony drift validate --profile consumer --summary
make drift-validate
```

## Checks

See `drift_checks.py` — DRIFT-001…016 + 004b on kit-dev (004b/009–010 when `project_ssot.sync_policy: board_only`).

| Profile | Checks (summary) |
|---------|------------------|
| **kit-dev** | Full set including DRIFT-014 (token anchors), DRIFT-015 (plugin rule dup WARN), DRIFT-016 (thin-index parity) |
| **consumer** | DRIFT-005 + DRIFT-008 (+ DRIFT-014/016 when token program files present) |
| **consumer-board** | Consumer set + board-specific checks when SSOT on |

Token-efficiency cadence: [token-efficiency-enforcement.md](../../docs/operations/token-efficiency-enforcement.md).

**DRIFT-005 on consumer:** When `IMPLEMENTATION-STATUS.md` is absent (normal on plugin installs), the check **PASSes (skip)** — not a consumer failure. A FAIL on missing file indicates an older kit payload (false positive; see `consumer-quickstart.md`).

Exit code 1 on P0 failure only.
