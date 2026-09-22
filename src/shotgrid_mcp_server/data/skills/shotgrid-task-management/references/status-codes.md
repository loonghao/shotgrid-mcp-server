# Status codes

`sg_status_list` holds a short **code**, not the label the ShotGrid UI shows.
Writing a value the field does not accept fails the update, so resolve the code
before you write it.

## The default ShotGrid codes

| Code | Typical label | Meaning |
| --- | --- | --- |
| `wtg` | Waiting to Start | Not begun, ready to be picked up |
| `rdy` | Ready to Start | Queued for work |
| `ip` | In Progress | Actively being worked on |
| `rev` | Pending Review | Waiting on supervisor or client review |
| `cmpt` | Client Approved | Approved by the client |
| `fin` | Final | Approved internally, closed out |
| `omt` | Omitted | Cancelled, no longer needed |
| `hld` | On Hold | Blocked or paused |

## Always confirm against the live schema

Studios rename, add and remove codes, and the set differs between entity types
(`Task`, `Asset`, `Shot`, `Version` each carry their own). Treat the table above
as a starting point only.

Resolve the codes for the entity type you are about to write:

- The `shotgrid://schema/statuses/{entity_type}` MCP resource, which lists every
  `status_list` field of one entity type with its valid values and display
  labels.
- The `shotgrid://schema/statuses` resource for all entity types at once.
- `schema_get` with the entity type, when you already have the schema in hand.

## Other fields worth confirming

- **`task_assignees`** holds a list of `HumanUser` links — pass a list, not a
  single link.
- **`start_date` / `due_date`** are dates, not datetimes, and expect ISO 8601.
- **`duration`** is in working days, not hours.
