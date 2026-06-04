--- 
name: shotgrid-search
description: Search and discovery: search_entities, find_one_entity, search_with_related, search_advanced, project_find_active, user_find_active, entity_find_by_date
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: default
    search-hint: "shotgrid, entity, shotgrid-search"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Search
Search and discovery: search_entities, find_one_entity, search_with_related, search_advanced, project_find_active, user_find_active, entity_find_by_date

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
