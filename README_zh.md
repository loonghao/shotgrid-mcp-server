# 🎯 ShotGrid MCP Server

[English](README.md) | 简体中文

<div align="center ">
基于fastmcp的高性能ShotGrid Model Context Protocol (MCP) 服务器实现

[![Python Version](https://img.shields.io/pypi/pyversions/shotgrid-mcp-server.svg)](https://pypi.org/project/shotgrid-mcp-server/)
[![License](https://img.shields.io/github/license/loonghao/shotgrid-mcp-server.svg)](LICENSE)
[![PyPI version](https://badge.fury.io/py/shotgrid-mcp-server.svg)](https://badge.fury.io/py/shotgrid-mcp-server)
[![Downloads](https://pepy.tech/badge/shotgrid-mcp-server)](https://pepy.tech/project/shotgrid-mcp-server)

</div>

## ✨ 特性

- 🚀 基于fastmcp的高性能实现
- 🛠 完整的CRUD操作工具集
- 🖼 专门的缩略图上传/下载工具
- 🔄 高效的连接池管理
- ✅ 使用pytest的全面测试覆盖
- 📦 使用UV进行依赖管理
- 🌐 跨平台支持 (Windows, macOS, Linux)

## 🎯 快速演示

这是使用 ShotGrid MCP 服务器查询实体的简单示例：

![ShotGrid MCP 服务器演示](images/sg-mcp.gif)

## 🚀 快速开始

### 安装

使用UV安装：
```bash
uv pip install shotgrid-mcp-server
```

### 开发环境设置

1. 克隆仓库：
```bash
git clone https://github.com/loonghao/shotgrid-mcp-server.git
cd shotgrid-mcp-server
```

2. 安装开发依赖：
```bash
pip install -r requirements-dev.txt
```

3. 开发命令
所有开发命令通过nox管理。查看`noxfile.py`获取可用命令：
```bash
# 运行测试
nox -s tests

# 运行代码检查
nox -s lint

# 运行类型检查
nox -s type_check

# 更多命令...
```

### 🔧 开发

#### 环境设置

1. 设置环境变量：
```powershell
$env:SHOTGRID_URL='你的_shotgrid_url'
$env:SHOTGRID_SCRIPT_NAME='你的_script_name'
$env:SHOTGRID_SCRIPT_KEY='你的_script_key'
```

2. 运行开发服务器：
```bash
uv run fastmcp dev src\shotgrid_mcp_server\server.py:app
```
服务器将以开发模式启动，并启用热重载功能。

## ⚙️ 配置

### 环境变量

创建`.env`文件并配置以下变量：
```bash
SHOTGRID_URL=your_shotgrid_url
SHOTGRID_SCRIPT_NAME=your_script_name
SHOTGRID_SCRIPT_KEY=your_script_key
```

## 🔧 可用工具

- `create`: 创建ShotGrid实体
- `read`: 读取实体信息
- `update`: 更新实体数据
- `delete`: 删除实体
- `download_thumbnail`: 下载实体缩略图
- `upload_thumbnail`: 上传实体缩略图

## 📚 API文档

详细的API文档请参考`/docs`目录下的文档文件。

## 🤝 贡献指南

欢迎提交贡献！请确保：

1. 遵循Google Python代码风格指南
2. 使用pytest编写测试
3. 更新文档
4. 使用绝对导入
5. 遵循项目代码规范

## 📝 版本历史

查看[CHANGELOG.md](CHANGELOG.md)了解详细的版本历史。

## 📄 许可证

MIT许可证 - 查看[LICENSE](LICENSE)文件了解详情。

## 🔌 MCP客户端配置

在MCP客户端中使用ShotGrid MCP服务器时，需要在客户端设置中添加以下配置：

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

### 🔑 凭证设置

请将以下值替换为您的ShotGrid凭证：
- `SHOTGRID_SCRIPT_NAME`: 您的ShotGrid脚本名称
- `SHOTGRID_SCRIPT_KEY`: 您的ShotGrid脚本密钥
- `SHOTGRID_URL`: 您的ShotGrid服务器URL

### 🛡️ 工具权限

`alwaysAllow`部分列出了可以无需用户确认即可执行的工具。这些工具经过精心选择，确保操作安全。
