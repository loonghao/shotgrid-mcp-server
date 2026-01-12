# 编辑器配置

在代码编辑器中配置 ShotGrid MCP Server。

## 演示

![代码编辑器配置 ShotGrid MCP](/00-codebuddy-config-shotgrid-mcp.gif)

## 步骤

1. 打开支持 MCP 的编辑器（Claude Desktop、Cursor、VS Code 等）
2. 导航到 MCP 设置
3. 添加 ShotGrid MCP 服务器配置
4. 设置您的 ShotGrid 凭据
5. 重启编辑器以应用更改

## 配置示例

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

## 验证连接

配置完成后，您可以通过询问 AI 助手来验证连接：

> "列出 ShotGrid 中的所有项目"

如果配置正确，您应该能看到 ShotGrid 项目列表。
