# Filter reference

Every condition is a `[field, operator, value]` triplet. Conditions are combined
with the request's `filter_operator` field, which is separate from `filters`:

```json
{
  "filters": [
    ["sg_status_list", "is", "ip"],
    ["project", "is", { "type": "Project", "id": 123 }]
  ],
  "filter_operator": "all"
}
```

`filter_operator` defaults to `all` (AND). Use `any` for OR.

## Operators

| Operator | Value shape | Notes |
| --- | --- | --- |
| `is`, `is_not` | scalar or entity link | Equality on any field type |
| `less_than`, `greater_than` | number or date | Numeric and date comparison |
| `contains`, `not_contains` | string | Substring match, case-insensitive |
| `starts_with`, `ends_with` | string | Prefix / suffix match |
| `between`, `not_between` | `[low, high]` | Inclusive range |
| `in`, `not_in` | list of values | Membership test |
| `in_last`, `not_in_last` | `[amount, unit]` | Relative to now, in the past |
| `in_next`, `not_in_next` | `[amount, unit]` | Relative to now, in the future |
| `in_calendar_day` / `_week` / `_month` / `_year` | `[amount, unit]` | Calendar-aligned windows |
| `type_is`, `type_is_not` | entity type name | Match the linked entity's type |
| `name_contains`, `name_not_contains`, `name_is` | string | Match the linked entity's name |

## Time filters

Relative filters take the amount **and** the unit as two extra list entries:

```json
["updated_at", "in_last", 7, "DAY"]
["created_at", "in_calendar_month", 1, "MONTH"]
```

Omitting the unit is the most common mistake — `["updated_at", "in_last", 7]`
is not a complete condition.

## Entity links

A field that points at another entity compares against a link dict:

```json
["project", "is", { "type": "Project", "id": 123 }]
["assigned_to", "is", { "type": "HumanUser", "id": 88 }]
```

`type_is` and the `name_*` operators let you match a link without knowing its ID:

```json
["entity", "type_is", "Asset"]
["entity", "name_contains", "hero"]
```

## Status codes

`sg_status_list` values are short codes, not the labels shown in the ShotGrid
UI. `ip` is "In Progress", `fin` is "Final", `wtg` is "Waiting to Start", and
most studios add their own. Read the valid codes for the entity type from the
`shotgrid://schema/statuses` resource or from `schema_get` before filtering on
status.

## Multi-entity fields

Fields such as `assigned_users` hold a list. Use `in` / `not_in` against them:

```json
["assigned_users", "in", { "type": "HumanUser", "id": 88 }]
```
