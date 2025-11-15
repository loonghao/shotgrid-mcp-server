"""Tools for ShotGrid MCP server.

This package contains all the tools that can be registered with the ShotGrid MCP server.
Each module in this package contains a set of related tools.
"""

from typing import Any  # noqa

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.schema_resources import register_schema_resources
from shotgrid_mcp_server.tools.api_tools import register_api_tools
from shotgrid_mcp_server.tools.create_tools import register_create_tools
from shotgrid_mcp_server.tools.delete_tools import register_delete_tools
from shotgrid_mcp_server.tools.note_tools import register_note_tools
from shotgrid_mcp_server.tools.playlist_tools import register_playlist_tools
from shotgrid_mcp_server.tools.read_tools import register_read_tools
from shotgrid_mcp_server.tools.search_tools import register_search_tools
from shotgrid_mcp_server.tools.thumbnail_tools import register_thumbnail_tools
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.tools.update_tools import register_update_tools
from shotgrid_mcp_server.tools.vendor_tools import register_vendor_tools


def register_all_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register all tools and resources with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Register all tools
    register_create_tools(server, sg)
    register_read_tools(server, sg)
    register_update_tools(server, sg)
    register_delete_tools(server, sg)
    register_search_tools(server, sg)
    register_thumbnail_tools(server, sg)

    # Register entity-specific tools
    register_note_tools(server, sg)
    register_playlist_tools(server, sg)
    register_vendor_tools(server, sg)

    # Register direct API tools
    register_api_tools(server, sg)

    # Register schema-related MCP resources
    register_schema_resources(server, sg)
