# ShotGrid MCP Server 缓存策略调研与实施方案

## 调研结果

### 1. FastMCP 内置缓存支持 ✅

**FastMCP 2.13.0 (2025-10-25)** 已经内置了完整的缓存解决方案：

#### Response Caching Middleware
- 专为 MCP 设计的响应缓存中间件
- 可以缓存 tool 和 resource 的响应
- 支持 TTL（Time-To-Live）配置
- 自动处理缓存失效

#### Pluggable Storage Backends
基于 [py-key-value-aio](https://github.com/strawgate/py-key-value) 库，支持多种后端：
- **Filesystem** (默认，带加密)
- **In-Memory**
- **Redis**
- **DynamoDB**
- **Elasticsearch**
- 支持加密、TTL、缓存等包装器

### 2. MCP 协议层面的缓存

MCP 协议本身没有定义缓存机制，但提供了一些相关特性：

#### Resources
- Resources 是只读的，天然适合缓存
- 可以通过 URI 唯一标识
- 支持模板化 URI (RFC 6570)

#### Tools
- Tools 可能有副作用，需要谨慎缓存
- 可以基于参数哈希进行缓存

### 3. Schema 缓存策略

ShotGrid schema 的特点：
- **相对稳定**：schema 不会频繁变化
- **体积较大**：完整 schema 包含大量字段定义
- **访问频繁**：每次验证都可能需要 schema

## 推荐方案

### 方案 A：使用 FastMCP 内置缓存（推荐）

**优势：**
- ✅ 与 MCP 生态完美集成
- ✅ 开箱即用，无需额外依赖
- ✅ 支持多种存储后端
- ✅ 自动处理序列化/反序列化
- ✅ 支持加密存储

**实施步骤：**

```python
from fastmcp import FastMCP
from fastmcp.middleware import CachingMiddleware

# 创建服务器
mcp = FastMCP("shotgrid-mcp-server")

# 添加缓存中间件
mcp.add_middleware(
    CachingMiddleware(
        # 缓存 schema 资源 24 小时
        resource_ttl=86400,  # 24 hours
        # 缓存搜索结果 5 分钟
        tool_ttl=300,  # 5 minutes
        # 使用文件系统存储（默认加密）
        backend="filesystem",
        # 或使用 Redis
        # backend="redis://localhost:6379/0"
    )
)
```

### 方案 B：使用 diskcache（备选）

如果需要更细粒度的控制，可以使用 diskcache：

```python
from diskcache import Cache
from functools import wraps

# 创建缓存实例
schema_cache = Cache("./cache/schema", size_limit=100 * 1024 * 1024)  # 100MB

def cached_schema(ttl=86400):
    """Schema 缓存装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            result = schema_cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                schema_cache.set(cache_key, result, expire=ttl)
            return result
        return wrapper
    return decorator

@cached_schema(ttl=86400)  # 24 hours
def get_entity_schema(entity_type: str):
    return sg.schema_field_read(entity_type)
```

### 方案 C：混合方案（最佳实践）

结合两者优势：

1. **FastMCP 缓存中间件**：处理 MCP 层面的响应缓存
2. **diskcache**：处理应用层面的数据缓存（如 schema）

```python
# 1. FastMCP 层缓存
mcp.add_middleware(CachingMiddleware(resource_ttl=3600))

# 2. 应用层 Schema 缓存
from diskcache import Cache
schema_cache = Cache("./cache/schema")

@schema_cache.memoize(expire=86400)
def get_cached_schema(entity_type: str):
    return sg.schema_field_read(entity_type)
```

## 缓存策略建议

### Schema 缓存
- **TTL**: 24 小时
- **失效策略**: 手动失效 + 定时刷新
- **存储**: 文件系统（加密）

### 搜索结果缓存
- **TTL**: 5-15 分钟
- **失效策略**: 基于参数哈希
- **存储**: 内存或 Redis

### 实体数据缓存
- **TTL**: 1-5 分钟
- **失效策略**: 写操作自动失效
- **存储**: 内存

## 性能优化建议

### 1. Schema 预加载
```python
async def preload_schemas():
    """服务器启动时预加载常用 schema"""
    common_entities = ["Shot", "Asset", "Task", "Version", "Note"]
    for entity_type in common_entities:
        await get_cached_schema(entity_type)
```

### 2. 批量缓存
```python
def cache_multiple_schemas(entity_types: List[str]):
    """批量缓存多个 entity schema"""
    with schema_cache.transact():
        for entity_type in entity_types:
            get_cached_schema(entity_type)
```

### 3. 缓存预热
```python
@mcp.lifespan()
async def lifespan():
    """服务器生命周期管理"""
    # 启动时预热缓存
    await preload_schemas()
    yield
    # 关闭时清理
    schema_cache.close()
```

## 监控与调试

### 缓存命中率监控
```python
from fastmcp.middleware import CachingMiddleware

cache_middleware = CachingMiddleware(
    resource_ttl=86400,
    enable_metrics=True  # 启用指标收集
)

# 查看缓存统计
print(f"Cache hits: {cache_middleware.hits}")
print(f"Cache misses: {cache_middleware.misses}")
print(f"Hit rate: {cache_middleware.hit_rate:.2%}")
```

### 缓存调试
```python
# 查看缓存内容
for key in schema_cache:
    print(f"Key: {key}, Size: {len(schema_cache[key])}")

# 清空特定缓存
schema_cache.delete("schema:Shot")

# 清空所有缓存
schema_cache.clear()
```

## 总结

**推荐使用 FastMCP 2.13.0 内置的 Response Caching Middleware**，原因：

1. ✅ 原生支持，无需额外集成
2. ✅ 自动处理 MCP 协议细节
3. ✅ 支持多种存储后端
4. ✅ 内置加密和 TTL 支持
5. ✅ 与 FastMCP 生态完美集成

对于特殊需求（如 schema 验证缓存），可以在应用层使用 diskcache 作为补充。

