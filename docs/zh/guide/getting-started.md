# 快速开始

ShotGrid MCP Server 使 Claude、Cursor、VS Code Copilot 等 AI 助手能够直接与您的 ShotGrid（Flow Production Tracking）数据交互。

## 前置要求

- Python 3.10+
- 具有 API 访问权限的 ShotGrid 账户
- 支持 MCP 的客户端（Claude Desktop、Cursor、VS Code 等）

## 快速安装

```bash
# 使用 uv（推荐）
uv pip install shotgrid-mcp-server

# 或使用 pip
pip install shotgrid-mcp-server
```

## 配置

设置 ShotGrid 凭据为环境变量：

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_script_key"
```

## 运行服务器

### stdio 传输（默认）

适用于 Claude Desktop、Cursor 等本地 MCP 客户端：

```bash
uvx shotgrid-mcp-server
```

### HTTP 传输

适用于远程访问：

```bash
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

## 下一步

- [安装指南](/zh/guide/installation) - 详细安装说明
- [配置](/zh/guide/configuration) - 高级配置选项
- [演示](/zh/guide/demos/editor-setup) - 查看实际效果
