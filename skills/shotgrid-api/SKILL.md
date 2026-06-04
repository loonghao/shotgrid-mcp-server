---
name: shotgrid-api
description: >-
  Data layer skill — low-level ShotGrid API access. Use when you need direct ShotGrid API operations beyond the higher-level CRUD/search tools.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: data
    stage: discovery
    search-hint: "sg find, sg create, sg update, sg delete, sg batch, schema read, text search, revive, upload, download attachment, summarize, shotgrid API"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid API (Data Layer)

Direct ShotGrid API access — low-level operations for sg_find, sg_find_one, sg_create, sg_update, sg_delete, sg_batch, sg_schema_entity_read, sg_schema_field_read, sg_text_search, sg_revive, sg_upload, sg_download_attachment, and sg_summarize.

## Tools

- **shotgrid-api__sg_find** — Low-level ShotGrid find operation. Returns raw results with filtering, ordering, and pagination.
- **shotgrid-api__sg_find_one** — Low-level ShotGrid find_one operation. Returns a single entity matching filters.
- **shotgrid-api__sg_create** — Low-level ShotGrid create operation. Creates a new entity with provided data.
- **shotgrid-api__sg_update** — Low-level ShotGrid update operation. Updates an existing entity's fields.
- **shotgrid-api__sg_delete** — Low-level ShotGrid delete operation. Retires an entity by ID.
- **shotgrid-api__sg_batch** — Low-level ShotGrid batch operation. Executes multiple requests in a single API call.
- **shotgrid-api__sg_schema_entity_read** — Read entity schema. Returns all available entity types.
- **shotgrid-api__sg_schema_field_read** — Read field schema for an entity type. Optionally filter by specific field.
- **shotgrid-api__sg_text_search** — Full-text search across entities. Searches by text and entity types.
- **shotgrid-api__sg_revive** — Revive a retired entity by type and ID.
- **shotgrid-api__sg_upload** — Upload a file to ShotGrid and attach to an entity field.
- **shotgrid-api__sg_download_attachment** — Download an attachment from ShotGrid by attachment ID.
- **shotgrid-api__sg_summarize** — Summarize entities matching filters. Returns counts grouped by a field.

## Usage

```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-api") → register all tools
# 3. tools/call with shotgrid-api__<tool_name>
```
