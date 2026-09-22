# Common entity types

Resolve the full list for the site with `sg_schema_entity_read` or the
`shotgrid://schema/entities` resource — studios add custom entities and rename
fields. The table below covers the types most tasks touch.

| Entity type | What it is | Fields worth asking for first |
| --- | --- | --- |
| `Project` | A show or production | `code`, `name`, `sg_status_list` |
| `Sequence` | A group of shots | `code`, `project`, `sg_status_list` |
| `Shot` | One shot inside a sequence | `code`, `sg_sequence`, `sg_cut_in`, `sg_cut_out`, `sg_status_list` |
| `Asset` | A character, prop or environment | `code`, `sg_asset_type`, `sg_status_list` |
| `Task` | A unit of assigned work | `content`, `entity`, `task_assignees`, `sg_status_list`, `start_date`, `due_date` |
| `Version` | A submitted iteration of a task | `code`, `entity`, `sg_task`, `sg_status_list`, `sg_uploaded_movie` |
| `PublishedFile` | A published file | `code`, `path`, `entity`, `version_number` |
| `Note` | Review feedback | `content`, `subject`, `note_links`, `sg_status_list` |
| `HumanUser` | A person | `name`, `login`, `email` |
| `CustomEntity01` … `CustomEntityNN` | Studio-defined entities | Studio-defined; read the schema |

## Fields that exist on almost every entity

- `id` — integer primary key.
- `type` — the entity type name, present in every link dict.
- `code` — the human-readable identifier.
- `project` — link to the owning `Project`. Filter on it to bound a query.
- `created_at` / `updated_at` — datetimes, usable with relative time filters.
- `sg_status_list` — the pipeline status code, when the type has a status.

## Reading a link field

A link field returns a dict, not an ID:

```json
{ "type": "Project", "id": 123, "name": "Feature Film" }
```

To see more than `id` and `type`, name the sub-field in `fields`, e.g.
`project.Project.name`.

## Field naming

- Built-in fields are lowercase with underscores (`created_at`, `description`).
- Custom fields are prefixed `sg_` (`sg_status_list`, `sg_asset_type`).
- The prefix is the only reliable signal: never infer a field name from another
  studio's convention.
