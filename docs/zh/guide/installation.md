# 安装

## 包安装

### 使用 uv（推荐）

```bash
uv pip install shotgrid-mcp-server
```

### 使用 pip

```bash
pip install shotgrid-mcp-server
```

### 从源码安装

```bash
git clone https://github.com/loonghao/shotgrid-mcp-server.git
cd shotgrid-mcp-server
pip install -e .
```

## MCP 客户端配置

### Claude Desktop

添加到 Claude Desktop 配置文件：

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

添加到 MCP 设置：

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

### HTTP 传输（远程）

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
