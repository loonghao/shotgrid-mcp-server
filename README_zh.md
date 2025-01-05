# 🎯 ShotGrid MCP Server

[English](README.md) | 简体中文

<div align="center">

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

## ⚙️ 配置

### 环境变量

创建`.env`文件并配置以下变量：
```bash
SHOTGRID_URL=your_shotgrid_url
SCRIPT_NAME=your_script_name
SCRIPT_KEY=your_script_key
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

MIT License - 查看[LICENSE](LICENSE)文件了解详细信息。
