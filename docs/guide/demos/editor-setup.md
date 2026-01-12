# Editor Setup

Configure ShotGrid MCP Server in your code editor.

## Demo

![Configure ShotGrid MCP in Code Editor](/00-codebuddy-config-shotgrid-mcp.gif)

## Steps

1. Open your MCP-compatible editor (Claude Desktop, Cursor, VS Code, etc.)
2. Navigate to MCP settings
3. Add the ShotGrid MCP server configuration
4. Set your ShotGrid credentials
5. Restart the editor to apply changes

## Configuration Example

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

## Verify Connection

After configuration, you can verify the connection by asking your AI assistant:

> "List all projects in ShotGrid"

If configured correctly, you should see a list of your ShotGrid projects.
