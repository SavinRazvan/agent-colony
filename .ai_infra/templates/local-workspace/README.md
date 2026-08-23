# Local workspace templates

**File:** README.md  
**Path:** `.ai_infra/templates/local-workspace/README.md`  
**Role:** Documents exemplar trackers, artifact stubs, and CI fixtures copied into `.local/` at scaffold/activate.

## Layout

| Path | Purpose |
|------|---------|
| `exemplars/` | Tracker and audit markdown seeded into `.local/index-and-planning/` when missing |
| `artifact-stubs/` | README stubs for `.local/workflow-artifacts/*` buckets |
| `ci/` | Kit-dev CI fixtures only — **not** shipped to consumer installs |

Scaffold copies exemplars into `.local/index-and-planning/current/` (and history/audits as needed), and README stubs into `workflow-artifacts/*`. Prefer **GitHub Project board (ADR-008)** and **Cursor Open Canvas** for live status and visualization. Offline markdown trackers remain under `.local/index-and-planning/`.

Deprecated browser dashboard files were removed in kit 0.7.3. Activate/update heal deletes leftover dashboard folders if present.
