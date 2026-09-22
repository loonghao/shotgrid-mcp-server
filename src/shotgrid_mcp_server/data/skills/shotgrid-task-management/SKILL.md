---
name: shotgrid-task-management
description: Create, update and close ShotGrid tasks safely, including batching, and attach review notes without clobbering fields you did not mean to change.
license: MIT
metadata:
  version: 1.0.0
---

# Managing ShotGrid tasks

Read `references/status-codes.md` before setting any status — the codes are
studio-specific and the value you write must be one the entity type accepts.

## Read before you write

1. `schema_get` with entity type `Task` to learn the real field names and which
   ones are required or editable.
2. `entity_find_one` (or `search_entities`) to read the current record. Report
   the current status and assignment to the user before changing anything.
3. Confirm the status code and the assignee with the user. A task update is a
   production-side effect: it is visible to the team immediately and it is not
   something to infer from a vague request.

## Tools

| Goal | Tool |
| --- | --- |
| Read one task | `entity_find_one` |
| Read several tasks | `search_entities` |
| Update one task | `entity_update` |
| Update many tasks with one shape | `batch_entity_create` / `batch_operations` |
| Create a task | `entity_create` |
| Attach or read review feedback | `shotgrid_note_create` / `shotgrid_note_read` |

## Procedure

1. Resolve the target. Search by `project` plus `content` or `code`; do not
   guess an ID. If the search returns more than one record, ask which one.
2. Build the smallest update payload. `entity_update` writes only the fields you
   pass — omitting a field leaves it alone, so there is no need to echo the
   whole record back.
3. Set the status with a valid code from `references/status-codes.md`.
4. Apply the change with `entity_update`.
5. Re-read the task and report what changed. A successful call that changed
   nothing is still worth catching.
6. When the change carries context a teammate needs, add a note with
   `shotgrid_note_create` on the task instead of only reporting in chat.

## Batching

When the same update applies to many tasks, use one batch call rather than a
loop of `entity_update`:

- `batch_operations` for mixed create / update / delete requests.
- `batch_entity_create` for creating several records of one type.

Batches are capped at 100 operations (`MAX_BATCH_SIZE`). Split larger sets, and
check the per-item results — a batch returns one entry per operation, so a
partial failure is normal and must be read, not assumed away.

## Pitfalls

- **Never invent a status code.** An invalid code is rejected, and a valid code
  with the wrong meaning silently misinforms the team.
- **`sg_status_list` on a Task is not a free-text field.** The value must be one
  of the codes the entity type allows.
- **Date fields expect ISO 8601** (`2026-09-22` or a full timestamp). Localised
  or ambiguous formats are a common source of off-by-one-day due dates.
- **Do not guess field names.** Custom fields are named `sg_<something>` and
  differ per studio; `schema_get` is the only reliable source.
- **Retiring is not deleting.** `entity_delete` retires a record; `sg_revive`
  brings it back. Prefer a status change over a delete when the intent is "not
  needed right now".
