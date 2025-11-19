# Deployment Guide

This guide explains how to deploy the ShotGrid MCP Server in various environments.

## Table of Contents

- [ASGI Deployment](#asgi-deployment)
- [Stdio Mode (Local)](#stdio-mode-local)
- [HTTP Mode (Remote)](#http-mode-remote)
- [Cloud Platforms](#cloud-platforms)
- [Production Best Practices](#production-best-practices)

## ASGI Deployment

The ShotGrid MCP Server provides a standard ASGI application that can be deployed to any ASGI server.

### Using the Default ASGI App

The simplest way to deploy is using the pre-configured ASGI application:

```bash
# Development mode with auto-reload
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --reload

# Production mode with multiple workers
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# With Gunicorn (recommended for production)
gunicorn shotgrid_mcp_server.asgi:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker

# With Hypercorn
hypercorn shotgrid_mcp_server.asgi:app --bind 0.0.0.0:8000
```

### Custom ASGI App with Middleware

For production deployments, you can create a custom ASGI app with middleware:

**app.py:**
```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

# Configure CORS for your domain
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Create app with middleware
app = create_asgi_app(
    middleware=[cors_middleware],
    path="/mcp"
)
```

Deploy it:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Stdio Mode (Local)

Stdio mode is designed for local MCP clients like Claude Desktop, Cursor, etc.

### Using UV

```bash
# Run with uvx (recommended)
uvx shotgrid-mcp-server

# Or install and run
uv pip install shotgrid-mcp-server
shotgrid-mcp-server stdio
```

### Environment Configuration

Create a `.env` file or set environment variables:

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_api_key"
```

### Claude Desktop Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "shotgrid": {
      "command": "uvx",
      "args": ["shotgrid-mcp-server"],
      "env": {
        "SHOTGRID_URL": "https://your-site.shotgunstudio.com",
        "SHOTGRID_SCRIPT_NAME": "your_script_name",
        "SHOTGRID_SCRIPT_KEY": "your_api_key"
      }
    }
  }
}
```

## HTTP Mode (Remote)

HTTP mode is designed for web-based deployments and remote access.

### Basic Usage

```bash
# Default settings (127.0.0.1:8000/mcp)
shotgrid-mcp-server http

# Custom host and port
shotgrid-mcp-server http --host 0.0.0.0 --port 8080

# Custom path
shotgrid-mcp-server http --path /api/mcp
```

### Multi-Site Support

HTTP mode supports multiple ShotGrid sites via HTTP headers:

**Server Setup:**
```bash
# Set default credentials (required for startup)
export SHOTGRID_URL="https://default.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="default_script"
export SHOTGRID_SCRIPT_KEY="default_key"

# Start server
shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

**Client Configuration:**

For each ShotGrid site, configure custom headers in your MCP client:

```json
{
  "mcpServers": {
    "shotgrid-site-1": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site1.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "site1_script",
          "X-ShotGrid-Script-Key": "site1_key"
        }
      }
    },
    "shotgrid-site-2": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site2.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "site2_script",
          "X-ShotGrid-Script-Key": "site2_key"
        }
      }
    }
  }
}
```

## Cloud Platforms

### FastMCP Cloud

Deploy to FastMCP Cloud platform:

1. Create your ASGI app (see `app.py` example)
2. Follow FastMCP Cloud deployment guide: https://gofastmcp.com/deployment/fastmcp-cloud

### Docker Deployment

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src ./src

# Install dependencies
RUN uv pip install --system -e .

# Expose port
EXPOSE 8000

# Run with uvicorn
CMD ["uvicorn", "shotgrid_mcp_server.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:
```bash
docker build -t shotgrid-mcp-server .
docker run -p 8000:8000 \
    -e SHOTGRID_URL="https://your-site.shotgunstudio.com" \
    -e SHOTGRID_SCRIPT_NAME="your_script" \
    -e SHOTGRID_SCRIPT_KEY="your_key" \
    shotgrid-mcp-server
```

### Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  shotgrid-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SHOTGRID_URL=${SHOTGRID_URL}
      - SHOTGRID_SCRIPT_NAME=${SHOTGRID_SCRIPT_NAME}
      - SHOTGRID_SCRIPT_KEY=${SHOTGRID_SCRIPT_KEY}
    restart: unless-stopped
```

Run with:
```bash
docker-compose up -d
```

### Kubernetes

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shotgrid-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shotgrid-mcp-server
  template:
    metadata:
      labels:
        app: shotgrid-mcp-server
    spec:
      containers:
      - name: shotgrid-mcp-server
        image: shotgrid-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: SHOTGRID_URL
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: url
        - name: SHOTGRID_SCRIPT_NAME
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: script-name
        - name: SHOTGRID_SCRIPT_KEY
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: script-key
---
apiVersion: v1
kind: Service
metadata:
  name: shotgrid-mcp-server
spec:
  selector:
    app: shotgrid-mcp-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## Production Best Practices

### Security

1. **Use HTTPS**: Always deploy behind a reverse proxy with SSL/TLS
2. **Restrict CORS**: Configure specific allowed origins instead of `*`
3. **Secure Credentials**: Use secrets management (environment variables, vault, etc.)
4. **Rate Limiting**: Add rate limiting middleware to prevent abuse

### Performance

1. **Multiple Workers**: Use multiple worker processes for better concurrency
2. **Connection Pooling**: The server uses connection pooling by default
3. **Caching**: Consider adding caching middleware for frequently accessed data

### Monitoring

1. **Logging**: Configure structured logging for better observability
2. **Metrics**: Add metrics collection (Prometheus, DataDog, etc.)
3. **Health Checks**: Implement health check endpoints

### Example Production Setup

**app.py with production middleware:**
```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    ),
    Middleware(GZipMiddleware, minimum_size=1000),
]

app = create_asgi_app(middleware=middleware, path="/mcp")
```

**Deploy with Gunicorn:**
```bash
gunicorn app:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### Reverse Proxy (Nginx)

**nginx.conf:**
```nginx
upstream shotgrid_mcp {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /mcp {
        proxy_pass http://shotgrid_mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### Connection Issues

If you're having connection issues:

1. Verify credentials are correctly set
2. Check firewall rules
3. Ensure ShotGrid server is accessible
4. Review server logs

### Performance Issues

For performance problems:

1. Increase worker count
2. Enable connection pooling
3. Add caching layer
4. Monitor resource usage

### Multi-Site Issues

When using multi-site support:

1. Verify headers are being sent correctly
2. Check header names match exactly
3. Ensure each site has valid credentials
4. Review server logs for header values
