# Getting Started

ShotGrid MCP Server enables AI assistants like Claude, Cursor, and VS Code Copilot to interact directly with your ShotGrid (Flow Production Tracking) data.

## Prerequisites

- Python 3.10+
- ShotGrid account with API access
- MCP-compatible client (Claude Desktop, Cursor, VS Code, etc.)

## Quick Installation

```bash
# Using uv (recommended)
uv pip install shotgrid-mcp-server

# Or using pip
pip install shotgrid-mcp-server
```

## Configuration

Set your ShotGrid credentials as environment variables:

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_script_key"
```

## Run the Server

### stdio Transport (Default)

For Claude Desktop, Cursor, and other local MCP clients:

```bash
uvx shotgrid-mcp-server
```

### HTTP Transport

For remote access:

```bash
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

## Next Steps

- [Installation Guide](/guide/installation) - Detailed installation instructions
- [Configuration](/guide/configuration) - Advanced configuration options
- [Demos](/guide/demos/editor-setup) - See it in action
