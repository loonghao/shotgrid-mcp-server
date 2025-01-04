# ShotGrid MCP Server

A Model Context Protocol (MCP) server implementation for ShotGrid using fastmcp. This server provides a standardized interface for interacting with ShotGrid through MCP tools.

## Features

- Create, read, update, and delete ShotGrid entities
- Download thumbnails and attachments
- Connection pooling for efficient resource management
- Comprehensive test coverage

## Installation

```bash
uv pip install shotgrid-mcp-server
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/loonghao/shotgrid-mcp-server.git
cd shotgrid-mcp-server
```

2. Install development dependencies:
```bash
uv pip install -e ".[test]"
```

3. Run tests:
```bash
python -m nox -s tests
```

4. Start development server:
```bash
uv run fastmcp dev src/shotgrid_mcp_server/server.py
```

## Environment Variables

Create a `.env` file in the project root with the following variables:
```bash
SHOTGRID_URL=your_shotgrid_url
SCRIPT_NAME=your_script_name
SCRIPT_KEY=your_script_key
```

## Version

Current version: 0.0.1

## License

MIT License