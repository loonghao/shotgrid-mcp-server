---
name: shotgrid-playlists
description: Playlist management: create_playlist, find_playlists, add_versions_to_playlist, remove_versions_from_playlist
license: MIT
metadata:
  dcc-mcp:
    dcc: shotgrid
    version: "1.0.0"
    layer: optional
    search-hint: "shotgrid, entity, shotgrid-playlists"
    tags: "shotgrid, mcp"
    tools: tools.yaml
---

# ShotGrid Playlists
Playlist management: create_playlist, find_playlists, add_versions_to_playlist, remove_versions_from_playlist

## Tools
- **create_playlist** — Create a playlist for version review in ShotGrid.
- **find_playlists** — Search for playlists in ShotGrid with optional project and name filters.
- **add_versions_to_playlist** — Add versions to an existing playlist.
- **remove_versions_from_playlist** — Remove versions from a playlist.

## Usage
```python
# Tools are loaded via dcc-gateway:
# 1. search_skills → find shotgrid-* skills
# 2. load_skill("shotgrid-playlists") → register all tools
# 3. tools/call with shotgrid-playlists__<tool_name>
```
