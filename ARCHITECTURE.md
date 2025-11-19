# Architecture Overview

This document describes the architecture of the ShotGrid MCP Server, focusing on the transport modes and deployment options.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Clients                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │Claude Desktop│  │   Cursor     │  │  Web Applications    │  │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘  │
└─────────┼──────────────────┼────────────────────┼──────────────┘
          │                  │                    │
          │ stdio            │ stdio              │ HTTP/HTTPS
          │                  │                    │
┌─────────▼──────────────────▼────────────────────▼──────────────┐
│                   ShotGrid MCP Server                            │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Transport Layer (Decoupled)                   │ │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐  │ │
│  │  │  stdio   │  │   HTTP   │  │    ASGI Application    │  │ │
│  │  │Transport │  │Transport │  │  (Uvicorn/Gunicorn)    │  │ │
│  │  └────┬─────┘  └────┬─────┘  └──────────┬─────────────┘  │ │
│  └───────┼─────────────┼───────────────────┼────────────────┘ │
│          │             │                   │                   │
│  ┌───────▼─────────────▼───────────────────▼────────────────┐ │
│  │                  MCP Core Logic                           │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ FastMCP Server (create_server)                      │ │ │
│  │  │  - Tool Registration                                │ │ │
│  │  │  - Request Routing                                  │ │ │
│  │  │  - Connection Management                            │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │              Middleware Layer (Optional)                  │ │
│  │  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────┐ │ │
│  │  │  CORS   │  │  Auth    │  │  Logging  │  │ GZip    │ │ │
│  │  └─────────┘  └──────────┘  └───────────┘  └─────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │            Connection Pool & Credentials                   │ │
│  │  ┌─────────────────────────────────────────────────────┐ │ │
│  │  │ ShotGridConnectionContext                           │ │ │
│  │  │  - Environment Variables (stdio)                   │ │ │
│  │  │  - HTTP Headers (HTTP transport)                   │ │ │
│  │  │  - Multi-site Support                              │ │ │
│  │  └─────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────┘ │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          │ shotgun_api3
                          │
                ┌─────────▼─────────┐
                │  ShotGrid Server  │
                │  (Flow Production │
                │     Tracking)     │
                └───────────────────┘
```

## Transport Modes

### 1. Stdio Transport

**Use Case**: Local MCP clients (Claude Desktop, Cursor, etc.)

**Flow**:
```
Client Process → stdin/stdout → MCP Server → ShotGrid API
```

**Credentials**: Environment variables
```bash
SHOTGRID_URL=https://your-site.shotgunstudio.com
SHOTGRID_SCRIPT_NAME=your_script
SHOTGRID_SCRIPT_KEY=your_key
```

**Usage**:
```bash
uvx shotgrid-mcp-server stdio
```

### 2. HTTP Transport

**Use Case**: Web-based deployments, remote access, multi-site support

**Flow**:
```
HTTP Client → HTTP Request → FastMCP HTTP Handler → MCP Server → ShotGrid API
```

**Credentials**: HTTP headers or environment variables
```
X-ShotGrid-URL: https://site.shotgunstudio.com
X-ShotGrid-Script-Name: script_name
X-ShotGrid-Script-Key: api_key
```

**Usage**:
```bash
shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

### 3. ASGI Application

**Use Case**: Production deployments, cloud platforms, containerized environments

**Flow**:
```
HTTP/WebSocket → ASGI Server → ASGI App → FastMCP → MCP Server → ShotGrid API
```

**Credentials**: HTTP headers or environment variables

**Usage**:
```bash
# Direct ASGI app
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# Custom app with middleware
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Component Architecture

### Core Components

1. **server.py**: MCP server creation and configuration
   - `create_server()`: Factory function for creating MCP server instances
   - Supports both eager and lazy connection modes
   - Registers all tools and resources

2. **asgi.py**: ASGI application factory
   - `create_asgi_app()`: Creates standalone ASGI applications
   - Supports custom middleware injection
   - Exports default `app` instance for deployment

3. **cli.py**: Command-line interface
   - `stdio`: Local transport mode
   - `http`: HTTP transport mode
   - Click-based CLI with subcommands

4. **connection_pool.py**: Connection management
   - `ShotGridConnectionContext`: Context manager for connections
   - Supports environment variables and HTTP headers
   - Connection pooling and reuse

5. **http_context.py**: HTTP-specific utilities
   - `get_shotgrid_credentials_from_headers()`: Extract credentials from HTTP headers
   - Request debugging and logging
   - Multi-site support

### Tool Architecture

```
┌────────────────────────────────────────────────────────┐
│                    Tool Categories                      │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   CRUD       │  │  Search      │  │  Thumbnails  │ │
│  │              │  │              │  │              │ │
│  │ • Create     │  │ • find       │  │ • download   │ │
│  │ • Read       │  │ • find_one   │  │ • upload     │ │
│  │ • Update     │  │ • advanced   │  │ • batch_dl   │ │
│  │ • Delete     │  │ • summarize  │  │              │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │  Playlists   │  │    Notes     │  │   Vendor     │ │
│  │              │  │              │  │              │ │
│  │ • create     │  │ • create     │  │ • find_users │ │
│  │ • find       │  │ • read       │  │ • find_vers  │ │
│  │ • add_vers   │  │ • update     │  │ • create_pl  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘ │
└────────────────────────────────────────────────────────┘
```

## Deployment Options

### Local Development

```bash
# Stdio mode for local clients
uvx shotgrid-mcp-server

# HTTP mode for testing
shotgrid-mcp-server http --host 127.0.0.1 --port 8000
```

### Production ASGI

```bash
# Using Uvicorn
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn shotgrid_mcp_server.asgi:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4
```

### Docker

```bash
# Build image
docker build -t shotgrid-mcp-server .

# Run container
docker run -p 8000:8000 \
    -e SHOTGRID_URL=... \
    -e SHOTGRID_SCRIPT_NAME=... \
    -e SHOTGRID_SCRIPT_KEY=... \
    shotgrid-mcp-server
```

### Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Kubernetes

```bash
# Apply deployment
kubectl apply -f deployment.yaml

# Check status
kubectl get pods -l app=shotgrid-mcp-server
```

## Multi-Site Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Client                            │
│  ┌───────────────────────────────────────────────────┐  │
│  │          Multi-Site Configuration                  │  │
│  │                                                     │  │
│  │  Site 1: headers={URL, Script, Key}               │  │
│  │  Site 2: headers={URL, Script, Key}               │  │
│  │  Site 3: headers={URL, Script, Key}               │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
          ▼                ▼                ▼
    ┌─────────┐      ┌─────────┐     ┌─────────┐
    │Request 1│      │Request 2│     │Request 3│
    │Site 1   │      │Site 2   │     │Site 3   │
    │Headers  │      │Headers  │     │Headers  │
    └────┬────┘      └────┬────┘     └────┬────┘
         │                │                │
         └────────────────┼────────────────┘
                          │
                          ▼
        ┌──────────────────────────────────┐
        │   ShotGrid MCP Server (Single)   │
        │                                   │
        │  http_context.py extracts        │
        │  credentials from headers        │
        │                                   │
        │  Creates per-request connection  │
        └──────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
    ┌─────────┐     ┌─────────┐    ┌─────────┐
    │  Site 1 │     │  Site 2 │    │  Site 3 │
    │ShotGrid │     │ShotGrid │    │ShotGrid │
    └─────────┘     └─────────┘    └─────────┘
```

## Middleware Architecture

Custom middleware can be injected into the ASGI application:

```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"]),
    Middleware(CustomAuthMiddleware),
    Middleware(LoggingMiddleware),
]

app = create_asgi_app(middleware=middleware)
```

**Middleware Stack** (bottom to top):
1. ASGI Server (Uvicorn/Gunicorn)
2. Custom Middleware (CORS, Auth, Logging, etc.)
3. FastMCP HTTP Handler
4. MCP Core Logic
5. ShotGrid API Client

## Security Considerations

### Authentication

- **Stdio mode**: Local process, inherits user environment
- **HTTP mode**: Credentials in headers (use HTTPS!)
- **ASGI deployment**: Add authentication middleware

### Network Security

- Always use HTTPS in production
- Configure CORS for specific origins
- Add rate limiting middleware
- Use reverse proxy (Nginx) for SSL termination

### Credential Management

- Use environment variables for defaults
- Support secret management systems (Vault, AWS Secrets Manager)
- Never log API keys
- Rotate keys regularly

## Performance Optimization

### Connection Pooling

The server uses connection pooling to reuse ShotGrid API connections:
- Reduces connection overhead
- Improves response times
- Configurable pool size

### Multi-Process Deployment

Use multiple workers for better concurrency:
```bash
uvicorn app:app --workers 4
gunicorn app:app -k uvicorn.workers.UvicornWorker --workers 4
```

### Caching

Add caching middleware for frequently accessed data:
- Schema information
- Project lists
- User data

### Monitoring

Implement monitoring for production:
- Request/response logging
- Performance metrics
- Error tracking
- Health checks

## Extension Points

### Custom Middleware

Add custom middleware for:
- Authentication/authorization
- Request logging
- Rate limiting
- Caching
- Metrics collection

### Custom Tools

Extend the server with custom tools:
1. Create tool functions in `tools/` directory
2. Register in `tools/__init__.py`
3. Tools automatically available in all transport modes

### Custom Transports

FastMCP supports custom transports:
- WebSocket
- SSE (Server-Sent Events)
- Custom protocols

## Testing Strategy

### Unit Tests

- Test individual components in isolation
- Mock external dependencies
- Fast execution

### Integration Tests

- Test component interactions
- Use test ShotGrid instance
- Verify end-to-end flows

### Deployment Tests

- Test Docker builds
- Verify environment configurations
- Check health endpoints

## Future Enhancements

### Planned Features

1. **WebSocket Support**: Real-time updates
2. **GraphQL API**: Alternative query interface
3. **Caching Layer**: Redis integration
4. **Metrics Export**: Prometheus endpoints
5. **Admin Dashboard**: Web UI for management
6. **Plugin System**: Dynamic tool loading

### Performance Improvements

1. **Async Connection Pool**: Better concurrency
2. **Request Batching**: Reduce API calls
3. **Response Compression**: Faster transfers
4. **Edge Caching**: CDN integration

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [ShotGrid API Documentation](https://developers.shotgridsoftware.com/)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Starlette Documentation](https://www.starlette.io/)
