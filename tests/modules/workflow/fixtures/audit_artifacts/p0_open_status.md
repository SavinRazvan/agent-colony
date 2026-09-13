---
Audit-Schema: 1
Audit-Scope: kit
Named-Target: open P0 status fail fixture
Commissioned-By: maintainer
Audited-By: auditor
---

## Accountability summary

Open P0 must fail Schema-1 validation.

## Audit limits

- Fixture only

### AA-open-p0-001
- severity: P0
- status: open
- owner: platform-architecture
- due_slice: next-slice
- consequence_if_ignored: merge with unresolved critical finding
- evidence: status open on P0
- recommendation: resolve or accept_divergence before merge
