# Quick Start Guide

Get up and running with ShotGrid MCP Server in minutes!

## Table of Contents

- [Installation](#installation)
- [Stdio Mode (Local Use)](#stdio-mode-local-use)
- [HTTP Mode (Remote Access)](#http-mode-remote-access)
- [ASGI Deployment (Production)](#asgi-deployment-production)
- [Docker Deployment](#docker-deployment)
- [Next Steps](#next-steps)

## Installation

Install using UV (recommended):

```bash
uv pip install shotgrid-mcp-server
```

Or using pip:

```bash
pip install shotgrid-mcp-server
```

## Stdio Mode (Local Use)

Perfect for using with Claude Desktop, Cursor, or other local MCP clients.

### Step 1: Set Environment Variables

Create a `.env` file or export environment variables:

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_api_key"
```

### Step 2: Run the Server

```bash
uvx shotgrid-mcp-server
# or
shotgrid-mcp-server stdio
```

### Step 3: Configure Claude Desktop

Edit your Claude Desktop config file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

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

### Step 4: Restart Claude Desktop

Restart Claude Desktop and you should see the ShotGrid MCP server in the MCP menu.

## HTTP Mode (Remote Access)

Perfect for team deployments or web-based applications.

### Step 1: Set Default Credentials

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_api_key"
```

### Step 2: Start HTTP Server

```bash
shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

### Step 3: Configure Your MCP Client

```json
{
  "mcpServers": {
    "shotgrid-remote": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

### Multi-Site Support (Optional)

Override credentials per request using HTTP headers:

```json
{
  "mcpServers": {
    "shotgrid-site1": {
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
    "shotgrid-site2": {
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

## ASGI Deployment (Production)

Perfect for production deployments with high availability and scalability.

### Option 1: Using Default ASGI App

```bash
# Development mode
uvicorn shotgrid_mcp_server.asgi:app --reload

# Production mode (4 workers)
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# Production with Gunicorn
gunicorn shotgrid_mcp_server.asgi:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4
```

### Option 2: Custom App with Middleware

Create `app.py`:

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

# Create app
app = create_asgi_app(middleware=[cors_middleware], path="/mcp")
```

Deploy:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Docker Deployment

Perfect for containerized environments and cloud platforms.

### Step 1: Create `.env` File

```bash
SHOTGRID_URL=https://your-site.shotgunstudio.com
SHOTGRID_SCRIPT_NAME=your_script_name
SHOTGRID_SCRIPT_KEY=your_api_key
```

### Step 2: Run with Docker

```bash
# Build image
docker build -t shotgrid-mcp-server .

# Run container
docker run -p 8000:8000 --env-file .env shotgrid-mcp-server
```

### Step 3: Or Use Docker Compose

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f shotgrid-mcp

# Stop services
docker-compose down
```

## Testing Your Deployment

### Test Stdio Mode

```bash
# Start server
shotgrid-mcp-server stdio

# In another terminal, test with MCP client
# (or use Claude Desktop)
```

### Test HTTP Mode

```bash
# Start server
shotgrid-mcp-server http --port 8000

# Test health (if implemented)
curl http://localhost:8000/health

# Test MCP endpoint with your client
```

### Test ASGI App

```bash
# Start server
uvicorn shotgrid_mcp_server.asgi:app --port 8000

# Test endpoint
curl http://localhost:8000/mcp
```

## Common Issues

### Issue: "Missing required environment variables"

**Solution**: Ensure all three environment variables are set:
```bash
export SHOTGRID_URL="..."
export SHOTGRID_SCRIPT_NAME="..."
export SHOTGRID_SCRIPT_KEY="..."
```

### Issue: "Connection refused"

**Solution**: 
- Check if the server is running
- Verify the port is not blocked by firewall
- Ensure correct host/port in client configuration

### Issue: "Invalid credentials"

**Solution**:
- Verify script name and API key are correct
- Check if script is enabled in ShotGrid
- Ensure URL is correct (include https://)

### Issue: Docker container exits immediately

**Solution**:
- Check logs: `docker logs <container-id>`
- Verify environment variables are passed correctly
- Ensure `.env` file is in the correct location

## Next Steps

- 📚 Read the [Deployment Guide](deployment.md) for production setup
- 🏗️ Review the [Architecture Overview](../ARCHITECTURE.md) to understand the system
- 🔧 Check out [examples/custom_app.py](../examples/custom_app.py) for advanced middleware
- 🐳 Explore Docker and Kubernetes deployment options

## Getting Help

- 📖 Check the [README](../README.md) for feature overview
- 🐛 Report issues on [GitHub](https://github.com/loonghao/shotgrid-mcp-server/issues)
- 💬 Join discussions on [GitHub Discussions](https://github.com/loonghao/shotgrid-mcp-server/discussions)

## Example Workflows

### Local Development with Claude Desktop

1. Install: `uv pip install shotgrid-mcp-server`
2. Set env vars in Claude config
3. Restart Claude Desktop
4. Ask Claude: "List all active projects in ShotGrid"

### Team Deployment

1. Deploy HTTP server: `shotgrid-mcp-server http --host 0.0.0.0 --port 8000`
2. Configure reverse proxy (Nginx) with SSL
3. Team members connect via HTTP transport
4. Each can use different site credentials via headers

### Production Cloud Deployment

1. Create `app.py` with custom middleware
2. Build Docker image
3. Deploy to Kubernetes/Cloud Run/etc.
4. Configure auto-scaling and load balancing
5. Add monitoring and logging

Enjoy using ShotGrid MCP Server! 🎬
