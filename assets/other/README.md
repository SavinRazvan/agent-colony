# Other assets (maintainer reference)

## Research: AI auditing paper (insight transfer)

| File | Source |
|------|--------|
| [`paper-arxiv-2401.14462v1.txt`](paper-arxiv-2401.14462v1.txt) | *AI auditing: The Broken Bus on the Road to AI Accountability*, [arXiv:2401.14462](https://arxiv.org/abs/2401.14462) |

**Authors (paper):** Abeba Birhane · Briana Vecchione · Ryan Steed · Victor Ojewale · Inioluwa Deborah Raji

**Kit maintainer (this adaptation):** Savin Ionuț Răzvan (`@SavinRazvan`) — local copy + insight transfer into Agent Colony kit-process accountability (not co-authorship of the paper).

**How Agent Colony uses it:** Insight transfer into **kit-process** workflow accountability (named target, audit limits, consequence fields, independence hygiene, stages beyond evaluation). See [ADR-013](../../.ai_infra/docs/decisions/ADR-013-audit-accountability.md) and [evidence-first.md](../../.ai_infra/docs/operations/evidence-first.md) § Assurance stages.

**Not claimed:** Societal-harm, legal-compliance, fairness, or product-ML model audits. The paper’s domain is broader AI accountability; this kit adapts process ideas to Cursor multi-agent repo workflow only.

This directory is **maintainer / kit-dev reference** — not copied into the consumer plugin `payload/` by default.
