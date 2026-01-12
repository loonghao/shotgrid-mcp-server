# Tools Overview

ShotGrid MCP Server provides **40+ tools** for interacting with ShotGrid.

## Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **CRUD** | 5 | Create, Read, Update, Delete entities |
| **Batch** | 3 | Bulk operations for efficiency |
| **Media** | 2 | Thumbnail upload/download |
| **Notes** | 3 | Create, read, update notes |
| **Playlists** | 2+ | Playlist management |
| **Direct API** | 10+ | Low-level ShotGrid API access |

## CRUD Operations

| Tool | Description |
|------|-------------|
| `create_entity` | Create a new entity |
| `find_one_entity` | Find a single entity |
| `search_entities` | Search for multiple entities |
| `update_entity` | Update an existing entity |
| `delete_entity` | Delete an entity |

## Batch Operations

| Tool | Description |
|------|-------------|
| `batch_create` | Create multiple entities at once |
| `batch_update` | Update multiple entities at once |
| `batch_delete` | Delete multiple entities at once |

## Media Operations

| Tool | Description |
|------|-------------|
| `download_thumbnail` | Download entity thumbnail |
| `upload_thumbnail` | Upload entity thumbnail |

## Notes

| Tool | Description |
|------|-------------|
| `shotgrid.note.create` | Create a new note |
| `shotgrid.note.read` | Read note content |
| `shotgrid.note.update` | Update an existing note |

## Playlists

| Tool | Description |
|------|-------------|
| `create_playlist` | Create a new playlist |
| `find_playlists` | Find playlists |

## Direct API

| Tool | Description |
|------|-------------|
| `sg.find` | Direct ShotGrid find |
| `sg.create` | Direct ShotGrid create |
| `sg.update` | Direct ShotGrid update |
| `sg.batch` | Direct ShotGrid batch |
| `sg.schema` | Get entity schema |
