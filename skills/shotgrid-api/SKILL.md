---
name: shotgrid-api
description: Direct ShotGrid API access: sg_find, sg_find_one, sg_create, sg_update, sg_delete, sg_batch, sg_schema_entity_read, sg_schema_field_read, sg_text_search, sg_revive, sg_upload, sg_download_attachment, sg_summarize, etc.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: optional
    search-hint: "shotgrid, entity, shotgrid-api"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid API (Low-Level)
Direct ShotGrid API access: sg_find, sg_find_one, sg_create, sg_update, sg_delete, sg_batch, sg_schema_entity_read, sg_schema_field_read, sg_text_search, sg_revive, sg_upload, sg_download_attachment, sg_summarize, etc.

## Tools
- **sg_find** — Low-level ShotGrid find operation. Returns raw results with filtering, ordering, and pagination.
- **sg_find_one** — Low-level ShotGrid find_one operation. Returns a single entity matching filters.
- **sg_create** — Low-level ShotGrid create operation. Creates a new entity with provided data.
- **sg_update** — Low-level ShotGrid update operation. Updates an existing entity's fields.
- **sg_delete** — Low-level ShotGrid delete operation. Retires an entity by ID.
- **sg_batch** — Low-level ShotGrid batch operation. Executes multiple requests in a single API call.
- **sg_schema_entity_read** — Read entity schema. Returns all available entity types.
- **sg_schema_field_read** — Read field schema for an entity type. Optionally filter by specific field.
- **sg_text_search** — Full-text search across entities. Searches by text and entity types.
- **sg_revive** — Revive a retired entity by type and ID.
- **sg_upload** — Upload a file to ShotGrid and attach to an entity field.
- **sg_download_attachment** — Download an attachment from ShotGrid by attachment ID.
- **sg_summarize** — Summarize entities matching filters. Returns counts grouped by a field.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-api") → register all tools
# 3. tools/call with shotgrid-api__<tool_name>
```
