---
name: shotgrid-crud
description: Core CRUD operations: create_entity, read_entity, update_entity, delete_entity, entity_schema
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: default
    search-hint: "shotgrid, entity, shotgrid-crud"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid CRUD
Core CRUD operations: create_entity, read_entity, update_entity, delete_entity, entity_schema

## Tools
- **create_entity** — Create a new entity (Shot, Asset, Task, Version, etc.) in ShotGrid.
- **read_entity** — Read a single entity from ShotGrid by ID with optional field filtering.
- **update_entity** — Update an existing entity's fields in ShotGrid.
- **delete_entity** — Delete (retire) an entity in ShotGrid.
- **entity_schema** — Get field schema information for an entity type.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-crud") → register all tools
# 3. tools/call with shotgrid-crud__<tool_name>
```
