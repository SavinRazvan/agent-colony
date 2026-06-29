<!--
File: gate-matrix.md
Path: .ai_infra/docs/operations/gate-matrix.md
Role: Explains prepare GATES vs kit-dev gates vs consumer verify.
Used By:
 - consumer-quickstart.md
 - enterprise-auditor alignment
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/install/cursor_workflow/cli.py
-->

# Gate matrix

Three gate surfaces exist by design (Pattern A).

| Surface | When | Steps | Source of truth |
|---------|------|-------|-----------------|
| **`prepare.py` GATES** | PR merge prep on consumer project | 2: testing artifacts + pytest | `.ai_infra/scripts/pr/prepare.py` |
| **`cursor-workflow gates`** | Kit dev / maintainer hygiene | 4: above + governance + debrand | `.ai_infra/install/cursor_workflow/cli.py` |
| **`scaffold --verify`** | Post-install smoke on consumer | Same 4 as kit gates | `.ai_infra/scripts/install/scaffold.py` `_run_verify` |
| **`make drift-validate`** | Slice closure / maintainer hygiene | Operational drift (DRIFT-001…008) | `.ai_infra/scripts/workflow/check_drift.py` |

**Rule:** Agents preparing a PR run **`prepare.py`** (or MCP `workflow_run_prepare`). Maintainers validating the kit repo run **`make gates`**, **`make drift-validate`**, or **`cursor-workflow gates`**.

Optional product gates: append once to consumer `prepare.py` at install; document in overlay README.
