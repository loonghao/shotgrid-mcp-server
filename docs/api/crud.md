# CRUD Operations

Basic Create, Read, Update, Delete operations for ShotGrid entities.

## create_entity

Create a new entity in ShotGrid.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type (Shot, Asset, Task, etc.) |
| `data` | object | Yes | Entity data |

### Example

```
Create a new shot called "SH001" in project 123
```

## find_one_entity

Find a single entity by ID or filters.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type |
| `filters` | array | Yes | Filter conditions |
| `fields` | array | No | Fields to return |

### Example

```
Find shot with ID 456
```

## search_entities

Search for multiple entities matching criteria.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type |
| `filters` | array | No | Filter conditions |
| `fields` | array | No | Fields to return |
| `order` | array | No | Sort order |
| `limit` | number | No | Max results |

### Example

```
Find all shots in project 123 with status "ip"
```

## update_entity

Update an existing entity.

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type |
| `entity_id` | number | Yes | Entity ID |
| `data` | object | Yes | Fields to update |

### Example

```
Update shot 456 status to "fin"
```

## delete_entity

Delete an entity (soft delete).

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `entity_type` | string | Yes | Entity type |
| `entity_id` | number | Yes | Entity ID |

### Example

```
Delete shot 456
```
