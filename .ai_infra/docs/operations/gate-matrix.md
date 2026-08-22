<!--
File: gate-matrix.md
Path: .ai_infra/docs/operations/gate-matrix.md
Role: Explains prepare resolve_gates() vs kit-dev gates vs consumer verify.
Used By:
 - consumer-quickstart.md
 - auditor alignment
Depends On:
 - .ai_infra/scripts/pr/prepare.py
 - .ai_infra/install/agent_colony/cli.py
-->

# Gate matrix

**Use ASD-STE100:** [asd-ste100-prose.md](asd-ste100-prose.md)


> **Consumer installs:** use `agent-colony install --verify` or `python .ai_infra/scripts/install/scaffold.py --target … --verify` (4 steps). Do **not** use a `agent_colony scaffold` subcommand — it does not exist. `agent-colony gates` is a separate **5**-step maintainer hygiene command (adds doc facts). Sections mentioning `make gates`, `make verify-all`, `kit-quality.yml`, or `IMPLEMENTATION-STATUS.md` apply to **kit repository maintainers** only.

Three gate surfaces exist by design (Pattern A).

| Surface | When | Steps | Source of truth |
|---------|------|-------|-----------------|
| **`prepare.py` `resolve_gates()`** | PR merge prep | **2** universal (testing artifacts + pytest); **5** on kit-dev (auto-appends drift + doc facts + `sync_plugin_bundle.py --check`) | `.ai_infra/scripts/pr/prepare.py` `resolve_gates()` (`GATES` = 2-gate alias) |
| **`agent-colony gates`** | Kit dev / maintainer hygiene | **5**: testing artifacts + pytest + governance + debrand + doc facts | `.ai_infra/install/agent_colony/cli.py` `cmd_gates` |
| **`make doc-validate`** | After doc/agent/rule changes | DOC-001…008 canonical fact checks | `.ai_infra/scripts/architecture/check_doc_facts.py` |
| **`make verify-all`** | Pre-audit / release readiness | 7 (+ optional ci-seed): sync-plugin → gates → drift → integrate → check-plugin → health → contributors | `.ai_infra/scripts/architecture/verify_all.py` |
| **Install / scaffold `--verify`** | Post-install smoke on consumer | **4**: testing artifacts + pytest + governance + debrand (no doc facts) | `agent-colony install --verify` or `.ai_infra/scripts/install/scaffold.py` `_run_verify` — not interchangeable with `agent-colony gates` |
| **`make drift-validate`** | Slice closure / maintainer hygiene | Operational drift (DRIFT-001…010 + 004b + **014–016** token contract on kit-dev; consumer profile subset). See [token-efficiency-enforcement.md](token-efficiency-enforcement.md) | `.ai_infra/scripts/workflow/check_drift.py` |
| **Consumer drift** | Post-install verify on app projects | `drift validate --profile consumer` — DRIFT-005 (skip when `IMPLEMENTATION-STATUS.md` absent) + DRIFT-008 | [consumer-quickstart.md](consumer-quickstart.md#drift-on-consumer-apps) |
| **`kit-quality.yml` (CI)** | Push/PR on kit repo | seed → gates → drift → integrate → check-plugin → health → contributors → install-dry-run (strict `check-plugin` with **no** prior sync) | `.github/workflows/kit-quality.yml` |

**Rule:** Agents preparing a PR run **`prepare.py`** (or MCP `workflow_run_prepare`). Kit-dev `prepare.py` runs drift + doc facts + strict `check-plugin` automatically; consumers keep universal gates unless extended at install. Maintainers validating the kit repo may also run **`make gates`**, **`make drift-validate`**, or **`agent-colony gates`**. GitHub Actions runs **`seed_kit_workspace.py`** first because `.local/` is gitignored. Note: **`make verify-all`** syncs the plugin bundle before `--check` (working-tree refresh); CI and kit-dev prepare use `--check` alone so committed drift fails.

Optional product gates: append once to consumer `prepare.py` at install; document in overlay README.
