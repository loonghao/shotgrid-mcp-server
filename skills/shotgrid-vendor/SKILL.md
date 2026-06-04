---
name: shotgrid-vendor
description: >-
  Pipeline skill — ShotGrid vendor management. Use when finding vendor users, versions, or creating vendor review playlists.
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: domain
    stage: pipeline
    search-hint: "vendor users, vendor versions, vendor playlist, external review, shotgrid vendor"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Vendor
Pipeline skill for managing vendor users, versions, and review playlists in ShotGrid.

## Tools
- **find_vendor_users** — Find vendor (external) users by name or email filter.
- **find_vendor_versions** — Find versions submitted by vendor users, filtered by project, status, and date range.
- **create_vendor_playlist** — Create a playlist for vendor review with specified versions and vendor user access.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-vendor") → register all tools
# 3. tools/call with shotgrid-vendor__<tool_name>
```
