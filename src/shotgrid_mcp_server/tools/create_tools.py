"""Create tools for ShotGrid MCP server.

This module contains tools for creating entities in ShotGrid.
"""

from typing import Any, Dict, List, cast

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import EntityDict, FastMCPType
from shotgrid_mcp_server.types import EntityType


def register_create_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register create tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("create_entity")
    def create_entity(entity_type: EntityType, data: Dict[str, Any]) -> EntityDict:
        """Create an entity in ShotGrid.

        Args:
            entity_type: Type of entity to create.
            data: Entity data.

        Returns:
            Dict[str, Any]: Created entity.

        Raises:
            ToolError: If the create operation fails.
        """
        try:
            # Create entity
            result = sg.create(entity_type, data)
            if result is None:
                raise ToolError(f"Failed to create {entity_type}")

            # Return serialized entity
            return cast(EntityDict, serialize_entity(result))
        except Exception as err:
            handle_error(err, operation="create_entity")
            raise  # This is needed to satisfy the type checker

    @server.tool("batch_create_entities")
    def batch_create_entities(entity_type: EntityType, data_list: List[Dict[str, Any]]) -> List[EntityDict]:
        """Create multiple entities in ShotGrid.

        Args:
            entity_type: Type of entity to create.
            data_list: List of entity data.

        Returns:
            List[Dict[str, Any]]: List of created entities.

        Raises:
            ToolError: If any create operation fails.
        """
        try:
            # Create batch requests
            batch_data = []
            for data in data_list:
                batch_data.append({"request_type": "create", "entity_type": entity_type, "data": data})

            # Execute batch request
            results = sg.batch(batch_data)
            if not results:
                raise ToolError("Failed to create entities in batch")

            # Return serialized entities
            return [cast(EntityDict, serialize_entity(result)) for result in results]
        except Exception as err:
            handle_error(err, operation="batch_create_entities")
            raise  # This is needed to satisfy the type checker

    # Register batch operations tool
    register_batch_operations(server, sg)


def register_batch_operations(server: FastMCPType, sg: Shotgun) -> None:
    """Register batch operations tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("batch_operations")
    def batch_operations(operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple operations in a single batch request.

        This method allows for efficient execution of multiple operations
        (create, update, delete) in a single API call.

        Args:
            operations: List of operation dictionaries. Each operation should have:
                - request_type: "create", "update", or "delete"
                - entity_type: Type of entity
                - data: Data for create/update (not needed for delete)
                - entity_id: Entity ID for update/delete (not needed for create)

        Returns:
            List[Dict[str, Any]]: Results of the batch operations.

        Raises:
            ToolError: If the batch operation fails.
        """
        try:
            # Validate operations
            validate_batch_operations(operations)

            # Execute batch request
            results = sg.batch(operations)
            if results is None:
                raise ToolError("Failed to execute batch operations")

            # Format results
            return format_batch_results(results)
        except Exception as err:
            handle_error(err, operation="batch_operations")
            raise  # This is needed to satisfy the type checker


def validate_batch_operations(operations: List[Dict[str, Any]]) -> None:
    """Validate batch operations.

    Args:
        operations: List of operations to validate.

    Raises:
        ToolError: If any operation is invalid.
    """
    if not operations:
        raise ToolError("No operations provided for batch execution")

    # Validate each operation
    for i, op in enumerate(operations):
        request_type = op.get("request_type")
        if request_type not in ["create", "update", "delete"]:
            raise ToolError(f"Invalid request_type in operation {i}: {request_type}")

        if "entity_type" not in op:
            raise ToolError(f"Missing entity_type in operation {i}")

        if request_type in ["update", "delete"] and "entity_id" not in op:
            raise ToolError(f"Missing entity_id in {request_type} operation {i}")

        if request_type in ["create", "update"] and "data" not in op:
            raise ToolError(f"Missing data in {request_type} operation {i}")


def format_batch_results(results: List[Any]) -> List[Dict[str, Any]]:
    """Format batch operation results.

    Args:
        results: Results from batch operation.

    Returns:
        List[Dict[str, Any]]: Formatted results.
    """
    formatted_results = []
    for result in results:
        if result is not None and isinstance(result, dict) and "type" in result and "id" in result:
            formatted_results.append(cast(Dict[str, Any], serialize_entity(result)))
        else:
            formatted_results.append(result)  # type: ignore[arg-type]

    return formatted_results
