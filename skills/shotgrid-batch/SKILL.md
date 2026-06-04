---
name: shotgrid-batch
description: >-
  Data layer skill — batch CRUD operations for ShotGrid. Use when creating, updating, or deleting many entities at once.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: data
    stage: mutate
    search-hint: "batch create, batch update, batch delete, bulk operations, shotgrid batch"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Batch

Data layer skill — batch CRUD operations for ShotGrid. Use when creating, updating, or deleting many entities at once.

## Tools

- **batch_create** — Create multiple entities of the same type in a single batch operation.
- **batch_update** — Update multiple entities of the same type in a single batch operation.
- **batch_delete** — Delete (retire) multiple entities in a single batch operation.

## Usage

```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-batch") → register all tools
# 3. tools/call with shotgrid-batch__<tool_name>
```
