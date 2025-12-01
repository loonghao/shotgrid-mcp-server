"""FastMCP Cloud entry point.

This module is specifically designed for FastMCP Cloud deployment.
It handles the case where the package is not installed but the source
code is available in the container.

FastMCP Cloud Configuration:
    Entrypoint: fastmcp_entry.py
    Requirements File: requirements.txt

HTTP Headers for Multi-Site Support:
    X-ShotGrid-URL:         ShotGrid server URL for this request
    X-ShotGrid-Script-Name: Script name for this request
    X-ShotGrid-Script-Key:  API key for this request

Environment Variables (fallback):
    SHOTGRID_URL:         Your ShotGrid server URL
    SHOTGRID_SCRIPT_NAME: Your ShotGrid script name
    SHOTGRID_SCRIPT_KEY:  Your ShotGrid script key
"""

# Import built-in modules
import os
import sys

# Add src directory to Python path for uninstalled package
_current_dir = os.path.dirname(os.path.abspath(__file__))
_src_dir = os.path.join(_current_dir, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Now we can import the server module
from shotgrid_mcp_server.server import create_server

# Create MCP server with lazy connection for HTTP mode
# Credentials will be provided via HTTP headers or environment variables
mcp = create_server(lazy_connection=True, preload_schema=False)

# Export the HTTP ASGI app for deployment
# This enables multi-site support through HTTP headers
app = mcp.http_app(path="/mcp")

# Alternative name
server = mcp

