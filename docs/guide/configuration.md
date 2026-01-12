# Configuration

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SHOTGRID_URL` | Yes | Your ShotGrid site URL |
| `SHOTGRID_SCRIPT_NAME` | Yes | API script name |
| `SHOTGRID_SCRIPT_KEY` | Yes | API script key |
| `SHOTGRID_HTTP_PROXY` | No | HTTP proxy URL |
| `SHOTGRID_HTTPS_PROXY` | No | HTTPS proxy URL |

## Example Configuration

```bash
# Required
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_script_key"

# Optional - Proxy settings
export SHOTGRID_HTTP_PROXY="http://proxy:8080"
export SHOTGRID_HTTPS_PROXY="https://proxy:8080"
```

## Transport Options

### stdio (Default)

Best for local MCP clients like Claude Desktop and Cursor.

```bash
uvx shotgrid-mcp-server
```

### HTTP

Best for remote access and shared environments.

```bash
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

### ASGI

Best for production deployments with uvicorn or gunicorn.

```bash
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000
```
