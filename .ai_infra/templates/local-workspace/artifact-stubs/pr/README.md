# PR workflow artifacts

**Tier 2 runtime** files for the maintainer PR lane (`review-pr` → `prepare-pr` → `merge-pr`).

| File | Writer |
|------|--------|
| `review.md` | `.ai_infra/scripts/pr/review.py` |
| `prep.md` | `.ai_infra/scripts/pr/prepare.py` |
| `merge.md` | `.ai_infra/scripts/pr/merge.py` |

Created on first script run. See `.ai_infra/docs/operations/local-workspace-layout.md`.
