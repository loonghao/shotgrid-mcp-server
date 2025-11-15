"""Delete tools for ShotGrid MCP server.

This module contains tools for deleting entities in ShotGrid.
"""

from typing import Any  # noqa

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.custom_types import EntityType


def register_delete_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register delete tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("entity_delete")
    def delete_entity(entity_type: EntityType, entity_id: int) -> None:
        """Delete an entity in ShotGrid.

        Args:
            entity_type: Type of entity to delete.
            entity_id: ID of entity to delete.

        Raises:
            ToolError: If the delete operation fails.
        """
        try:
            # First check if the entity exists
            entity = sg.find_one(entity_type, [["id", "is", entity_id]])
            if entity is None:
                raise ToolError(f"Entity {entity_type} with ID {entity_id} not found")

            # Then try to delete it
            result = sg.delete(entity_type, entity_id)
            if result is False:  # ShotGrid API returns False on failure
                raise ToolError(f"Failed to delete {entity_type} with ID {entity_id}")
            return None
        except Exception as err:
            handle_error(err, operation="delete_entity")
            raise  # This is needed to satisfy the type checker
