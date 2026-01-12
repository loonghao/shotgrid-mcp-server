# Batch Operations

Perform bulk operations efficiently in a single API call.

## batch_create

Create multiple entities at once.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type |
| `data_list` | array | Yes | List of entity data objects |

### Example

```
Create 10 shots named SH001 to SH010 in project 123
```

## batch_update

Update multiple entities at once.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `updates` | array | Yes | List of update objects |

Each update object contains:
- `entity_type`: Entity type
- `entity_id`: Entity ID
- `data`: Fields to update

### Example

```
Update status to "fin" for shots 100, 101, and 102
```

## batch_delete

Delete multiple entities at once.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entities` | array | Yes | List of entity references |

Each entity reference contains:
- `entity_type`: Entity type
- `entity_id`: Entity ID

### Example

```
Delete shots 100, 101, and 102
```

## Performance Benefits

Batch operations are significantly faster than individual operations:

| Operation | Individual | Batch | Speedup |
|-----------|------------|-------|---------|
| Create 100 entities | ~100 API calls | 1 API call | ~100x |
| Update 50 entities | ~50 API calls | 1 API call | ~50x |
| Delete 20 entities | ~20 API calls | 1 API call | ~20x |
