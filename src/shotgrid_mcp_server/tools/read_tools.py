"""Read tools for ShotGrid MCP server.

This module contains tools for reading entities from ShotGrid.
"""

from typing import Any, Dict

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.response_models import SchemaResult
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
        """Get field schema information for an entity type in ShotGrid.

        **When to use this tool:**
        - You need to know what fields are available for an entity type
        - You need to check field data types (text, number, date, entity, etc.)
        - You need to validate field names before creating/updating entities
        - You need to see field properties (required, editable, default values)
        - You want to understand the structure of an entity type

        **When NOT to use this tool:**
        - To get entity data - Use `search_entities` or `find_one_entity` instead
        - To get all entity types - Use `sg_schema_entity_read` instead
        - To get a specific field's schema - Use `sg_schema_field_read` instead
        - For cached schema information - Check MCP resources first

        **Common use cases:**
        - Validate field names before creating a Shot
        - Check what fields are available for Task entity
        - Understand field data types for Version entity
        - See required fields for creating an Asset

        Args:
            entity_type: Type of entity to get schema for.
                        Must be a valid ShotGrid entity type.

                        Common types:
                        - "Shot": Shots in sequences
                        - "Asset": Assets (characters, props, environments)
                        - "Task": Work assignments
                        - "Version": Published versions
                        - "PublishedFile": Published files
                        - "Note": Notes and comments

                        Example: "Shot"

        Returns:
            Dictionary containing:
            - entity_type: The entity type
            - fields: Dictionary of field schemas
              Each field schema includes:
              - data_type: Field data type (text, number, date, entity, etc.)
              - properties: Field properties (editable, required, default_value, etc.)

            Example:
            {
                "entity_type": "Shot",
                "fields": {
                    "code": {
                        "data_type": {"value": "text"},
                        "properties": {
                            "editable": {"value": true},
                            "summary_default": {"value": "none"}
                        }
                    },
                    "sg_status_list": {
                        "data_type": {"value": "status_list"},
                        "properties": {
                            "valid_values": {"value": ["wtg", "ip", "rev", "fin", "omt"]}
                        }
                    },
                    ...
                }
            }

        Raises:
            ToolError: If the schema retrieval fails or entity_type is invalid.

        Examples:
            Get schema for Shot entity:
            {
                "entity_type": "Shot"
            }

            Get schema for Task entity:
            {
                "entity_type": "Task"
            }

        Note:
            - Schema information is relatively static and can be cached
            - Use this to validate field names before operations
            - Field data types determine what values are valid
            - Some fields are read-only (editable: false)
            - Check MCP resources for cached schema information first
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

            # Return structured result
            return SchemaResult(
                entity_type=entity_type,
                fields=dict(result),
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="get_schema")
            raise  # This is needed to satisfy the type checker
