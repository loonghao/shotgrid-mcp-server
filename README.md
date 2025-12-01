# 🎯 ShotGrid MCP Server

English | [简体中文](README_zh.md)

<div align="center">

A high-performance ShotGrid Model Context Protocol (MCP) server implementation based on fastmcp

[![Python Version](https://img.shields.io/pypi/pyversions/shotgrid-mcp-server.svg)](https://pypi.org/project/shotgrid-mcp-server/)
[![License](https://img.shields.io/github/license/loonghao/shotgrid-mcp-server.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/shotgrid-mcp-server.svg)](https://badge.fury.io/py/shotgrid-mcp-server)
[![codecov](https://codecov.io/gh/loonghao/shotgrid-mcp-server/branch/main/graph/badge.svg)](https://codecov.io/gh/loonghao/shotgrid-mcp-server)
[![Downloads](https://pepy.tech/badge/shotgrid-mcp-server)](https://pepy.tech/project/shotgrid-mcp-server)
[![Downloads](https://static.pepy.tech/badge/shotgrid-mcp-server/week)](https://pepy.tech/project/shotgrid-mcp-server)
[![Downloads](https://static.pepy.tech/badge/shotgrid-mcp-server/month)](https://pepy.tech/project/shotgrid-mcp-server)

</div>

##  Demo

Here's a simple example of querying entities using the ShotGrid MCP server:

![ShotGrid MCP Server Demo](images/sg-mcp.gif)

## ✨ Features

- 🚀 High-performance implementation based on fastmcp
- 🛠 Complete CRUD operation toolset
- 🖼 Dedicated thumbnail download/upload tools
- 🔄 Efficient connection pool management
- 🔌 Direct ShotGrid API access through MCP tools
- 📝 Enhanced note and playlist management
- 🌐 Multiple transport modes: stdio, HTTP, and ASGI
- ☁️ Cloud-ready ASGI application for easy deployment
- 🔧 Customizable middleware support (CORS, authentication, etc.)
- ✅ Comprehensive test coverage with pytest
- 📦 Dependency management with UV
- 🌐 Cross-platform support (Windows, macOS, Linux)

## 🚀 Quick Start

### Installation

Install using UV:
```bash
uv pip install shotgrid-mcp-server
```

### Quick Usage

Once installed, you can start the server directly with:

#### STDIO Transport (Default)

For local MCP clients (like Claude Desktop, Cursor, etc.):
```bash
uvx shotgrid-mcp-server
```

This will start the ShotGrid MCP server with stdio transport, which is the default mode for local MCP clients.

#### HTTP Transport

For web-based deployments or remote access:
```bash
# Start with HTTP transport on default port (8000)
uvx shotgrid-mcp-server http

# Start with custom host and port
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8080

# Start with custom path
uvx shotgrid-mcp-server http --path /api/mcp
```

The HTTP transport uses the Streamable HTTP protocol, which is recommended for web deployments and allows remote clients to connect to your server.

##### Multi-Site Support (HTTP Transport)

HTTP transport mode supports configuring ShotGrid credentials via HTTP request headers, enabling a single server instance to serve multiple ShotGrid sites:

**Server Configuration:**
```bash
# Set default environment variables (required for server startup)
export SHOTGRID_URL="https://default.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="default_script"
export SHOTGRID_SCRIPT_KEY="default_key"

# Start HTTP server
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

**Client Configuration:**

In your MCP client configuration, add custom HTTP headers for each ShotGrid site:

```json
{
  "mcpServers": {
    "shotgrid-site-1": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site1.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "my_script",
          "X-ShotGrid-Script-Key": "abc123..."
        }
      }
    },
    "shotgrid-site-2": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site2.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "another_script",
          "X-ShotGrid-Script-Key": "xyz789..."
        }
      }
    }
  }
}
```

This allows you to configure multiple ShotGrid site instances in the same MCP client, each with different credentials.

**Notes:**
- For stdio transport mode, environment variables (SHOTGRID_URL, SHOTGRID_SCRIPT_NAME, SHOTGRID_SCRIPT_KEY) are still required
- For HTTP transport mode, credentials can be passed via HTTP headers or use environment variables as defaults
- It's recommended to use HTTPS in production to protect API keys

#### Entry Points

The server provides multiple entry points for different deployment scenarios:

| Entry Point | Use Case | Command |
|-------------|----------|---------|
| **CLI** | Local development with Claude Desktop | `shotgrid-mcp-server` or `shotgrid-mcp-server stdio` |
| **HTTP** | Remote access / Web deployments | `shotgrid-mcp-server http --host 0.0.0.0 --port 8000` |
| **ASGI** | Production with uvicorn/gunicorn | `uvicorn shotgrid_mcp_server.asgi:app` |
| **FastMCP Cloud** | Managed cloud deployment | Use `fastmcp_entry.py` as entrypoint |

#### FastMCP Cloud (Recommended)

The easiest way to deploy to production:

1. Sign up at [fastmcp.cloud](https://fastmcp.cloud) and create a new project
2. Connect your GitHub repository (`loonghao/shotgrid-mcp-server`)
3. Configure deployment settings:

   | Setting | Value |
   |---------|-------|
   | **Entrypoint** | `fastmcp_entry.py` |
   | **Requirements File** | `requirements.txt` |

4. Add environment variables in the dashboard:
   - `SHOTGRID_URL` - Your ShotGrid server URL
   - `SHOTGRID_SCRIPT_NAME` - Your script name
   - `SHOTGRID_SCRIPT_KEY` - Your API key

5. Click Deploy and get your server URL (e.g., `https://your-project.fastmcp.app/mcp`)

6. Configure your MCP client:
   ```json
   {
     "mcpServers": {
       "shotgrid-cloud": {
         "url": "https://your-project.fastmcp.app/mcp",
         "transport": { "type": "http" }
       }
     }
   }
   ```

#### ASGI Deployment

For self-hosted production deployments with any ASGI server:

> **Note**: The ASGI application uses **lazy initialization** - the ShotGrid connection is only created when the first request arrives, not during module import.

```bash
# Development mode with Uvicorn
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --reload

# Production mode with multiple workers
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# Using Gunicorn with Uvicorn workers
gunicorn shotgrid_mcp_server.asgi:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4
```

See the [Deployment Guide](docs/deployment.md) for more details including Docker, custom middleware, and other cloud platforms.

### Development Setup

1. Clone the repository:
```bash
git clone https://github.com/loonghao/shotgrid-mcp-server.git
cd shotgrid-mcp-server
```

2. Install development dependencies:
```bash
pip install -r requirements-dev.txt
```

3. Development Commands
All development commands are managed through nox. Check `noxfile.py` for available commands:
```bash
# Run tests
nox -s tests

# Run linting
nox -s lint

# Run type checking
nox -s type_check

# And more...
```

4. Development Server with Hot Reloading

**Note: This requires Node.js to be installed on your system.**

For a better development experience with hot reloading (server automatically restarts when code changes):
```bash
uv run fastmcp dev src/shotgrid_mcp_server/server.py:mcp
```

This will start the server in development mode, and any changes to the code will automatically reload the server.

## ⚙️ Configuration

### Environment Variables

The following environment variables are required:

```bash
SHOTGRID_URL=your_shotgrid_url
SHOTGRID_SCRIPT_NAME=your_script_name
SHOTGRID_SCRIPT_KEY=your_script_key
```

You can set them directly in your shell:

```powershell
# PowerShell
$env:SHOTGRID_URL='your_shotgrid_url'
$env:SHOTGRID_SCRIPT_NAME='your_script_name'
$env:SHOTGRID_SCRIPT_KEY='your_script_key'
```

```bash
# Bash
export SHOTGRID_URL='your_shotgrid_url'
export SHOTGRID_SCRIPT_NAME='your_script_name'
export SHOTGRID_SCRIPT_KEY='your_script_key'
```

Or create a `.env` file in your project directory.

## 🔧 Available Tools

### Core Tools
- `create_entity`: Create ShotGrid entities
- `find_one_entity`: Find a single entity
- `search_entities`: Search for entities with filters
- `update_entity`: Update entity data
- `delete_entity`: Delete entities

### Media Tools
- `download_thumbnail`: Download entity thumbnails
- `upload_thumbnail`: Upload entity thumbnails

### Note & Playlist Tools
- `shotgrid.note.create`: Create notes
- `shotgrid.note.read`: Read note information
- `shotgrid.note.update`: Update note content
- `create_playlist`: Create playlists
- `find_playlists`: Find playlists with filters

### Direct API Access
- `sg.find`: Direct access to ShotGrid API find method
- `sg.create`: Direct access to ShotGrid API create method
- `sg.update`: Direct access to ShotGrid API update method
- `sg.batch`: Direct access to ShotGrid API batch method
- And many more...

## 🤖 AI Prompt Examples

Here are some examples of how to use ShotGrid MCP with AI assistants like Claude:

### Basic Queries

```
Help me find all ShotGrid entities updated in the last 3 months.
```

```
Show me all shots that were updated last week for the "Awesome Project".
```

### Creating and Managing Playlists

```
Create a playlist called "Daily Review - April 21" with all shots updated yesterday by the lighting department.
```

```
Find all playlists created this week.
```

### Notes and Feedback

```
Add a note to SHOT_010 saying "Please adjust the lighting in the background to be more dramatic".
```

### Advanced Workflows

```
Help me summarize the time logs for the "Animation" department this month and generate a chart using echarts to visualize the hours spent.
```

```
Find all shots that were updated yesterday by the lighting team, create a playlist called "Lighting Review - April 21", and notify the director via a note.
```

## 📚 Documentation

For detailed documentation, please refer to the documentation files in the `/docs` directory.

You can also explore the available tools and their parameters directly in Claude Desktop after installing the server.

## 🤝 Contributing

Contributions are welcome! Please ensure:

1. Follow Google Python Style Guide
2. Write tests using pytest
3. Update documentation
4. Use absolute imports
5. Follow the project's coding standards

## 📝 Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

## 📄 License

MIT License - see the [LICENSE](LICENSE) file for details.

## 🔌 MCP Client Configuration

To use the ShotGrid MCP server in your MCP client, add the appropriate configuration to your client's settings.

### Claude Desktop / Anthropic Claude

```json
{
  "mcpServers": {
    "shotgrid-server": {
      "command": "uvx",
      "args": [
        "--python", "3.10",
        "shotgrid-mcp-server"
      ],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "XXX",
        "SHOTGRID_SCRIPT_KEY": "XX",
        "SHOTGRID_URL": "XXXX"
      },
      "disabled": false,
      "alwaysAllow": [
        "search_entities",
        "create_entity",
        "batch_create",
        "find_entity",
        "get_entity_types",
        "update_entity",
        "download_thumbnail",
        "batch_update",
        "delete_entity",
        "batch_delete"
      ]
    }
  }
}
```

### Cursor

```json
// .cursor/mcp.json
{
  "mcpServers": {
    "shotgrid-server": {
      "command": "uvx",
      "args": [
        "shotgrid-mcp-server"
      ],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "XXX",
        "SHOTGRID_SCRIPT_KEY": "XX",
        "SHOTGRID_URL": "XXXX"
      }
    }
  }
}
```

### Windsurf (Codeium)

```json
// MCP configuration
{
  "mcpServers": {
    "shotgrid-server": {
      "command": "uvx",
      "args": [
        "shotgrid-mcp-server"
      ],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "XXX",
        "SHOTGRID_SCRIPT_KEY": "XX",
        "SHOTGRID_URL": "XXXX"
      }
    }
  }
}
```

### Cline (VS Code Extension)

```json
// MCP configuration
{
  "mcpServers": {
    "shotgrid-server": {
      "command": "uvx",
      "args": [
        "shotgrid-mcp-server"
      ],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "XXX",
        "SHOTGRID_SCRIPT_KEY": "XX",
        "SHOTGRID_URL": "XXXX"
      }
    }
  }
}
```

### Visual Studio Code

```json
// .vscode/mcp.json
{
  "inputs": [
    {
      "type": "promptString",
      "id": "shotgrid-script-name",
      "description": "ShotGrid Script Name",
      "password": false
    },
    {
      "type": "promptString",
      "id": "shotgrid-script-key",
      "description": "ShotGrid Script Key",
      "password": true
    },
    {
      "type": "promptString",
      "id": "shotgrid-url",
      "description": "ShotGrid URL",
      "password": false
    }
  ],
  "servers": {
    "shotgrid-server": {
      "type": "stdio",
      "command": "uvx",
      "args": ["shotgrid-mcp-server"],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "${input:shotgrid-script-name}",
        "SHOTGRID_SCRIPT_KEY": "${input:shotgrid-script-key}",
        "SHOTGRID_URL": "${input:shotgrid-url}"
      }
    }
  }
}
```

### VS Code User Settings

```json
// settings.json
{
  "mcp": {
    "shotgrid-server": {
      "type": "stdio",
      "command": "uvx",
      "args": ["shotgrid-mcp-server"],
      "env": {
        "SHOTGRID_SCRIPT_NAME": "XXX",
        "SHOTGRID_SCRIPT_KEY": "XX",
        "SHOTGRID_URL": "XXXX"
      }
    }
  },
  "chat.mcp.discovery.enabled": true
}
```

### 🔑 Credentials Setup

In the configuration examples above, replace the following values with your ShotGrid credentials:
- `SHOTGRID_SCRIPT_NAME`: Your ShotGrid script name
- `SHOTGRID_SCRIPT_KEY`: Your ShotGrid script key
- `SHOTGRID_URL`: Your ShotGrid server URL

### 🛡️ Tool Permissions

The `alwaysAllow` section lists the tools that can be executed without requiring user confirmation. These tools are carefully selected for safe operations. You can customize this list based on your security requirements.

## 🏗️ Architecture

```mermaid
flowchart TB
    subgraph Clients["🤖 MCP Clients"]
        direction LR
        CLAUDE["Claude Desktop"]
        CURSOR["Cursor"]
        VSCODE["VS Code"]
        AI["Other AI"]
    end

    subgraph MCP["⚡ ShotGrid MCP Server"]
        direction LR
        TOOLS["40+ Tools"]
        POOL["Connection Pool"]
        SCHEMA["Schema Cache"]
    end

    subgraph ShotGrid["🎬 ShotGrid API"]
        direction LR
        P["Projects"]
        S["Shots"]
        A["Assets"]
        T["Tasks"]
        N["Notes"]
    end

    Clients -->|"MCP Protocol<br/>stdio / http"| MCP
    MCP -->|"REST API"| ShotGrid

    style Clients fill:#2ecc71,stroke:#27ae60,color:#fff
    style MCP fill:#3498db,stroke:#2980b9,color:#fff
    style ShotGrid fill:#e74c3c,stroke:#c0392b,color:#fff
```