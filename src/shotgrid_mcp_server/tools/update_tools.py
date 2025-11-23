"""Update tools for ShotGrid MCP server.

This module contains tools for updating entities in ShotGrid.
"""

import logging
from typing import Any, Dict, cast

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.response_models import EntityUpdateResult
from shotgrid_mcp_server.schema_validator import get_schema_validator
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import EntityDict, FastMCPType

logger = logging.getLogger(__name__)


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
    ) -> Dict[str, Any]:
        """Update an existing entity in ShotGrid.

        **When to use this tool:**
        - You need to modify field values on an existing entity
        - You want to update task status or assignment
        - You need to change shot/asset properties
        - You want to update version status or description
        - You need to link entities together
        - You want to clear field values

        **When NOT to use this tool:**
        - To create a new entity - Use `create_entity` instead
        - To update multiple entities at once - Use `batch_operations` instead
        - To delete an entity - Use `delete_entity` instead
        - Entity doesn't exist yet - Use `create_entity` first

        **Common use cases:**
        - Update task status to "In Progress" or "Complete"
        - Assign a task to a different artist
        - Update shot description or frame range
        - Change version status to "Approved"
        - Update entity links (e.g., link a version to a different shot)
        - Clear field values by setting them to None

        **Note:** Only the fields specified in `data` will be updated; other fields remain unchanged.
        For updating multiple entities at once, use `batch_operations` instead.

        Args:
            entity_type: The type of entity to update (e.g., "Shot", "Task", "Version").
                        Must be a valid ShotGrid entity type.

            entity_id: The ID of the entity to update.
                      You can find entity IDs using search tools like `search_entities`
                      or `find_one_entity`.

            data: Dictionary of field values to update.
                  Only include fields you want to change.

                  Update task status:
                  {
                      "sg_status_list": "ip"
                  }

                  Reassign task to different artist:
                  {
                      "task_assignees": [{"type": "HumanUser", "id": 99}]
                  }

                  Update shot frame range:
                  {
                      "sg_cut_in": 1001,
                      "sg_cut_out": 1048,
                      "sg_cut_duration": 48
                  }

                  Update version status and description:
                  {
                      "sg_status_list": "rev",
                      "description": "Ready for client review"
                  }

                  Clear a field (set to null):
                  {
                      "description": None
                  }

                  Update entity reference:
                  {
                      "entity": {"type": "Shot", "id": 456}
                  }

        Returns:
            Dictionary containing:
            - entity: The updated entity with all current field values
            - entity_type: The type of entity updated
            - schema_resources: Links to schema information

            Example:
            {
                "entity": {
                    "type": "Task",
                    "id": 5678,
                    "content": "Animation",
                    "sg_status_list": "ip",
                    "task_assignees": [{"type": "HumanUser", "id": 99, "name": "John Doe"}],
                    "entity": {"type": "Shot", "id": 789, "name": "SH001"},
                    "updated_at": "2025-01-15T14:20:00Z",
                    ...
                },
                "entity_type": "Task",
                "schema_resources": {
                    "entities": "shotgrid://schema/entities",
                    "statuses": "shotgrid://schema/statuses"
                }
            }

        Common Status Codes:
            - wtg: Waiting to Start
            - rdy: Ready to Start
            - ip: In Progress
            - rev: Pending Review
            - fin: Final
            - omt: Omitted

        Raises:
            ToolError: If entity doesn't exist, fields are invalid or non-editable,
                      or the ShotGrid API returns an error.

        Note:
            - Only editable fields can be updated
            - System fields (id, type, created_at) cannot be modified
            - Entity references must use {"type": "EntityType", "id": 123} format
            - Setting a field to None clears its value
            - Fields are validated against the ShotGrid schema before update
            - The returned entity includes all fields, not just the updated ones
        """
        try:
            # Validate fields against schema
            validator = get_schema_validator()
            validation_result = validator.validate_fields(
                entity_type=entity_type,
                data=data,
                sg_connection=sg,
                check_required=False,  # Don't check required fields for updates
            )

            # Log validation warnings
            if validation_result["warnings"]:
                for warning in validation_result["warnings"]:
                    logger.warning(f"Field validation: {warning}")

            # Raise error if there are invalid fields
            if validation_result["invalid"]:
                raise ToolError(f"Invalid fields for {entity_type}: {', '.join(validation_result['invalid'])}")

            result = sg.update(entity_type, entity_id, data)
            if result is None:
                raise ToolError(f"Failed to update {entity_type} with ID {entity_id}")

            # Return structured result
            return EntityUpdateResult(
                entity=cast(EntityDict, serialize_entity(result)),
                entity_type=entity_type,
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="update_entity")
            raise  # This is needed to satisfy the type checker
