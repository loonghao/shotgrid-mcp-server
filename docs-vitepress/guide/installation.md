# Installation

## Package Installation

### Using uv (Recommended)

```bash
uv pip install shotgrid-mcp-server
```

### Using pip

```bash
pip install shotgrid-mcp-server
```

### From Source

```bash
git clone https://github.com/loonghao/shotgrid-mcp-server.git
cd shotgrid-mcp-server
pip install -e .
```

## MCP Client Configuration

### Claude Desktop

Add to your Claude Desktop configuration file:

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
        "SHOTGRID_SCRIPT_KEY": "your_script_key"
      }
    }
  }
}
```

### Cursor / VS Code

Add to your MCP settings:

```json
{
  "mcpServers": {
    "shotgrid": {
      "command": "uvx",
      "args": ["shotgrid-mcp-server"],
      "env": {
        "SHOTGRID_URL": "https://your-site.shotgunstudio.com",
        "SHOTGRID_SCRIPT_NAME": "your_script_name",
        "SHOTGRID_SCRIPT_KEY": "your_script_key"
      }
    }
  }
}
```

### HTTP Transport (Remote)

```json
{
  "mcpServers": {
    "shotgrid": {
      "url": "http://your-server:8000/mcp",
      "transport": { "type": "http" }
    }
  }
}
```
