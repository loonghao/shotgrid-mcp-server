# 部署指南

本指南介绍如何在各种环境中部署 ShotGrid MCP Server。

## 目录

- [ASGI 部署](#asgi-部署)
- [Stdio 模式（本地）](#stdio-模式本地)
- [HTTP 模式（远程）](#http-模式远程)
- [云平台部署](#云平台部署)
- [生产环境最佳实践](#生产环境最佳实践)

## ASGI 部署

ShotGrid MCP Server 提供了标准的 ASGI 应用，可以部署到任何 ASGI 服务器。

### 使用默认 ASGI 应用

最简单的部署方式是使用预配置的 ASGI 应用：

```bash
# 开发模式（自动重载）
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --reload

# 生产模式（多进程）
uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000 --workers 4

# 使用 Gunicorn（生产环境推荐）
gunicorn shotgrid_mcp_server.asgi:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker

# 使用 Hypercorn
hypercorn shotgrid_mcp_server.asgi:app --bind 0.0.0.0:8000
```

### 自定义 ASGI 应用（带中间件）

生产环境部署时，可以创建自定义 ASGI 应用并添加中间件：

**app.py:**
```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

# 为你的域名配置 CORS
cors_middleware = Middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# 创建带中间件的应用
app = create_asgi_app(
    middleware=[cors_middleware],
    path="/mcp"
)
```

部署：
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Stdio 模式（本地）

Stdio 模式专为本地 MCP 客户端设计，如 Claude Desktop、Cursor 等。

### 使用 UV

```bash
# 使用 uvx 运行（推荐）
uvx shotgrid-mcp-server

# 或者安装后运行
uv pip install shotgrid-mcp-server
shotgrid-mcp-server stdio
```

### 环境配置

创建 `.env` 文件或设置环境变量：

```bash
export SHOTGRID_URL="https://your-site.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="your_script_name"
export SHOTGRID_SCRIPT_KEY="your_api_key"
```

### Claude Desktop 配置

在 Claude Desktop 配置文件中添加（macOS 路径：`~/Library/Application Support/Claude/claude_desktop_config.json`）：

```json
{
  "mcpServers": {
    "shotgrid": {
      "command": "uvx",
      "args": ["shotgrid-mcp-server"],
      "env": {
        "SHOTGRID_URL": "https://your-site.shotgunstudio.com",
        "SHOTGRID_SCRIPT_NAME": "your_script_name",
        "SHOTGRID_SCRIPT_KEY": "your_api_key"
      }
    }
  }
}
```

## HTTP 模式（远程）

HTTP 模式专为 Web 部署和远程访问设计。

### 基本使用

```bash
# 默认设置（127.0.0.1:8000/mcp）
shotgrid-mcp-server http

# 自定义主机和端口
shotgrid-mcp-server http --host 0.0.0.0 --port 8080

# 自定义路径
shotgrid-mcp-server http --path /api/mcp
```

### 多站点支持

HTTP 模式支持通过 HTTP 请求头配置多个 ShotGrid 站点：

**服务器设置：**
```bash
# 设置默认凭据（启动时必需）
export SHOTGRID_URL="https://default.shotgunstudio.com"
export SHOTGRID_SCRIPT_NAME="default_script"
export SHOTGRID_SCRIPT_KEY="default_key"

# 启动服务器
shotgrid-mcp-server http --host 0.0.0.0 --port 8000
```

**客户端配置：**

为每个 ShotGrid 站点在 MCP 客户端中配置自定义请求头：

```json
{
  "mcpServers": {
    "shotgrid-site-1": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site1.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "site1_script",
          "X-ShotGrid-Script-Key": "site1_key"
        }
      }
    },
    "shotgrid-site-2": {
      "url": "http://your-server:8000/mcp",
      "transport": {
        "type": "http",
        "headers": {
          "X-ShotGrid-URL": "https://site2.shotgunstudio.com",
          "X-ShotGrid-Script-Name": "site2_script",
          "X-ShotGrid-Script-Key": "site2_key"
        }
      }
    }
  }
}
```

## 云平台部署

### FastMCP Cloud

[FastMCP Cloud](https://fastmcp.cloud) 是将 MCP 服务器部署到生产环境的最简单方式。

#### 快速设置

1. 在 [fastmcp.cloud](https://fastmcp.cloud) **注册**并创建新项目
2. **连接**您的 GitHub 仓库
3. **配置**部署设置：

| 设置 | 值 |
|------|-----|
| **入口文件 (Entrypoint)** | `fastmcp_entry.py` |
| **依赖文件 (Requirements File)** | `requirements.txt` |

4. 在 FastMCP Cloud 控制台中**设置环境变量**：
   - `SHOTGRID_URL`：您的 ShotGrid 服务器 URL
   - `SHOTGRID_SCRIPT_NAME`：您的脚本名称
   - `SHOTGRID_SCRIPT_KEY`：您的 API 密钥

5. **部署**并获取服务器 URL（例如：`https://your-project.fastmcp.app/mcp`）

#### 工作原理

服务器导出一个模块级的 `mcp` 实例，FastMCP Cloud 会自动发现它：

```python
# src/shotgrid_mcp_server/server.py
from fastmcp import FastMCP

# 用于 FastMCP Cloud 的模块级 MCP 实例
mcp: FastMCP = create_server(lazy_connection=True, preload_schema=False)
```

#### 客户端配置

部署完成后，配置您的 MCP 客户端使用云端点：

```json
{
  "mcpServers": {
    "shotgrid-cloud": {
      "url": "https://your-project.fastmcp.app/mcp",
      "transport": {
        "type": "http"
      }
    }
  }
}
```

#### 优势

- **零基础设施**：无需管理服务器
- **自动扩展**：自动处理流量高峰
- **内置监控**：在控制台查看日志和指标
- **轻松更新**：推送到 GitHub 自动部署

### Docker 部署

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 安装 uv
RUN pip install uv

# 复制项目文件
COPY pyproject.toml uv.lock ./
COPY src ./src

# 安装依赖
RUN uv pip install --system -e .

# 暴露端口
EXPOSE 8000

# 使用 uvicorn 运行
CMD ["uvicorn", "shotgrid_mcp_server.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
```

构建和运行：
```bash
docker build -t shotgrid-mcp-server .
docker run -p 8000:8000 \
    -e SHOTGRID_URL="https://your-site.shotgunstudio.com" \
    -e SHOTGRID_SCRIPT_NAME="your_script" \
    -e SHOTGRID_SCRIPT_KEY="your_key" \
    shotgrid-mcp-server
```

### Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  shotgrid-mcp:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SHOTGRID_URL=${SHOTGRID_URL}
      - SHOTGRID_SCRIPT_NAME=${SHOTGRID_SCRIPT_NAME}
      - SHOTGRID_SCRIPT_KEY=${SHOTGRID_SCRIPT_KEY}
    restart: unless-stopped
```

运行：
```bash
docker-compose up -d
```

### Kubernetes

**deployment.yaml:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: shotgrid-mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: shotgrid-mcp-server
  template:
    metadata:
      labels:
        app: shotgrid-mcp-server
    spec:
      containers:
      - name: shotgrid-mcp-server
        image: shotgrid-mcp-server:latest
        ports:
        - containerPort: 8000
        env:
        - name: SHOTGRID_URL
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: url
        - name: SHOTGRID_SCRIPT_NAME
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: script-name
        - name: SHOTGRID_SCRIPT_KEY
          valueFrom:
            secretKeyRef:
              name: shotgrid-credentials
              key: script-key
---
apiVersion: v1
kind: Service
metadata:
  name: shotgrid-mcp-server
spec:
  selector:
    app: shotgrid-mcp-server
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

## 生产环境最佳实践

### 安全性

1. **使用 HTTPS**：始终在反向代理后部署并启用 SSL/TLS
2. **限制 CORS**：配置具体的允许源而不是使用 `*`
3. **保护凭据**：使用密钥管理（环境变量、vault 等）
4. **速率限制**：添加速率限制中间件防止滥用

### 性能

1. **多进程部署**：使用多个工作进程提高并发能力
2. **连接池**：服务器默认使用连接池
3. **缓存**：考虑为频繁访问的数据添加缓存中间件

### 监控

1. **日志**：配置结构化日志便于观察
2. **指标**：添加指标收集（Prometheus、DataDog 等）
3. **健康检查**：实现健康检查端点

### 生产环境示例

**带生产中间件的 app.py:**
```python
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from shotgrid_mcp_server.asgi import create_asgi_app

middleware = [
    Middleware(
        CORSMiddleware,
        allow_origins=["https://yourdomain.com"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    ),
    Middleware(GZipMiddleware, minimum_size=1000),
]

app = create_asgi_app(middleware=middleware, path="/mcp")
```

**使用 Gunicorn 部署:**
```bash
gunicorn app:app \
    -k uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --access-logfile - \
    --error-logfile - \
    --log-level info
```

### 反向代理（Nginx）

**nginx.conf:**
```nginx
upstream shotgrid_mcp {
    server localhost:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location /mcp {
        proxy_pass http://shotgrid_mcp;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 故障排查

### 连接问题

如果遇到连接问题：

1. 验证凭据是否正确设置
2. 检查防火墙规则
3. 确保 ShotGrid 服务器可访问
4. 查看服务器日志

### 性能问题

性能问题时：

1. 增加工作进程数
2. 启用连接池
3. 添加缓存层
4. 监控资源使用

### 多站点问题

使用多站点支持时：

1. 验证请求头是否正确发送
2. 检查请求头名称是否完全匹配
3. 确保每个站点凭据有效
4. 查看服务器日志中的请求头值
