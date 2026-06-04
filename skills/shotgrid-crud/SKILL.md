---
name: shotgrid-crud
description: >-
  Data layer skill — ShotGrid entity CRUD operations. Use when creating, reading,
  updating, or deleting entities. Not for search — use shotgrid-search instead.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: data
    stage: mutate
    search-hint: "create entity, read entity, update entity, delete entity, entity schema, shotgrid CRUD"
    tags: "shotgrid, mcp, crud"
    tools: tools.yaml
---

# ShotGrid CRUD

Data layer skill — ShotGrid entity CRUD operations.

## Tools

- **shotgrid-crud__create_entity** — Create a new entity (Shot, Asset, Task, Version, etc.) in ShotGrid.
- **shotgrid-crud__read_entity** — Read a single entity from ShotGrid by ID with optional field filtering.
- **shotgrid-crud__update_entity** — Update an existing entity's fields in ShotGrid.
- **shotgrid-crud__delete_entity** — Delete (retire) an entity in ShotGrid.
- **shotgrid-crud__entity_schema** — Get field schema information for an entity type.

## Groups

See `groups.yaml` for tool groupings:
- **default** — All tools.
- **read-only** — Safe read operations: read_entity, entity_schema.

## Usage

```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-crud") → register all tools
# 3. tools/call with shotgrid-crud__<tool_name>
```
