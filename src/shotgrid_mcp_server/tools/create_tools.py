"""Create tools for ShotGrid MCP server.

This module contains tools for creating entities in ShotGrid.
"""

import logging
from typing import Any, Dict, List, cast

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.response_models import (
    BatchOperationsResult,
    EntityCreateResult,
    generate_entity_url,
)
from shotgrid_mcp_server.schema_validator import get_schema_validator
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import EntityDict, FastMCPType

logger = logging.getLogger(__name__)


def _validate_and_create_entity(sg: Shotgun, entity_type: EntityType, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate fields and create entity.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity to create.
        data: Entity data.

    Returns:
        Created entity result.

    Raises:
        ToolError: If validation fails or creation fails.
    """
    # Validate fields against schema
    validator = get_schema_validator()
    validation_result = validator.validate_fields(
        entity_type=entity_type,
        data=data,
        sg_connection=sg,
        check_required=True,
    )

    # Log validation warnings
    if validation_result["warnings"]:
        for warning in validation_result["warnings"]:
            logger.warning(f"Field validation: {warning}")

    # Raise error if there are invalid fields
    if validation_result["invalid"]:
        raise ToolError(f"Invalid fields for {entity_type}: {', '.join(validation_result['invalid'])}")

    # Create entity
    result = sg.create(entity_type, data)
    if result is None:
        raise ToolError(f"Failed to create {entity_type}")

    # Generate entity URL
    entity_id = result.get("id")
    sg_url = generate_entity_url(sg.base_url, entity_type, entity_id) if entity_id else None

    # Return structured result
    return EntityCreateResult(
        entity=cast(EntityDict, serialize_entity(result)),
        entity_type=entity_type,
        sg_url=sg_url,
    ).model_dump()


def register_create_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register create tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("entity_create")
    def create_entity(entity_type: EntityType, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single entity in ShotGrid.

        Use this tool to create one entity at a time. For creating multiple entities
        efficiently in a single operation, use `batch_create_entities` instead.

        Common use cases:
        - Create a new Shot in a Sequence
        - Create a new Task assigned to an artist
        - Create a new Version linked to a Shot
        - Create a new Note with attachments
        - Create a new Asset in a project

        ShotGrid Entity Types:
        - Shot: Individual shots in sequences
        - Asset: Reusable elements (characters, props, environments)
        - Task: Work assignments for artists
        - Version: Iterations of work (e.g., animation v003)
        - PublishedFile: Finalized files ready for use
        - Note: Comments and feedback
        - Playlist: Collections of versions for review
        - Project, Sequence, Episode, CustomEntity01, etc.

        Field Naming Conventions:
        - Standard fields: code, description, created_at, updated_at
        - Status fields: sg_status_list
        - Custom fields: sg_custom_field_name (always prefixed with sg_)
        - Entity references: {"type": "EntityType", "id": 123}
        - Multi-entity fields: [{"type": "User", "id": 1}, {"type": "User", "id": 2}]

        Args:
            entity_type: The type of entity to create (e.g., "Shot", "Asset", "Task").
                        Must be a valid ShotGrid entity type.

            data: Dictionary of field values for the new entity.
                  Required fields depend on the entity type.

                  Shot example:
                  {
                      "code": "SH001",
                      "project": {"type": "Project", "id": 123},
                      "sg_sequence": {"type": "Sequence", "id": 456},
                      "description": "Opening shot of the sequence",
                      "sg_status_list": "ip"
                  }

                  Task example:
                  {
                      "content": "Animation",
                      "entity": {"type": "Shot", "id": 789},
                      "task_assignees": [{"type": "HumanUser", "id": 42}],
                      "sg_status_list": "wtg",
                      "due_date": "2025-12-31"
                  }

                  Version example:
                  {
                      "code": "animation_v003",
                      "project": {"type": "Project", "id": 123},
                      "entity": {"type": "Shot", "id": 789},
                      "sg_status_list": "rev",
                      "description": "Latest animation pass"
                  }

        Returns:
            Dictionary containing:
            - entity: The created entity with all fields populated
            - entity_type: The type of entity created
            - schema_resources: Links to schema information

            Example:
            {
                "entity": {
                    "type": "Shot",
                    "id": 1234,
                    "code": "SH001",
                    "project": {"type": "Project", "id": 123, "name": "Demo Project"},
                    "sg_sequence": {"type": "Sequence", "id": 456, "code": "SEQ01"},
                    "sg_status_list": "ip",
                    "created_at": "2025-01-15T10:30:00Z",
                    ...
                },
                "entity_type": "Shot",
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
            ToolError: If required fields are missing, field validation fails,
                      or the ShotGrid API returns an error.

        Note:
            - Fields are validated against the ShotGrid schema before creation
            - Invalid or non-editable fields will raise an error
            - Entity references must include both "type" and "id"
            - Required fields vary by entity type (e.g., Shot requires "code" and "project")
            - Date fields use ISO 8601 format (YYYY-MM-DD or YYYY-MM-DDTHH:MM:SSZ)
        """
        try:
            return _validate_and_create_entity(sg, entity_type, data)
        except Exception as err:
            handle_error(err, operation="create_entity")
            raise  # This is needed to satisfy the type checker

    @server.tool("batch_entity_create")
    def batch_create_entities(entity_type: EntityType, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create multiple entities of the same type in ShotGrid in a single batch operation.

        **When to use this tool:**
        - You need to create multiple entities of the same type (e.g., 10 shots)
        - You want to create entities efficiently in a single API call
        - You have a list of entity data ready to create
        - You want to minimize API calls for better performance

        **When NOT to use this tool:**
        - To create a single entity - Use `create_entity` instead (simpler)
        - To create entities of different types - Use `batch_operations` instead
        - To update existing entities - Use `update_entity` or `batch_operations` instead

        **Common use cases:**
        - Create 10 shots in a sequence at once
        - Create multiple tasks for a shot
        - Create multiple assets in a project
        - Bulk import entities from a spreadsheet

        Args:
            entity_type: Type of entity to create.
                        All entities in the batch must be of the same type.

                        Example: "Shot"

            data_list: List of entity data dictionaries.
                      Each dictionary contains the field values for one entity.

                      Example:
                      [
                          {"code": "SH001", "project": {"type": "Project", "id": 123}},
                          {"code": "SH002", "project": {"type": "Project", "id": 123}},
                          {"code": "SH003", "project": {"type": "Project", "id": 123}}
                      ]

        Returns:
            Dictionary containing:
            - results: List of created entities with their IDs
            - total_count: Total number of entities processed
            - success_count: Number of successfully created entities
            - failure_count: Number of failed creations
            - message: Summary message

            Example:
            {
                "results": [
                    {"type": "Shot", "id": 1234, "code": "SH001"},
                    {"type": "Shot", "id": 1235, "code": "SH002"},
                    {"type": "Shot", "id": 1236, "code": "SH003"}
                ],
                "total_count": 3,
                "success_count": 3,
                "failure_count": 0,
                "message": "Successfully created 3 Shot entities"
            }

        Raises:
            ToolError: If any create operation fails or entity_type is invalid.

        Examples:
            Create multiple shots:
            {
                "entity_type": "Shot",
                "data_list": [
                    {"code": "SH001", "project": {"type": "Project", "id": 123}},
                    {"code": "SH002", "project": {"type": "Project", "id": 123}},
                    {"code": "SH003", "project": {"type": "Project", "id": 123}}
                ]
            }

            Create multiple tasks:
            {
                "entity_type": "Task",
                "data_list": [
                    {"content": "Animation", "entity": {"type": "Shot", "id": 1234}, "project": {"type": "Project", "id": 123}},
                    {"content": "Lighting", "entity": {"type": "Shot", "id": 1234}, "project": {"type": "Project", "id": 123}}
                ]
            }

        Note:
            - All entities must be of the same type
            - Batch operations are more efficient than creating entities one by one
            - If any entity fails to create, the entire batch may fail
            - Use `batch_operations` for mixed entity types or mixed operations (create/update/delete)
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

            # Serialize results and add sg_url
            serialized_results = []
            for result in results:
                serialized = cast(EntityDict, serialize_entity(result))
                # Add sg_url to each created entity
                entity_id = result.get("id") if isinstance(result, dict) else None
                if entity_id:
                    serialized["sg_url"] = generate_entity_url(sg.base_url, entity_type, entity_id)
                serialized_results.append(serialized)

            # Return structured result
            return BatchOperationsResult(
                results=serialized_results,
                total_count=len(serialized_results),
                success_count=len(serialized_results),
                failure_count=0,
                message=f"Successfully created {len(serialized_results)} {entity_type} entities",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="batch_create_entities")
            raise  # This is needed to satisfy the type checker

    # Expose create tool implementations at module level for tests and internal use
    globals()["create_entity"] = create_entity
    globals()["batch_create_entities"] = batch_create_entities

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
        """Execute multiple operations in a single batch request to ShotGrid.

        Use this tool when you need to perform multiple operations efficiently in one API call.
        This is significantly faster than executing operations one by one.

        Common use cases:
        - Create multiple entities at once (e.g., 50 shots in a sequence)
        - Update multiple entities with different values
        - Mix different operation types (create some, update others, delete some)
        - Perform bulk data migrations or cleanup
        - Initialize project structure (create sequences, shots, tasks)

        For creating multiple entities of the same type, you can also use `batch_entity_create`.
        For single operations, use the individual tools (entity_create, entity_update, entity_delete).

        Supported Operations:
            - create: Create new entities
            - update: Update existing entities
            - delete: Delete (retire) entities
            - download_thumbnail: Download entity thumbnails (special handling)

        Args:
            operations: List of operation dictionaries. Each operation must have:

                request_type: Type of operation to perform.
                    Values: "create", "update", "delete", "download_thumbnail"

                entity_type: Type of entity to operate on.
                    Examples: "Shot", "Asset", "Task", "Version"

                For CREATE operations:
                    data: Dictionary of field values for the new entity.

                    Example:
                    {
                        "request_type": "create",
                        "entity_type": "Shot",
                        "data": {
                            "code": "SH001",
                            "project": {"type": "Project", "id": 123},
                            "sg_sequence": {"type": "Sequence", "id": 456}
                        }
                    }

                For UPDATE operations:
                    entity_id: ID of the entity to update.
                    data: Dictionary of fields to update.

                    Example:
                    {
                        "request_type": "update",
                        "entity_type": "Shot",
                        "entity_id": 1234,
                        "data": {
                            "sg_status_list": "ip",
                            "description": "Updated description"
                        }
                    }

                For DELETE operations:
                    entity_id: ID of the entity to delete.

                    Example:
                    {
                        "request_type": "delete",
                        "entity_type": "Shot",
                        "entity_id": 1234
                    }

                For DOWNLOAD_THUMBNAIL operations:
                    entity_id: ID of the entity.
                    field_name: (Optional) Thumbnail field name, defaults to "image".
                    file_path: (Optional) Path to save thumbnail.
                    size: (Optional) Thumbnail size ("thumbnail", "large", "800x600").
                    image_format: (Optional) Image format ("jpg", "png").

                    Example:
                    {
                        "request_type": "download_thumbnail",
                        "entity_type": "Asset",
                        "entity_id": 456,
                        "field_name": "image",
                        "file_path": "/path/to/save/thumbnail.jpg",
                        "size": "large",
                        "image_format": "jpg"
                    }

        Returns:
            List of operation results. Each result corresponds to an operation in the input list.

            For successful operations:
            - CREATE: Returns the created entity with all fields
            - UPDATE: Returns the updated entity with all fields
            - DELETE: Returns True
            - DOWNLOAD_THUMBNAIL: Returns download result

            For failed operations:
            - Returns error information

            Example:
            [
                {
                    "type": "Shot",
                    "id": 1234,
                    "code": "SH001",
                    ...
                },
                {
                    "type": "Shot",
                    "id": 1235,
                    "code": "SH002",
                    ...
                },
                True  # Delete result
            ]

        Raises:
            ToolError: If operations list is empty, contains invalid operations,
                      or the batch request fails.

        Examples:
            Create multiple shots:
            [
                {
                    "request_type": "create",
                    "entity_type": "Shot",
                    "data": {
                        "code": "SH001",
                        "project": {"type": "Project", "id": 123},
                        "sg_sequence": {"type": "Sequence", "id": 456}
                    }
                },
                {
                    "request_type": "create",
                    "entity_type": "Shot",
                    "data": {
                        "code": "SH002",
                        "project": {"type": "Project", "id": 123},
                        "sg_sequence": {"type": "Sequence", "id": 456}
                    }
                }
            ]

            Mixed operations (create, update, delete):
            [
                {
                    "request_type": "create",
                    "entity_type": "Task",
                    "data": {
                        "content": "Animation",
                        "entity": {"type": "Shot", "id": 1234},
                        "project": {"type": "Project", "id": 123}
                    }
                },
                {
                    "request_type": "update",
                    "entity_type": "Shot",
                    "entity_id": 1234,
                    "data": {
                        "sg_status_list": "ip"
                    }
                },
                {
                    "request_type": "delete",
                    "entity_type": "Shot",
                    "entity_id": 5678
                }
            ]

            Bulk status update:
            [
                {
                    "request_type": "update",
                    "entity_type": "Task",
                    "entity_id": 100,
                    "data": {"sg_status_list": "fin"}
                },
                {
                    "request_type": "update",
                    "entity_type": "Task",
                    "entity_id": 101,
                    "data": {"sg_status_list": "fin"}
                },
                {
                    "request_type": "update",
                    "entity_type": "Task",
                    "entity_id": 102,
                    "data": {"sg_status_list": "fin"}
                }
            ]

        Performance Benefits:
            - Single API call instead of N separate calls
            - Reduced network latency
            - Faster execution (up to 10x for large batches)
            - Atomic operation (all succeed or all fail)

        Note:
            - Operations are executed in the order provided
            - If one operation fails, subsequent operations may not execute
            - Maximum batch size is typically 500 operations (ShotGrid limit)
            - Thumbnail downloads are handled separately from standard operations
            - All operations must be valid before execution begins
            - Use schema validation to ensure field names are correct
        """
        try:
            # Validate operations
            validate_batch_operations(operations)

            # Separate thumbnail operations from standard batch operations
            thumbnail_operations = [op for op in operations if op.get("request_type") == "download_thumbnail"]
            standard_operations = [op for op in operations if op.get("request_type") != "download_thumbnail"]

            results = []

            # Execute standard batch operations if any
            if standard_operations:
                standard_results = sg.batch(standard_operations)
                if standard_results is None:
                    raise ToolError("Failed to execute standard batch operations")
                results.extend(standard_results)

            # Execute thumbnail operations if any
            if thumbnail_operations:
                # Import the thumbnail_tools module here to avoid circular imports
                from shotgrid_mcp_server.tools.thumbnail_tools import download_thumbnail

                for op in thumbnail_operations:
                    entity_type = op["entity_type"]
                    entity_id = op["entity_id"]
                    field_name = op.get("field_name", "image")
                    file_path = op.get("file_path")
                    size = op.get("size")
                    image_format = op.get("image_format")

                    try:
                        # Use the download_thumbnail function to handle the operation
                        result = download_thumbnail(
                            sg=sg,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            field_name=field_name,
                            file_path=file_path,
                            size=size,
                            image_format=image_format,
                        )
                        results.append(result)
                    except Exception as download_err:
                        results.append({"error": str(download_err)})

            # Format results and add sg_url for create operations
            return format_batch_results_with_url(results, standard_operations, sg.base_url)
        except Exception as err:
            handle_error(err, operation="batch_operations")
            raise  # This is needed to satisfy the type checker

    # Expose batch_operations implementation at module level for tests and internal use
    globals()["batch_operations"] = batch_operations


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
        if request_type not in ["create", "update", "delete", "download_thumbnail"]:
            raise ToolError(f"Invalid request_type in operation {i}: {request_type}")

        if "entity_type" not in op:
            raise ToolError(f"Missing entity_type in operation {i}")

        if request_type in ["update", "delete", "download_thumbnail"] and "entity_id" not in op:
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


def format_batch_results_with_url(
    results: List[Any], operations: List[Dict[str, Any]], base_url: str
) -> List[Dict[str, Any]]:
    """Format batch operation results and add sg_url for create operations.

    Args:
        results: Results from batch operation.
        operations: List of operations that were executed (excluding thumbnail ops).
        base_url: ShotGrid base URL for generating entity URLs.

    Returns:
        List[Dict[str, Any]]: Formatted results with sg_url added for create operations.
    """
    formatted_results = []

    for i, result in enumerate(results):
        if result is not None and isinstance(result, dict) and "type" in result and "id" in result:
            serialized = cast(Dict[str, Any], serialize_entity(result))

            # Add sg_url for create operations
            if i < len(operations):
                op = operations[i]
                if op.get("request_type") == "create":
                    entity_type = result.get("type")
                    entity_id = result.get("id")
                    if entity_type and entity_id:
                        serialized["sg_url"] = generate_entity_url(base_url, entity_type, entity_id)

            formatted_results.append(serialized)
        else:
            formatted_results.append(result)  # type: ignore[arg-type]

    return formatted_results
