"""Read tools for ShotGrid MCP server.

This module contains tools for reading entities from ShotGrid.
"""

from typing import Any, Dict

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType


def register_read_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register read tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("schema_get")
    def get_schema(entity_type: EntityType) -> Dict[str, Any]:
        """Get schema for an entity type.

        Args:
            entity_type: Type of entity to get schema for.

        Returns:
            Dict[str, Any]: Entity schema.

        Raises:
            ToolError: If the schema retrieval fails.
        """
        try:
            result = sg.schema_field_read(entity_type)
            if result is None:
                raise ToolError(f"Failed to read schema for {entity_type}")

            # Add type field to schema
            result["type"] = {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": entity_type}},
            }

            return {"fields": dict(result)}  # Ensure we return Dict[str, Any]
        except Exception as err:
            handle_error(err, operation="get_schema")
            raise  # This is needed to satisfy the type checker
