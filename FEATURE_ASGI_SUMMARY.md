# ASGI Application Enhancement - Summary

This document summarizes the enhancements made to support standalone ASGI deployment and improved transport mode decoupling.

## Overview

The ShotGrid MCP Server has been enhanced to provide better separation between stdio and HTTP transport modes, and to support standalone ASGI application deployment for production environments and cloud platforms.

## Key Changes

### 1. New ASGI Module (`src/shotgrid_mcp_server/asgi.py`)

**Purpose**: Provide a standalone ASGI application that can be deployed to any ASGI server.

**Key Features**:
- `create_asgi_app()` factory function for creating customizable ASGI apps
- Support for custom middleware injection (CORS, authentication, logging, etc.)
- **Lazy initialization** to prevent connection errors during Docker build or module import
- `get_app()` function for controlled application initialization
- Default `app` callable for simple deployment (with lazy initialization)
- Comprehensive documentation and examples

**Usage**:
```python
from shotgrid_mcp_server.asgi import create_asgi_app

# Simple deployment
app = create_asgi_app()

# With middleware
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

app = create_asgi_app(
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["*"])
    ],
    path="/mcp"
)
```

**Deploy**:
```bash
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Deployment Entry Point (`app.py`)

**Purpose**: Provide a ready-to-use example for production deployment with middleware.

**Features**:
- Pre-configured CORS middleware
- Comments explaining production considerations
- Easy to customize for specific needs

**Usage**:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Enhanced Package Exports

**Updated**: `src/shotgrid_mcp_server/__init__.py`

**Changes**:
- Added `create_asgi_app` to `__all__` exports
- Imported `create_asgi_app` from asgi module

**Usage**:
```python
from shotgrid_mcp_server import create_asgi_app

app = create_asgi_app()
```

### 4. Comprehensive Documentation

#### English Documentation:
- **docs/deployment.md**: Complete deployment guide
  - ASGI deployment options
  - Stdio and HTTP mode setup
  - Docker, Docker Compose, and Kubernetes examples
  - Production best practices
  - Security considerations
  - Performance optimization
  - Troubleshooting guide

- **docs/QUICKSTART.md**: Quick start guide
  - Step-by-step setup instructions
  - Examples for all deployment modes
  - Common issues and solutions
  - Next steps and resources

- **ARCHITECTURE.md**: System architecture overview
  - Architecture diagrams
  - Component descriptions
  - Transport mode details
  - Multi-site architecture
  - Middleware architecture
  - Security and performance considerations
  - Future enhancements

#### Chinese Documentation:
- **docs/deployment_zh.md**: 部署指南（中文版）
  - All content from English version, translated to Chinese

#### Updated README Files:
- **README.md**: Added ASGI deployment section with examples
- **README_zh.md**: 添加了 ASGI 部署章节和示例

### 5. Docker Support

#### Dockerfile
**Purpose**: Multi-stage build for optimized container images

**Features**:
- Multi-stage build for smaller images
- Non-root user for security
- Health check support
- UV-based dependency management

**Usage**:
```bash
docker build -t shotgrid-mcp-server .
docker run -p 8000:8000 --env-file .env shotgrid-mcp-server
```

#### .dockerignore
**Purpose**: Optimize Docker build context

**Features**:
- Excludes unnecessary files
- Reduces image size
- Faster builds

#### docker-compose.yml
**Purpose**: Easy multi-container orchestration

**Features**:
- ShotGrid MCP service
- Optional Nginx reverse proxy
- Health checks
- Environment variable configuration

**Usage**:
```bash
docker-compose up -d
```

### 6. Advanced Examples

#### examples/custom_app.py
**Purpose**: Demonstrate advanced ASGI application with multiple middleware

**Features**:
- Request logging middleware
- Rate limiting middleware (example)
- CORS configuration
- GZip compression
- Production-ready patterns

**Usage**:
```bash
uvicorn examples.custom_app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 7. Test Coverage

#### tests/test_asgi.py
**Purpose**: Ensure ASGI functionality works correctly

**Tests**:
- Default ASGI app creation
- Custom path configuration
- Single middleware injection
- Multiple middleware injection
- Module-level app initialization

**Run**:
```bash
uv run pytest tests/test_asgi.py -v
```

### 8. CHANGELOG Update

**Updated**: CHANGELOG.md

**Added**:
- New "Unreleased" section documenting all ASGI-related features
- Categorized changes as "Feat" and "Refactor"

## Deployment Options Comparison

| Mode | Use Case | Credentials | Best For |
|------|----------|-------------|----------|
| **stdio** | Local MCP clients | Environment variables | Claude Desktop, Cursor |
| **HTTP** | Remote access | HTTP headers or env vars | Team deployments, multi-site |
| **ASGI** | Production deployment | HTTP headers or env vars | Cloud platforms, high availability |

## Architecture Benefits

### 1. Decoupled Transport Modes

**Before**:
- Transport logic tightly coupled with server logic
- Difficult to add custom middleware
- Limited deployment flexibility

**After**:
- Clear separation between transport and business logic
- Easy to add custom middleware
- Flexible deployment options (Uvicorn, Gunicorn, Hypercorn, etc.)

### 2. Cloud-Ready Deployment

**Features**:
- Standard ASGI application
- Compatible with all ASGI servers
- Easy to deploy to:
  - FastMCP Cloud
  - AWS Lambda (with Mangum)
  - Google Cloud Run
  - Azure Container Apps
  - Heroku, Railway, Render
  - Kubernetes

### 3. Middleware Extensibility

**Capabilities**:
- CORS configuration
- Authentication/authorization
- Rate limiting
- Request logging
- Response compression
- Metrics collection
- Custom business logic

**Example**:
```python
middleware = [
    Middleware(CORSMiddleware, allow_origins=["*"]),
    Middleware(AuthMiddleware, api_key="secret"),
    Middleware(LoggingMiddleware),
    Middleware(GZipMiddleware),
]

app = create_asgi_app(middleware=middleware)
```

### 4. Multi-Site Support

**Architecture**:
- Single server instance serves multiple ShotGrid sites
- Credentials provided via HTTP headers per request
- Cost-effective for organizations with multiple sites

**Example Configuration**:
```json
{
  "mcpServers": {
    "site1": {
      "url": "http://server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site1.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "script1",
          "X-ShotGrid-Script-Key": "key1"
        }
      }
    },
    "site2": {
      "url": "http://server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site2.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "script2",
          "X-ShotGrid-Script-Key": "key2"
        }
      }
    }
  }
}
```

## Production Deployment Patterns

### 1. Simple Production

```bash
# Install
pip install shotgrid-mcp-server

# Set environment
export SHOTGRID_URL="..."
export SHOTGRID_SCRIPT_NAME="..."
export SHOTGRID_SCRIPT_KEY="..."

# Deploy with Uvicorn
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4
```

### 2. Production with Custom Middleware

```python
# app.py
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

app = create_asgi_app(
    middleware=[
        Middleware(CORSMiddleware, allow_origins=["https://yourdomain.com"])
    ]
)
```

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

### 3. Docker Deployment

```bash
# Build
docker build -t shotgrid-mcp-server .

# Run
docker run -p 8000:8000 --env-file .env shotgrid-mcp-server
```

### 4. Docker Compose Deployment

```bash
# Create .env file
echo "SHOTGRID_URL=..." > .env
echo "SHOTGRID_SCRIPT_NAME=..." >> .env
echo "SHOTGRID_SCRIPT_KEY=..." >> .env

# Deploy
docker-compose up -d
```

### 5. Kubernetes Deployment

```bash
# Create secret
kubectl create secret generic shotgrid-credentials \
    --from-literal=url="..." \
    --from-literal=script-name="..." \
    --from-literal=script-key="..."

# Deploy
kubectl apply -f deployment.yaml
```

## Testing

All new functionality is tested:

```bash
# Run ASGI tests
uv run pytest tests/test_asgi.py -v

# Run all tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ -v --cov=shotgrid_mcp_server --cov-report=term-missing
```

## Migration Guide

### From HTTP Mode to ASGI Deployment

**Before** (HTTP mode):
```bash
shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

**After** (ASGI deployment):
```bash
# Option 1: Use default ASGI app
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# Option 2: Use custom app with middleware
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

**Benefits**:
- Better performance with multiple workers
- Custom middleware support
- Standard ASGI deployment
- Compatible with more ASGI servers

### Adding Custom Middleware

**Create** `app.py`:
```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

middleware = [
    Middleware(CORSMiddleware, allow_origins=["https://yourdomain.com"]),
    Middleware(GZipMiddleware, minimum_size=1000),
]

app = create_asgi_app(middleware=middleware, path="/mcp")
```

**Deploy**:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Future Enhancements

Based on this architecture, future enhancements could include:

1. **WebSocket Support**: Real-time updates
2. **GraphQL API**: Alternative query interface
3. **Caching Layer**: Redis integration
4. **Metrics Export**: Prometheus endpoints
5. **Admin Dashboard**: Web UI for management
6. **Plugin System**: Dynamic tool loading
7. **Rate Limiting**: Built-in rate limiting middleware
8. **API Gateway Integration**: Kong, Traefik, etc.

## References

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [FastMCP Cloud Deployment](https://gofastmcp.com/deployment/fastmcp-cloud)
- [ASGI Specification](https://asgi.readthedocs.io/)
- [Starlette Documentation](https://www.starlette.io/)
- [Uvicorn Documentation](https://www.uvicorn.org/)
- [Gunicorn Documentation](https://gunicorn.org/)

## Conclusion

This enhancement significantly improves the deployment flexibility and production readiness of the ShotGrid MCP Server:

✅ **Decoupled Architecture**: Clear separation of concerns  
✅ **Cloud-Ready**: Deploy to any cloud platform  
✅ **Middleware Support**: Easily add custom functionality  
✅ **Multi-Site Support**: Serve multiple ShotGrid sites from one instance  
✅ **Production-Ready**: Docker, Kubernetes, and cloud deployment examples  
✅ **Well-Documented**: Comprehensive guides in English and Chinese  
✅ **Tested**: Full test coverage for new functionality  

The server is now ready for production deployments at scale! 🚀
