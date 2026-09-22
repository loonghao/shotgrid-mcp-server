---
name: shotgrid-schema-discovery
description: Discover the ShotGrid schema (entity types, fields, status codes) from MCP resources instead of tool calls, so field names are verified before any read or write.
license: MIT
metadata:
  version: 1.0.0
---

# Discovering the ShotGrid schema

Read `references/entity-types.md` for the common entity types and the fields
worth asking for first.

## Prefer resources over tools

This server exposes the schema as MCP resources alongside its tools. Resources
are context loaded once, not a round trip per question:

| Resource | Contents |
| --- | --- |
| `shotgrid://schema/entities` | Every entity type, as `sg.schema_read()` returns it |
| `shotgrid://schema/statuses` | `status_list` fields of every entity type |
| `shotgrid://schema/statuses/{entity_type}` | `status_list` fields of one entity type |

Use the matching tool when you need a narrower or live answer:

| Goal | Tool |
| --- | --- |
| Fields of one entity type | `schema_get` |
| All entity types | `sg_schema_entity_read` |
| One field's schema | `sg_schema_field_read` |

## Procedure

1. **Start with `shotgrid://schema/statuses/{entity_type}`** when the task
   involves status. It returns the valid codes and their display labels in one
   read, which is exactly what an update needs.
2. **Use `schema_get` for field-level questions** on a single entity type —
   data types, whether a field is required, whether it is editable.
3. **Verify every field name before writing.** Custom fields are named
   `sg_<something>` and are studio-specific. A field that exists in one project
   may not exist in another.
4. **Cache what you learned for the session.** Schema rarely changes inside one
   task; do not re-read it between steps.

## Pitfalls

- **Do not assume a field exists** because it exists on a similar entity type.
  `sg_status_list` is common but not universal.
- **Entity type names are case-sensitive** and capitalised (`Shot`, not `shot`).
- **Custom entities are `CustomEntity01` … `CustomEntityNN`**; their human
  names live in the schema, not in the type name.
- **A schema read is not a data read.** The schema tells you what a field is
  called, never what it currently holds.
