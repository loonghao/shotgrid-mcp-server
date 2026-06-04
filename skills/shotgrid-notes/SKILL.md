---
name: shotgrid-notes
description: >-
  Domain skill — ShotGrid note operations. Use when creating, reading, or updating notes on entities.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: domain
    stage: mutate
    search-hint: "create note, read notes, update note, shotgrid comment, feedback"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Notes
Domain skill — ShotGrid note operations. Use when creating, reading, or updating notes on entities.

## Tools
- **create_note** — Create a note on a ShotGrid entity with subject and content.
- **read_notes** — Read notes from a ShotGrid entity with optional field filtering.
- **update_note** — Update an existing note's fields (subject, content, etc.) in ShotGrid.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-notes") → register all tools
# 3. tools/call with shotgrid-notes__<tool_name>
```
