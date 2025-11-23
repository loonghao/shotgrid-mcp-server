"""Delete tools for ShotGrid MCP server.

This module contains tools for deleting entities in ShotGrid.
"""

from typing import Any, Dict  # noqa

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.response_models import EntityDeleteResult
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType


def register_delete_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register delete tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("entity_delete")
    def delete_entity(entity_type: EntityType, entity_id: int) -> Dict[str, Any]:
        """Delete (retire) an entity in ShotGrid.

        **IMPORTANT: This operation cannot be easily undone through the API.**
        Retired entities can only be restored through the ShotGrid web interface.

        **When to use this tool:**
        - You need to remove a shot that is no longer needed
        - You want to delete a task that was created by mistake
        - You need to retire a version that should not be visible
        - You want to clean up test data
        - You need to soft-delete an entity (mark as retired)

        **When NOT to use this tool:**
        - To update an entity - Use `update_entity` instead
        - To delete multiple entities at once - Use `batch_operations` instead
        - Entity type cannot be deleted (e.g., Project, HumanUser)
        - You're not sure if deletion is needed - Ask for confirmation first

        **Common use cases:**
        - Remove a shot that is no longer needed
        - Delete a task that was created by mistake
        - Retire a version that should not be visible
        - Clean up test data

        **Note:** In ShotGrid, deletion is typically a "soft delete" (retirement) -
        the entity is marked as retired but not permanently removed from the database.
        For batch deletions, use `batch_operations` instead.

        Args:
            entity_type: The type of entity to delete (e.g., "Shot", "Task", "Version").
                        Must be a valid ShotGrid entity type.

                        Note: Some entity types cannot be deleted (e.g., "Project", "HumanUser").

            entity_id: The ID of the entity to delete.
                      You can find entity IDs using search tools like `search_entities`
                      or `find_one_entity`.

        Returns:
            Dictionary containing:
            - success: True if deletion was successful
            - entity_type: The type of entity deleted
            - entity_id: The ID of the deleted entity
            - message: Confirmation message
            - schema_resources: Links to schema information

            Example:
            {
                "success": True,
                "entity_type": "Shot",
                "entity_id": 1234,
                "message": "Successfully deleted Shot with ID 1234",
                "schema_resources": {
                    "entities": "shotgrid://schema/entities"
                }
            }

        Raises:
            ToolError: If entity doesn't exist, cannot be deleted, or the ShotGrid API
                      returns an error.

        Examples:
            Delete a shot:
            {
                "entity_type": "Shot",
                "entity_id": 1234
            }

            Delete a task:
            {
                "entity_type": "Task",
                "entity_id": 5678
            }

            Delete a version:
            {
                "entity_type": "Version",
                "entity_id": 9012
            }

        Entity Types That Cannot Be Deleted:
            - Project: Projects cannot be deleted via API
            - HumanUser: Users cannot be deleted via API
            - ApiUser: API users cannot be deleted via API
            - Department: Departments cannot be deleted via API

        Note:
            - This is a SOFT DELETE (retirement) - the entity is not permanently removed
            - Retired entities are hidden from most queries by default
            - Retired entities can be restored through the ShotGrid web interface
            - Some entities cannot be deleted if they have dependencies (e.g., a Shot with Tasks)
            - The tool verifies the entity exists before attempting deletion
            - Use with caution - this operation cannot be undone through the API

        Best Practices:
            - Always verify the entity_id before deletion
            - Consider updating the entity's status instead of deleting
            - Use search tools to confirm you're deleting the correct entity
            - For production data, consider archiving instead of deleting
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

            # Return structured result
            return EntityDeleteResult(
                success=True,
                entity_type=entity_type,
                entity_id=entity_id,
                message=f"Successfully deleted {entity_type} with ID {entity_id}",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="delete_entity")
            raise  # This is needed to satisfy the type checker
