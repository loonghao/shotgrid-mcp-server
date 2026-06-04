---
name: shotgrid-media
description: Thumbnail operations: download_thumbnail, upload_thumbnail, batch_download
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: optional
    search-hint: "shotgrid, entity, shotgrid-media"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Media
Thumbnail operations: download_thumbnail, upload_thumbnail, batch_download

## Tools
- **download_thumbnail** — Download a thumbnail from ShotGrid for a given entity.
- **upload_thumbnail** — Upload a thumbnail image to ShotGrid for a given entity.
- **batch_download_thumbnails** — Download multiple thumbnails in batch for a list of entities.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-media") → register all tools
# 3. tools/call with shotgrid-media__<tool_name>
```
