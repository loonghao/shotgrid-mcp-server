"""Update tools for ShotGrid MCP server.

This module contains tools for updating entities in ShotGrid.
"""

from typing import Any, Dict

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType


def register_update_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register update tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("entity_update")
    def update_entity(
        entity_type: EntityType,
        entity_id: int,
        data: Dict[str, Any],
    ) -> None:
        """Update an entity in ShotGrid.

        Args:
            entity_type: Type of entity to update.
            entity_id: ID of entity to update.
            data: Data to update on the entity.

        Raises:
            ToolError: If the update operation fails.
        """
        try:
            result = sg.update(entity_type, entity_id, data)
            if result is None:
                raise ToolError(f"Failed to update {entity_type} with ID {entity_id}")
            return None
        except Exception as err:
            handle_error(err, operation="update_entity")
            raise  # This is needed to satisfy the type checker
