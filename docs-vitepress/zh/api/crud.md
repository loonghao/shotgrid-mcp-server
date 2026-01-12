# CRUD 操作

ShotGrid 实体的基本创建、读取、更新、删除操作。

## create_entity

在 ShotGrid 中创建新实体。

### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `entity_type` | string | 是 | 实体类型（Shot、Asset、Task 等） |
| `data` | object | 是 | 实体数据 |

### 示例

```
在项目 123 中创建一个名为 "SH001" 的新镜头
```

## find_one_entity

通过 ID 或过滤条件查找单个实体。

### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `entity_type` | string | 是 | 实体类型 |
| `filters` | array | 是 | 过滤条件 |
| `fields` | array | 否 | 返回的字段 |

### 示例

```
查找 ID 为 456 的镜头
```

## search_entities

搜索匹配条件的多个实体。

### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `entity_type` | string | 是 | 实体类型 |
| `filters` | array | 否 | 过滤条件 |
| `fields` | array | 否 | 返回的字段 |
| `order` | array | 否 | 排序方式 |
| `limit` | number | 否 | 最大结果数 |

### 示例

```
查找项目 123 中状态为 "ip" 的所有镜头
```

## update_entity

更新现有实体。

### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `entity_type` | string | 是 | 实体类型 |
| `entity_id` | number | 是 | 实体 ID |
| `data` | object | 是 | 要更新的字段 |

### 示例

```
将镜头 456 的状态更新为 "fin"
```

## delete_entity

删除实体（软删除）。

### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `entity_type` | string | 是 | 实体类型 |
| `entity_id` | number | 是 | 实体 ID |

### 示例

```
删除镜头 456
```
