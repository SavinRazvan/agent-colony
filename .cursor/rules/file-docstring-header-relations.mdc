---
description: Top-of-file module header with File/Path/Role/relations
alwaysApply: true
---

# File header (docstring / comment block)

- New sources must start with a module header; keep it accurate when responsibilities change.
- Required fields: `File:`, `Path:` (repo-relative), `Role:`, `Used By:`, `Depends On:`, `Notes:` (optional). Factual only; unknown relations → `TBD`.

## Python example

```python
"""
File: example_module.py
Path: src/example/example_module.py
Role: Short description of responsibilities.
Used By:
  - src/core/orchestrator.py
Depends On:
  - src/schemas/events.py
Notes:
  - Keep deterministic behavior for retry paths.
"""
```

- Non-Python: same fields in a top comment block using that language’s comment syntax.
