# 配置

## 环境变量

| 变量 | 必需 | 描述 |
|------|------|------|
| `SHOTGRID_URL` | 是 | 您的 ShotGrid 站点 URL |
| `SHOTGRID_SCRIPT_NAME` | 是 | API 脚本名称 |
| `SHOTGRID_SCRIPT_KEY` | 是 | API 脚本密钥 |
| `SHOTGRID_HTTP_PROXY` | 否 | HTTP 代理 URL |
| `SHOTGRID_HTTPS_PROXY` | 否 | HTTPS 代理 URL |

## 配置示例

```bash
# 必需
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_script_key"

# 可选 - 代理设置
export SHOTGRID_HTTP_PROXY="http://proxy:8080"
export SHOTGRID_HTTPS_PROXY="https://proxy:8080"
```

## 传输选项

### stdio（默认）

最适合 Claude Desktop 和 Cursor 等本地 MCP 客户端。

```bash
uvx shotgrid-mcp-server
```

### HTTP

最适合远程访问和共享环境。

```bash
uvx shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

### ASGI

最适合使用 uvicorn 或 gunicorn 的生产部署。

```bash
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000
```
