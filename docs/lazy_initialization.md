# Lazy Initialization in ASGI Mode

## Problem

When deploying the ShotGrid MCP Server in ASGI mode, the original implementation would attempt to create a ShotGrid connection during module import time. This caused issues in several scenarios:

1. **Docker Build Time**: During `docker build`, environment variables might contain placeholder values (e.g., `example.shotgunstudio.com`), causing connection failures
2. **Module Import**: Simply importing the module would trigger connection attempts
3. **Startup Failures**: If ShotGrid was temporarily unavailable, the entire application would fail to start

### Error Example

```
ProtocolError: <ProtocolError for example.shotgunstudio.com: 404 Not Found>
Failed to initialize server: <ProtocolError for example.shotgunstudio.com: 404 Not Found>
```

## Solution: Lazy Initialization

The ASGI application now uses **lazy initialization** - the actual ShotGrid connection is only created when the first request arrives, not when the module is imported.

### How It Works

#### Before (Eager Initialization)

```python
# asgi.py
from shotgrid_mcp_server.asgi import create_asgi_app

# This executes immediately when the module is imported!
app = create_asgi_app()  # ❌ Tries to connect to ShotGrid
```

#### After (Lazy Initialization)

```python
# asgi.py
_app_instance = None

def get_app():
    """Create app only when first accessed."""
    global _app_instance
    if _app_instance is None:
        _app_instance = create_asgi_app()  # ✅ Only creates on first request
    return _app_instance

def app(scope, receive, send):
    """ASGI entry point - lazy initialization."""
    application = get_app()
    return application(scope, receive, send)
```

### Benefits

1. **Docker Build Safety**: Module can be imported during Docker build without connecting to ShotGrid
2. **Startup Resilience**: Application starts even if ShotGrid is temporarily unavailable
3. **Environment Flexibility**: Can use placeholder environment variables during build
4. **On-Demand Connection**: Connection is created only when actually needed

## Implementation Details

### ASGI Module (`shotgrid_mcp_server/asgi.py`)

```python
# Lazy initialization of default ASGI application
_app_instance = None

def get_app():
    """Get or create the default ASGI application instance.
    
    This function implements lazy initialization to avoid creating
    ShotGrid connections during module import or Docker build time.
    """
    global _app_instance
    if _app_instance is None:
        logger.info("Initializing default ASGI application (lazy mode)")
        try:
            _app_instance = create_asgi_app()
            logger.info("ASGI application initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize ASGI application: %s", str(e))
            raise
    return _app_instance

# Module-level callable for ASGI servers
def app(scope, receive, send):
    """ASGI application entry point with lazy initialization."""
    application = get_app()
    return application(scope, receive, send)
```

### Custom App (`app.py`)

```python
_app_instance = None

def get_app():
    """Get or create the ASGI application with middleware."""
    global _app_instance
    if _app_instance is None:
        cors_middleware = Middleware(...)
        _app_instance = create_asgi_app(middleware=[cors_middleware])
    return _app_instance

def app(scope, receive, send):
    """ASGI application entry point with lazy initialization."""
    application = get_app()
    return application(scope, receive, send)
```

## Usage

### Development

```bash
# No connection during import
uvicorn shotgrid_mcp_server.asgi:app --reload

# Connection created on first HTTP request
curl http://localhost:8000/mcp
```

### Docker Build

```dockerfile
# Safe to run during build - no connection attempt
COPY src ./src
COPY app.py ./

# Connection only happens when container runs
CMD ["uvicorn", "shotgrid_mcp_server.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build succeeds even with placeholder credentials
docker build -t shotgrid-mcp-server .

# Run with real credentials
docker run -p 8000:8000 \
    -e SHOTGRID_URL="https://real-site.shotgunstudio.com" \
    -e SHOTGRID_SCRIPT_NAME="real_script" \
    -e SHOTGRID_SCRIPT_KEY="real_key" \
    shotgrid-mcp-server
```

### Production Deployment

```bash
# Workers start without connecting
gunicorn shotgrid_mcp_server.asgi:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4

# Each worker creates connection on first request
# Requests are load-balanced across workers
```

## Testing

The lazy initialization is tested to ensure:

1. **Module Import Safety**: Importing the module doesn't create connections
2. **Singleton Pattern**: `get_app()` returns the same instance
3. **On-Demand Creation**: App is only created when first accessed

```python
def test_create_asgi_app_lazy_initialization(mock_env_vars):
    """Test that the module-level app uses lazy initialization."""
    from shotgrid_mcp_server import asgi
    
    # The app should be a function (lazy init), not an instance
    assert callable(asgi.app)
    
    # Calling get_app() should create the instance
    app_instance = asgi.get_app()
    assert app_instance is not None
    
    # Calling again should return the same instance (singleton)
    app_instance2 = asgi.get_app()
    assert app_instance is app_instance2
```

## Comparison with HTTP Mode

### HTTP Mode (CLI)

In HTTP mode via CLI, the connection can still be created eagerly or lazily depending on the `lazy_connection` parameter:

```python
# cli.py - HTTP mode
def http(host: str, port: int, path: str) -> None:
    # Use lazy connection mode for HTTP
    app = create_server(lazy_connection=True)
    app.run(transport=\"http\", host=host, port=port, path=path)
```

### Server Module Fix

**Important Fix**: The `server.py` module previously had module-level code that would create a server instance during import:

```python
# ❌ BEFORE - Caused HTTP mode startup errors
if __name__ == "__main__":
    main()
else:
    # When imported, create a server for testing
    try:
        app = create_server()  # ❌ Immediate connection attempt!
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
```

This caused the same issue: when starting HTTP mode, importing `server.py` would trigger a ShotGrid connection attempt with placeholder/environment credentials, resulting in errors like:

```
ProtocolError: <ProtocolError for example.shotgunstudio.com: 404 Not Found>
Failed to initialize server
```

**The fix** was to remove this module-level initialization entirely:

```python
# ✅ AFTER - Safe module import
if __name__ == "__main__":
    main()
# No else block - no automatic initialization!
```

Now, importing `server.py` is safe and doesn't trigger any connection attempts. The server is only created when explicitly requested via CLI commands or ASGI entry points.

### ASGI Mode

In ASGI mode, lazy initialization happens at two levels:

1. **Module Level**: The `app` variable is a function, not an instance
2. **Server Level**: `create_server(lazy_connection=True)` is used

This provides maximum flexibility and resilience.

## Best Practices

### ✅ Do

1. Use lazy initialization for ASGI deployments
2. Test with placeholder credentials during build
3. Provide real credentials at runtime
4. Handle connection errors gracefully

### ❌ Don't

1. Create module-level app instances with `app = create_asgi_app()`
2. Assume connections are available during import
3. Use real credentials in Dockerfiles
4. Skip error handling in `get_app()`

## Troubleshooting

### Issue: "Failed to initialize ASGI application"

**Cause**: Real connection attempt during first request failed

**Solution**: 
- Check environment variables are set correctly
- Verify ShotGrid server is accessible
- Check credentials are valid
- Review logs for specific error

### Issue: "Module import takes too long"

**Cause**: Not using lazy initialization

**Solution**:
- Ensure you're using the lazy initialization pattern
- Don't create app instances at module level
- Use the `get_app()` function pattern

### Issue: "Connection errors during Docker build"

**Cause**: Eager initialization during build

**Solution**:
- Use lazy initialization pattern
- Provide placeholder credentials for build
- Real credentials at runtime only

## Migration Guide

If you have existing code that uses eager initialization:

### Before

```python
# ❌ Eager initialization
from shotgrid_mcp_server.asgi import create_asgi_app

app = create_asgi_app()  # Creates connection immediately
```

### After

```python
# ✅ Lazy initialization
_app_instance = None

def get_app():
    global _app_instance
    if _app_instance is None:
        from shotgrid_mcp_server.asgi import create_asgi_app
        _app_instance = create_asgi_app()
    return _app_instance

def app(scope, receive, send):
    application = get_app()
    return application(scope, receive, send)
```

Or simply use the built-in lazy app:

```python
# ✅ Use built-in lazy app
from shotgrid_mcp_server.asgi import app  # Already lazy!
```

## References

- [ASGI Specification](https://asgi.readthedocs.io/)
- [Lazy Initialization Pattern](https://en.wikipedia.org/wiki/Lazy_initialization)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
