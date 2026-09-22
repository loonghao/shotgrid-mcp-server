---
name: shotgrid-entity-search
description: Search ShotGrid (Flow Production Tracking) entities with the right tool and filter syntax, so queries stay narrow instead of pulling whole projects into context.
license: MIT
metadata:
  version: 1.0.0
---

# Searching ShotGrid entities

Read `references/filters.md` before writing any non-trivial filter — it lists
every operator the server accepts and the time-filter shapes that are easy to
get wrong.

## Pick the tool first

| Goal | Tool |
| --- | --- |
| Several entities of one type, with filters and field selection | `search_entities` |
| One type plus fields from linked entities (shots with their sequence names) | `search_entities_with_related` |
| Exactly one entity, by ID or a unique field | `entity_find_one` |
| Complex boolean logic, grouping, or aggregate summaries | `sg_search_advanced` |
| Full-text search across entity types | `sg_text_search` |
| Which fields exist on a type? | `schema_get` or `sg_schema_field_read` |
| Which entity types exist? | `sg_schema_entity_read` |

`search_entities_with_related` and `sg_search_advanced` cost one round trip
where several `search_entities` calls would cost many. Use them when the answer
needs linked data; stay with `search_entities` for a flat list.

## Procedure

1. **Confirm the entity type.** ShotGrid type names are capitalised and often
   studio-specific (`Shot`, `Asset`, `Task`, `Version`, `PublishedFile`,
   `CustomEntity01`). If the type is uncertain, call `sg_schema_entity_read`
   once rather than guessing.
2. **Confirm the fields.** Call `schema_get` for the entity type when you are
   about to filter or return a field you have not seen. A misspelled field name
   fails the whole query.
3. **Always bound the query.** Add a `project` filter, a status filter, or a
   date filter before requesting results. An unbounded `search_entities` on a
   live production can return tens of thousands of rows.
4. **Request only the fields you need** in `fields`. Entity records are wide;
   the default field set is a convenience, not a budget.
5. **Filter in ShotGrid, not in the model.** Push every condition into
   `filters`. Never fetch a broad result set and narrow it by reading.

## Example

Find in-progress shots of a project, newest update first:

```json
{
  "entity_type": "Shot",
  "filters": [
    ["project", "is", { "type": "Project", "id": 123 }],
    ["sg_status_list", "is", "ip"]
  ],
  "fields": ["code", "sg_status_list", "description"],
  "order": [{ "field_name": "updated_at", "direction": "desc" }]
}
```

## Pitfalls

- `filters` is a flat list of `[field, operator, value]` triplets. Combining
  conditions is done with the request's `filter_operator` field, **not** by
  nesting `and` / `or` arrays inside `filters`.
- Entity fields compare against a link dict: `{"type": "Project", "id": 123}`.
  Passing a bare `123` does not work.
- Status fields are `sg_status_list`; the values are short codes (`ip`, `fin`,
  `wtg`), not the display labels. Read the codes from the
  `shotgrid://schema/statuses` resource or `schema_get` before filtering.
- Time filters take an amount and a unit: `["updated_at", "in_last", 7, "DAY"]`.
