# 🎯 ShotGrid MCP Server

English | [简体中文](README_zh.md)

<div align="center">

A high-performance ShotGrid Model Context Protocol (MCP) server implementation based on fastmcp

[![Python Version](https://img.shields.io/pypi/pyversions/shotgrid-mcp-server.svg)](https://pypi.org/project/shotgrid-mcp-server/)
[![License](https://img.shields.io/github/license/loonghao/shotgrid-mcp-server.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/shotgrid-mcp-server.svg)](https://badge.fury.io/py/shotgrid-mcp-server)
[![Downloads](https://pepy.tech/badge/shotgrid-mcp-server)](https://pepy.tech/project/shotgrid-mcp-server)

</div>

## ✨ Features

- 🚀 High-performance implementation based on fastmcp
- 🛠 Complete CRUD operation toolset
- 🖼 Dedicated thumbnail download/upload tools
- 🔄 Efficient connection pool management
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

## ⚙️ Configuration

### Environment Variables

Create a `.env` file with the following variables:
```bash
SHOTGRID_URL=your_shotgrid_url
SCRIPT_NAME=your_script_name
SCRIPT_KEY=your_script_key
```

## 🔧 Available Tools

- `create`: Create ShotGrid entities
- `read`: Read entity information
- `update`: Update entity data
- `delete`: Delete entities
- `download_thumbnail`: Download entity thumbnails
- `upload_thumbnail`: Upload entity thumbnails

## 📚 API Documentation

For detailed API documentation, please refer to the documentation files in the `/docs` directory.

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
        "SCRIPT_NAME": "XXX",
        "SCRIPT_KEY": "XX",
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
- `SCRIPT_NAME`: Your ShotGrid script name
- `SCRIPT_KEY`: Your ShotGrid script key
- `SHOTGRID_URL`: Your ShotGrid server URL

### 🛡️ Tool Permissions

The `alwaysAllow` section lists the tools that can be executed without requiring user confirmation. These tools are carefully selected for safe operations.