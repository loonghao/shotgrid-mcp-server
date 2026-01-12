# Notes & Playlists

Manage notes and playlists in ShotGrid.

## Notes

### shotgrid.note.create

Create a new note on an entity.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | number | Yes | Project ID |
| `entity_type` | string | Yes | Linked entity type |
| `entity_id` | number | Yes | Linked entity ID |
| `subject` | string | No | Note subject |
| `content` | string | Yes | Note content |
| `addressings_to` | array | No | Users to notify |

#### Example

```
Add a note to shot 456 saying "Animation approved, ready for lighting"
```

### shotgrid.note.read

Read a note's content.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_id` | number | Yes | Note ID |

#### Example

```
Read note 789
```

### shotgrid.note.update

Update an existing note.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `note_id` | number | Yes | Note ID |
| `content` | string | No | New content |
| `subject` | string | No | New subject |

#### Example

```
Update note 789 with new content
```

## Playlists

### create_playlist

Create a new playlist for review.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | number | Yes | Project ID |
| `code` | string | Yes | Playlist name |
| `versions` | array | No | Version IDs to include |

#### Example

```
Create a playlist called "Daily Review" with versions 100, 101, 102
```

### find_playlists

Find playlists matching criteria.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `project_id` | number | No | Filter by project |
| `filters` | array | No | Additional filters |

#### Example

```
Find all playlists in project 123
```
