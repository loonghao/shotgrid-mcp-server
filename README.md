# 🎯 ShotGrid MCP Server

English | [简体中文](README_zh.md)

<div align="center">

A high-performance ShotGrid Model Context Protocol (MCP) server implementation based on fastmcp

[![Python Version](https://img.shields.io/pypi/pyversions/shotgrid-mcp-server.svg)](https://pypi.org/project/shotgrid-mcp-server/)
[![License](https://img.shields.io/github/license/loonghao/shotgrid-mcp-server.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/shotgrid-mcp-server.svg)](https://badge.fury.io/py/shotgrid-mcp-server)
[![Downloads](https://pepy.tech/badge/shotgrid-mcp-server)](https://pepy.tech/project/shotgrid-mcp-server)

</div>

## 🎬 Demo

Here's a simple example of querying entities using the ShotGrid MCP server:

![ShotGrid MCP Server Demo](images/sg-mcp.gif)

## ✨ Features

- 🚀 High-performance implementation based on fastmcp
- 🛠 Complete CRUD operation toolset
- 🖼 Dedicated thumbnail download/upload tools
- 🔄 Efficient connection pool management
- 🔌 Direct ShotGrid API access through MCP tools
- 📝 Enhanced note and playlist management
- ✅ Comprehensive test coverage with pytest
- 📦 Dependency management with UV
- 🌐 Cross-platform support (Windows, macOS, Linux)

## 🚀 Quick Start

### Installation

Install using UV:
```bash
uv pip install shotgrid-mcp-server
```

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



## Development

#### Environment Setup

1. Set up environment variables:
```powershell
$env:SHOTGRID_URL='your_shotgrid_url'
$env:SHOTGRID_SCRIPT_NAME='your_script_name'
$env:SHOTGRID_SCRIPT_KEY='your_script_key'
```

2. Run the development server:
```bash
uv run fastmcp dev src\shotgrid_mcp_server\server.py:app
```
The server will start in development mode with hot reloading enabled.

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:
```bash
SHOTGRID_URL=your_shotgrid_url
SHOTGRID_SCRIPT_NAME=your_script_name
SHOTGRID_SCRIPT_KEY=your_script_key
```

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

## 📚 API Documentation

For detailed API documentation, please refer to the documentation files in the `/docs` directory.

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

To use the ShotGrid MCP server in your MCP client, add the following configuration to your client's settings:

```json
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

### 🔑 Credentials Setup

Replace the following values with your ShotGrid credentials:
- `SHOTGRID_SCRIPT_NAME`: Your ShotGrid script name
- `SHOTGRID_SCRIPT_KEY`: Your ShotGrid script key
- `SHOTGRID_URL`: Your ShotGrid server URL

### 🛡️ Tool Permissions

The `alwaysAllow` section lists the tools that can be executed without requiring user confirmation. These tools are carefully selected for safe operations. You can customize this list based on your security requirements.