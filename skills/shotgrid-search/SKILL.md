---
name: shotgrid-search
description: >-
  Discovery layer skill — search and find ShotGrid entities. Use when searching, filtering, or discovering entities. Not for creating or modifying — use shotgrid-crud instead.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: data
    stage: discovery
    search-hint: "search entities, find entity, advanced search, project list, user list, date filter, shotgrid query"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Search

Discovery layer skill — search and find ShotGrid entities. Use when searching, filtering, or discovering entities. Not for creating or modifying — use shotgrid-crud instead.

## Tools

- **search_entities** — Search for entities in ShotGrid using filters and field selection.
- **find_one_entity** — Find a single entity by ID or unique field.
- **search_entities_with_related** — Search entities with related entity data in a single query.
- **sg_search_advanced** — Advanced search with time-based filters and related fields.
- **project_find_active** — Find projects active in the last N days.
- **user_find_active** — Find users active in the last N days.
- **entity_find_by_date** — Find entities within a date range.

## Usage

```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-search") → register all tools
# 3. tools/call with shotgrid-search__<tool_name>
```
