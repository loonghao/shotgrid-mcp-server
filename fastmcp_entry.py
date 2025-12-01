"""FastMCP Cloud entry point.

This module is specifically designed for FastMCP Cloud deployment.
It handles the case where the package is not installed but the source
code is available in the container.

FastMCP Cloud Configuration:
    Entrypoint: fastmcp_entry.py
    Requirements File: requirements.txt

Environment Variables:
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

# Module-level MCP instance for FastMCP Cloud
# FastMCP Cloud looks for 'mcp', 'server', or 'app' in the entrypoint file
mcp = create_server(lazy_connection=True, preload_schema=False)

# Alternative names that FastMCP Cloud might look for
server = mcp
app = mcp

