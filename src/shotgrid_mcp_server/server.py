"""ShotGrid MCP server implementation."""

# Import built-in modules
import json
import os
from typing import Any, Dict, List, Optional

# Import third-party modules
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext
from shotgrid_mcp_server.logger import get_logger, setup_logging
from shotgrid_mcp_server.utils import DateTimeEncoder, get_entity_types, handle_error

# Configure logging
logger = get_logger(__name__)


class ToolError(Exception):
    """Base class for tool-related errors."""

    pass


# Debug print environment variables
print("Successfully loaded environment variables:")
print(f"SHOTGRID_URL: {os.getenv('SHOTGRID_URL')}")
print(f"SCRIPT_NAME: {os.getenv('SCRIPT_NAME')}")
print(f"SCRIPT_KEY: {'*' * len(os.getenv('SCRIPT_KEY', ''))}")  # Mask API key


class ShotGridTools:
    """Collection of ShotGrid MCP tools.

    This class provides a set of tools for interacting with ShotGrid through MCP.
    Each tool is designed to handle specific operations like CRUD and file downloads.
    """

    def __init__(self) -> None:
        """Initialize ShotGridTools with a connection pool."""
        self.connection_context = ShotGridConnectionContext()
        self.sg = None

    def __enter__(self) -> "ShotGridTools":
        """Enter the context manager.

        Returns:
            ShotGridTools: The initialized tools instance.
        """
        self.sg = self.connection_context.__enter__()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the context manager.

        Args:
            exc_type: Exception type if an error occurred.
            exc_val: Exception value if an error occurred.
            exc_tb: Exception traceback if an error occurred.
        """
        self.connection_context.__exit__(exc_type, exc_val, exc_tb)

    def get_thumbnail_url(self, entity_type: str, entity_id: int, field_name: str) -> str:
        """Get the thumbnail URL for a ShotGrid entity.

        Args:
            entity_type: The type of entity (e.g., "Asset", "Shot").
            entity_id: The ID of the entity.
            field_name: The name of the thumbnail field.

        Returns:
            str: The thumbnail URL.

        Raises:
            ValueError: If the entity is not found or has no thumbnail URL.
        """
        entity = self.sg.find_one(entity_type, [["id", "is", entity_id]], [field_name])
        if not entity:
            raise ValueError(f"Entity {entity_type} with ID {entity_id} not found")

        if field_name not in entity:
            raise ValueError(f"Field {field_name} not found in entity")

        field_value = entity[field_name]
        if not field_value:
            raise ValueError(f"No thumbnail found in field {field_name}")

        # Handle different field types
        if isinstance(field_value, dict) and "url" in field_value:
            return field_value["url"]
        elif isinstance(field_value, str):
            return field_value
        else:
            raise ValueError(f"Invalid thumbnail field format: {field_value}")

    def download_thumbnail(self, entity_type: str, entity_id: int, field_name: str) -> bytes:
        """Download a thumbnail from ShotGrid.

        Args:
            entity_type: The type of entity (e.g., "Asset", "Shot").
            entity_id: The ID of the entity.
            field_name: The name of the thumbnail field.

        Returns:
            bytes: The thumbnail data.

        Raises:
            ValueError: If the entity is not found or has no thumbnail.
            ToolError: If there is an error downloading the thumbnail.
        """
        try:
            url = self.get_thumbnail_url(entity_type, entity_id, field_name)
            response = self.sg.download_attachment({"url": url})
            if not response:
                raise ValueError("Failed to download thumbnail")
            return response
        except Exception as e:
            logger.error("Failed to download thumbnail: %s", str(e))
            if isinstance(e, ValueError):
                raise
            raise ToolError(f"Failed to download thumbnail: {str(e)}")

    @staticmethod
    def handle_error(error: Exception, operation: str) -> str:
        """Handle errors in ShotGrid operations.

        Args:
            error: The exception that occurred.
            operation: Description of the operation that failed.

        Returns:
            str: Error message in JSON format.
        """
        error_msg = f"Failed to {operation}: {str(error)}"
        logger.error(error_msg)
        return json.dumps({"error": error_msg}, cls=DateTimeEncoder)

    @staticmethod
    def create_tool(server: FastMCP) -> None:
        """Register create tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool()
        async def create_entity(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
            """Create a single entity in ShotGrid.

            Args:
                entity_type: Type of entity to create.
                data: Entity data.

            Returns:
                Dict[str, Any]: Created entity data.
            """
            try:
                with ShotGridTools() as tools:
                    result = tools.sg.create(entity_type, data)
                logger.info("Created entity of type %s with ID %d", entity_type, result["id"])
                return result
            except Exception as e:
                error = ShotGridTools.handle_error(e, "create entity")
                return json.loads(error)

        @server.tool()
        async def batch_create(entity_type: str, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Create multiple entities in ShotGrid.

            Args:
                entity_type: Type of entities to create.
                data: List of entity data.

            Returns:
                List[Dict[str, Any]]: Created entities data.
            """
            try:
                batch_data = [{"request_type": "create", "entity_type": entity_type, "data": item} for item in data]
                with ShotGridTools() as tools:
                    results = tools.sg.batch(batch_data)
                logger.info("Created %d entities of type %s", len(results), entity_type)
                return results
            except Exception as e:
                error = ShotGridTools.handle_error(e, "batch create entities")
                return [json.loads(error)]

    @staticmethod
    def read_tool(server: FastMCP) -> None:
        """Register read tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool("find_entity")
        def find_entity(entity_id: int) -> Dict[str, Any]:
            """Find an entity by ID across all entity types.

            Args:
                entity_id: The ID of the entity to find.

            Returns:
                The entity data if found.
            """
            try:
                with ShotGridTools() as tools:
                    # Get all available entity types
                    entity_types = get_entity_types()

                    # Try each entity type
                    errors = []
                    for entity_type in entity_types:
                        try:
                            entity = tools.sg.find_one(
                                entity_type, [["id", "is", entity_id]], ["type", "code", "image", "sg_uploaded_movie"]
                            )
                            if entity:
                                logger.info("Found entity %s with ID %d", entity_type, entity_id)
                                return entity
                        except Exception as e:
                            errors.append(f"Error searching {entity_type}: {str(e)}")
                            continue

                    # If we get here, no entity was found
                    error_msg = f"No entity found with ID {entity_id}"
                    if errors:
                        error_msg += f"\nErrors encountered: {'; '.join(errors)}"
                    raise ValueError(error_msg)

            except Exception as e:
                logger.error("Error in find_entity: %s", str(e))
                return handle_error(e, operation="find_entity")

        @server.tool("get_entity_types")
        def get_available_entity_types() -> Dict[str, Any]:
            """Get all available entity types.

            Returns:
                Dictionary containing the list of entity types.
            """
            try:
                entity_types = list(get_entity_types())
                entity_types.sort()  # Sort for consistent output
                return {"entity_types": entity_types, "message": f"Found {len(entity_types)} entity types"}
            except Exception as e:
                return handle_error(e, operation="get_entity_types")

        @server.tool("search_entities")
        def search_entities(
            entity_type: str,
            filters: List[List[Any]],
            fields: Optional[List[str]] = None,
            order: Optional[List[List[str]]] = None,
            filter_operator: Optional[str] = None,
            limit: Optional[int] = None,
            retired_only: bool = False,
            page: Optional[int] = None,
        ) -> Dict[str, Any]:
            """Search for entities in ShotGrid.

            Args:
                entity_type: The type of entity to search for.
                filters: List of filter conditions.
                fields: List of fields to return.
                order: List of fields to order by.
                filter_operator: The filter operator to use.
                limit: Maximum number of entities to return.
                retired_only: Whether to return only retired entities.
                page: Page number for pagination.

            Returns:
                Dictionary containing the search results.
            """
            try:
                with ShotGridTools() as tools:
                    # Build find arguments
                    find_kwargs = {}
                    
                    # Required arguments
                    if not isinstance(filters, list):
                        raise ValueError("Filters must be a list of conditions")
                    
                    # Optional arguments
                    if fields is not None:
                        # 确保 fields 包含必要字段
                        essential_fields = {"id", "type"}
                        if isinstance(fields, list):
                            fields = list(set(fields) | essential_fields)
                        find_kwargs["fields"] = fields
                        
                    if order is not None:
                        find_kwargs["order"] = order
                    if filter_operator is not None:
                        find_kwargs["filter_operator"] = filter_operator
                    if limit is not None:
                        find_kwargs["limit"] = limit
                    if retired_only:
                        find_kwargs["retired_only"] = retired_only
                    if page is not None:
                        find_kwargs["page"] = page

                    logger.debug("Executing find with args: entity_type=%s, filters=%s, kwargs=%s", 
                               entity_type, filters, find_kwargs)
                    
                    try:
                        # 直接执行查询
                        entities = tools.sg.find(entity_type, filters, **find_kwargs)
                        
                        if not isinstance(entities, list):
                            logger.warning("Unexpected response type: %s", type(entities))
                            entities = []
                            
                        # 处理返回数据
                        processed_entities = []
                        for entity in entities:
                            if not isinstance(entity, dict):
                                logger.warning("Skipping non-dict entity: %s", type(entity))
                                continue
                                
                            # 创建新的字典以避免修改原始数据
                            processed_entity = {}
                            
                            # 复制基本字段
                            for field in ["id", "type"]:
                                if field in entity:
                                    processed_entity[field] = entity[field]
                            
                            # 复制其他请求的字段
                            if fields:
                                for field in fields:
                                    if field in entity and field not in processed_entity:
                                        value = entity[field]
                                        # 如果值是字符串且过长，进行截断
                                        if isinstance(value, str) and len(value) > 1000:
                                            value = value[:1000] + "..."
                                        processed_entity[field] = value
                            
                            processed_entities.append(processed_entity)
                            
                        logger.info("Found and processed %d entities", len(processed_entities))
                        return {"entities": processed_entities}
                        
                    except Exception as e:
                        logger.error("Error during entity search: %s", str(e))
                        raise

            except Exception as e:
                error = ShotGridTools.handle_error(e, "search_entities")
                if isinstance(error, str):
                    return json.loads(error)
                return error

        @server.tool()
        async def batch_read(entity_type: str, entity_ids: List[int], fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
            """Read multiple entities from ShotGrid.

            Args:
                entity_type: Type of entities to read.
                entity_ids: List of entity IDs to read.
                fields: Optional list of fields to return.

            Returns:
                List of entity data.
            """
            try:
                with ShotGridTools() as tools:
                    # Build find arguments
                    find_kwargs = {}
                    if fields is not None:
                        find_kwargs["fields"] = fields

                    # Execute find for each entity ID
                    entities = []
                    for entity_id in entity_ids:
                        try:
                            entity = tools.sg.find_one(entity_type, [["id", "is", entity_id]], **find_kwargs)
                            if entity:
                                entities.append(entity)
                        except Exception as e:
                            logger.error("Error reading entity %s with ID %d: %s", entity_type, entity_id, str(e))

                    logger.info("Read %d entities of type %s", len(entities), entity_type)
                    return entities

            except Exception as e:
                error = ShotGridTools.handle_error(e, "batch read entities")
                return [json.loads(error)]

    @staticmethod
    def update_tool(server: FastMCP) -> None:
        """Register update tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool()
        async def update_entity(entity_type: str, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
            """Update a single entity in ShotGrid.

            Args:
                entity_type: Type of entity to update.
                entity_id: ID of the entity.
                data: Updated entity data.

            Returns:
                Dict[str, Any]: Updated entity data.
            """
            try:
                with ShotGridTools() as tools:
                    # First get the entity to ensure it exists and get its current data
                    entity = tools.sg.find_one(entity_type, [["id", "is", entity_id]])
                    if not entity:
                        raise ValueError(f"Entity {entity_type} with ID {entity_id} not found")
                    
                    # Update the entity
                    result = tools.sg.update(entity_type, entity_id, data)
                    logger.info("Updated entity of type %s with ID %d", entity_type, entity_id)
                    return result
            except Exception as e:
                error = ShotGridTools.handle_error(e, "update entity")
                return json.loads(error)

        @server.tool()
        async def batch_update(entity_type: str, data: List[Dict[str, Any]]) -> str:
            """Update multiple entities in ShotGrid.

            Args:
                entity_type: Type of entities to update.
                data: List of entity data with IDs.

            Returns:
                str: Updated entities data in JSON format.
            """
            try:
                batch_data = [
                    {
                        "request_type": "update",
                        "entity_type": entity_type,
                        "entity_id": item["id"],
                        "data": {k: v for k, v in item.items() if k != "id"},
                    }
                    for item in data
                ]
                with ShotGridTools() as tools:
                    results = tools.sg.batch(batch_data)
                logger.info("Updated %d entities of type %s", len(results), entity_type)
                return json.dumps(results, cls=DateTimeEncoder)
            except Exception as e:
                return ShotGridTools.handle_error(e, "batch update entities")

    @staticmethod
    def delete_tool(server: FastMCP) -> None:
        """Register delete tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool()
        async def delete_entity(entity_type: str, entity_id: int) -> None:
            """Delete a single entity from ShotGrid.

            Args:
                entity_type: Type of entity to delete.
                entity_id: ID of the entity.

            Returns:
                None
            """
            try:
                with ShotGridTools() as tools:
                    # First get the entity to ensure it exists
                    entity = tools.sg.find_one(entity_type, [["id", "is", entity_id]])
                    if not entity:
                        raise ValueError(f"Entity {entity_type} with ID {entity_id} not found")
                    
                    # Delete the entity
                    tools.sg.delete(entity_type, entity_id)
                    logger.info("Deleted entity of type %s with ID %d", entity_type, entity_id)
                    return None
            except Exception as e:
                error = ShotGridTools.handle_error(e, "delete entity")
                return json.loads(error)

        @server.tool()
        async def batch_delete(entity_type: str, entity_ids: List[int]) -> str:
            """Delete multiple entities from ShotGrid.

            Args:
                entity_type: Type of entities to delete.
                entity_ids: List of entity IDs to delete.

            Returns:
                str: Success message in JSON format.
            """
            try:
                batch_data = [
                    {"request_type": "delete", "entity_type": entity_type, "entity_id": entity_id}
                    for entity_id in entity_ids
                ]
                with ShotGridTools() as tools:
                    tools.sg.batch(batch_data)
                logger.info("Deleted %d entities of type %s", len(entity_ids), entity_type)
                return json.dumps({"message": f"Successfully deleted {len(entity_ids)} entities"})
            except Exception as e:
                return ShotGridTools.handle_error(e, "batch delete entities")

    @staticmethod
    def download_tool(server: FastMCP) -> None:
        """Register download tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool()
        async def download_thumbnail(
            entity_type: str,
            entity_id: int,
            field_name: str = "image",
            size: str = "original",
            local_path: Optional[str] = None,
            use_presigned_url: bool = True,
        ) -> Dict[str, Any]:
            """Download a thumbnail image for an entity from ShotGrid.

            Args:
                entity_type: The type of entity containing the thumbnail (e.g., "Shot", "Asset").
                entity_id: The ID of the entity.
                field_name: The field name containing the thumbnail (default: "image").
                size: Size of the thumbnail to download (e.g., "original", "thumb").
                local_path: Local path where the thumbnail should be saved.
                use_presigned_url: If True, use a pre-signed URL for download.

            Returns:
                Dict[str, Any]: Download status and file information.
            """
            try:
                with ShotGridTools() as tools:
                    # Get the thumbnail data
                    thumbnail_data = tools.download_thumbnail(entity_type, entity_id, field_name)
                    
                    # If local path is provided, save the file
                    if local_path:
                        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
                        with open(local_path, "wb") as f:
                            f.write(thumbnail_data)
                        return {
                            "success": True,
                            "message": f"Thumbnail saved to {local_path}",
                            "local_path": local_path,
                        }
                    
                    return {
                        "success": True,
                        "message": "Thumbnail downloaded successfully",
                        "data": thumbnail_data,
                    }
            except Exception as e:
                error = ShotGridTools.handle_error(e, "download thumbnail")
                return json.loads(error)

        @server.tool()
        async def download_attachment(entity_type: str, entity_id: int, field_name: str, local_path: str) -> str:
            """Download an attachment from a ShotGrid entity.

            Args:
                entity_type: The type of entity containing the attachment (e.g., "Shot", "Version").
                entity_id: The ID of the entity.
                field_name: The field name containing the attachment.
                local_path: Local path where the attachment should be saved.

            Returns:
                str: JSON string containing the download status and file information.
            """
            try:
                with ShotGridTools() as tools:
                    # First get the entity to retrieve attachment info
                    logger.debug("Searching for entity %s with ID %d", entity_type, entity_id)
                    entity = tools.sg.find_one(entity_type, [["id", "is", entity_id]], [field_name])

                    if not entity:
                        error_msg = f"Entity {entity_type} with ID {entity_id} not found"
                        logger.error(error_msg)
                        return json.dumps({"error": error_msg})

                    logger.debug("Found entity: %s", entity)

                    if not entity.get(field_name):
                        error_msg = f"No attachment found in field {field_name}"
                        logger.error(error_msg)
                        return json.dumps({"error": error_msg})

                    attachment_data = entity.get(field_name)
                    logger.debug("Attachment data: %s", attachment_data)

                    # Create directory if it doesn't exist
                    os.makedirs(os.path.dirname(local_path), exist_ok=True)

                    # Download the attachment
                    logger.debug("Downloading attachment to %s", local_path)
                    tools.sg.download_attachment({"type": entity_type, "id": entity_id}, field_name, local_path)

                    if not os.path.exists(local_path):
                        error_msg = f"Failed to download attachment: File not created at {local_path}"
                        logger.error(error_msg)
                        return json.dumps({"error": error_msg})

                    logger.info(
                        "Successfully downloaded attachment from %s %d field %s to %s",
                        entity_type,
                        entity_id,
                        field_name,
                        local_path,
                    )
                    return json.dumps(
                        {
                            "message": "Attachment downloaded successfully",
                            "local_path": local_path,
                            "attachment_data": attachment_data,
                        }
                    )
            except Exception as e:
                error_msg = f"Failed to download attachment: {str(e)}"
                logger.error(error_msg, exc_info=True)
                return json.dumps({"error": error_msg})

    @staticmethod
    def schema_tool(server: FastMCP) -> None:
        """Register schema tools with the MCP server.

        Args:
            server: The FastMCP server instance.
        """

        @server.tool()
        async def get_schema(entity_type: Optional[str] = None) -> Dict[str, Any]:
            """Get schema information from ShotGrid.

            Args:
                entity_type: Optional entity type to get schema for. If None, returns schema for all types.

            Returns:
                Dict[str, Any]: Schema information.
            """
            try:
                with ShotGridTools() as tools:
                    if entity_type:
                        schema = tools.sg.schema_field_read(entity_type)
                    else:
                        schema = tools.sg.schema_read()
                logger.info("Retrieved schema information")
                return schema
            except Exception as e:
                error = ShotGridTools.handle_error(e, "get schema")
                return json.loads(error)

    @staticmethod
    def batch_tool(server: FastMCP) -> None:
        """Register the batch operation tools.

        Args:
            server: The FastMCP server to register the tool with.
        """

        @server.tool("batch_operations")
        def batch_operations(requests: List[Dict[str, Any]]) -> List[Any]:
            """Execute multiple operations in a single batch request.

            Args:
                requests: List of operation requests. Each request should have:
                    - request_type: Type of request ("create", "update", "delete", "read")
                    - entity_type: Type of entity to operate on
                    - data: Dict of fields (for create/update)
                    - entity_id: Entity ID (for update/delete)
                    - fields: List of fields to return (for read)

            Returns:
                List of results for each operation in the batch.
            """
            try:
                with ShotGridTools() as tools:
                    # Validate requests
                    for req in requests:
                        if "request_type" not in req or "entity_type" not in req:
                            raise ValueError("Each request must have 'request_type' and 'entity_type'")

                        if req["request_type"] not in ["create", "update", "delete", "read"]:
                            raise ValueError(f"Invalid request_type: {req['request_type']}")

                    # Prepare batch data
                    batch_data = []
                    for req in requests:
                        request_type = req["request_type"]
                        entity_type = req["entity_type"]

                        if request_type == "create":
                            if "data" not in req:
                                raise ValueError("Create requests must include 'data'")
                            batch_data.append(
                                {"request_type": "create", "entity_type": entity_type, "data": req["data"]}
                            )

                        elif request_type == "update":
                            if "entity_id" not in req or "data" not in req:
                                raise ValueError("Update requests must include 'entity_id' and 'data'")
                            batch_data.append(
                                {
                                    "request_type": "update",
                                    "entity_type": entity_type,
                                    "entity_id": req["entity_id"],
                                    "data": req["data"],
                                    "multi_entity_update_mode": req.get("multi_entity_update_mode"),
                                }
                            )

                        elif request_type == "delete":
                            if "entity_id" not in req:
                                raise ValueError("Delete requests must include 'entity_id'")
                            batch_data.append(
                                {"request_type": "delete", "entity_type": entity_type, "entity_id": req["entity_id"]}
                            )

                        elif request_type == "read":
                            if "entity_id" not in req:
                                raise ValueError("Read requests must include 'entity_id'")
                            batch_data.append(
                                {
                                    "request_type": "read",
                                    "entity_type": entity_type,
                                    "entity_id": req["entity_id"],
                                    "fields": req.get("fields", ["id", "type", "code"]),
                                }
                            )

                    # Execute batch request
                    results = tools.sg.batch(batch_data)
                    return results

            except Exception as e:
                return handle_error(e, operation="batch_operations")

        @server.tool("batch_create")
        def batch_create(entity_type: str, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Create multiple entities in a single batch request.

            Args:
                entity_type: Type of entities to create
                data_list: List of data dictionaries for each entity

            Returns:
                List of created entities
            """
            try:
                requests = [{"request_type": "create", "entity_type": entity_type, "data": data} for data in data_list]
                return batch_operations(requests)
            except Exception as e:
                return handle_error(e, operation="batch_create")

        @server.tool("batch_update")
        def batch_update(entity_type: str, updates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            """Update multiple entities in a single batch request.

            Args:
                entity_type: Type of entities to update
                updates: List of update specifications, each containing:
                    - entity_id: ID of entity to update
                    - data: Dictionary of fields to update
                    - multi_entity_update_mode: Optional update mode for multi-entity fields

            Returns:
                List of updated entities
            """
            try:
                requests = [
                    {
                        "request_type": "update",
                        "entity_type": entity_type,
                        "entity_id": update["entity_id"],
                        "data": update["data"],
                        "multi_entity_update_mode": update.get("multi_entity_update_mode"),
                    }
                    for update in updates
                ]
                return batch_operations(requests)
            except Exception as e:
                return handle_error(e, operation="batch_update")

        @server.tool("batch_delete")
        def batch_delete(entity_type: str, entity_ids: List[int]) -> List[bool]:
            """Delete multiple entities in a single batch request.

            Args:
                entity_type: Type of entities to delete
                entity_ids: List of entity IDs to delete

            Returns:
                List of boolean values indicating success of each deletion
            """
            try:
                requests = [
                    {"request_type": "delete", "entity_type": entity_type, "entity_id": entity_id}
                    for entity_id in entity_ids
                ]
                return batch_operations(requests)
            except Exception as e:
                return handle_error(e, operation="batch_delete")

    @staticmethod
    def search_tool(server: FastMCP) -> None:
        """Register the search tools.

        Args:
            server: The FastMCP server to register the tool with.
        """

        @server.tool("fuzzy_id_search")
        def fuzzy_id_search(
            target_id: int,
            range_size: int = 100,
            entity_types: Optional[List[str]] = None,
            fields: Optional[List[str]] = None,
        ) -> Dict[str, Any]:
            """Search for entities with IDs close to the target ID.

            Args:
                target_id: The target ID to search around
                range_size: The size of the ID range to search (default: 100)
                entity_types: Optional list of entity types to search (default: all common types)
                fields: Optional list of fields to return (default: basic fields)

            Returns:
                Dictionary containing search results grouped by entity type
            """
            try:
                with ShotGridTools() as tools:
                    # Calculate ID range
                    id_min = max(1, target_id - range_size // 2)
                    id_max = target_id + range_size // 2

                    # Use default entity types if none provided
                    if not entity_types:
                        entity_types = list(get_entity_types())

                    # Use default fields if none provided
                    if not fields:
                        fields = ["id", "type", "code", "image"]

                    results = {}
                    exact_match = None

                    # Search each entity type
                    for entity_type in entity_types:
                        filters = [["id", "between", id_min, id_max]]

                        entities = tools.sg.find(
                            entity_type, filters, fields=fields, order=[{"field_name": "id", "direction": "asc"}]
                        )

                        if entities:
                            results[entity_type] = entities
                            # Check for exact match
                            for entity in entities:
                                if entity["id"] == target_id:
                                    exact_match = entity

                    return {
                        "exact_match": exact_match,
                        "results": results,
                        "search_range": {"min_id": id_min, "max_id": id_max, "target_id": target_id},
                        "total_found": sum(len(entities) for entities in results.values()),
                    }

            except Exception as e:
                return handle_error(e, operation="fuzzy_id_search")

        @server.tool("id_range_search")
        def id_range_search(
            start_id: int,
            end_id: int,
            entity_types: Optional[List[str]] = None,
            fields: Optional[List[str]] = None,
            limit: Optional[int] = 1000,
        ) -> Dict[str, Any]:
            """Search for entities within a specific ID range.

            Args:
                start_id: Start of ID range
                end_id: End of ID range
                entity_types: Optional list of entity types to search
                fields: Optional list of fields to return
                limit: Maximum number of results to return per entity type

            Returns:
                Dictionary containing search results grouped by entity type
            """
            try:
                with ShotGridTools() as tools:
                    # Validate range
                    if start_id > end_id:
                        start_id, end_id = end_id, start_id

                    # Use default entity types if none provided
                    if not entity_types:
                        entity_types = list(get_entity_types())

                    # Use default fields if none provided
                    if not fields:
                        fields = ["id", "type", "code", "image"]

                    results = {}
                    total_found = 0

                    # Search each entity type
                    for entity_type in entity_types:
                        filters = [["id", "between", start_id, end_id]]

                        entities = tools.sg.find(
                            entity_type,
                            filters,
                            fields=fields,
                            order=[{"field_name": "id", "direction": "asc"}],
                            limit=limit,
                        )

                        if entities:
                            results[entity_type] = entities
                            total_found += len(entities)

                    return {
                        "results": results,
                        "search_range": {"start_id": start_id, "end_id": end_id},
                        "total_found": total_found,
                        "limit_per_type": limit,
                    }

            except Exception as e:
                return handle_error(e, operation="id_range_search")


def create_server() -> FastMCP:
    """Create and configure the MCP server.

    Returns:
        FastMCP: The configured server instance.
    """
    try:
        # Set up logging
        setup_logging()
        logger.info("Starting ShotGrid MCP server...")

        # Create server instance
        mcp = FastMCP(name="shotgrid-server")
        logger.info("Created FastMCP instance")

        # Register tools
        ShotGridTools.create_tool(mcp)
        ShotGridTools.read_tool(mcp)
        ShotGridTools.update_tool(mcp)
        ShotGridTools.delete_tool(mcp)
        ShotGridTools.download_tool(mcp)
        ShotGridTools.schema_tool(mcp)
        ShotGridTools.batch_tool(mcp)  # Register batch operation tools
        ShotGridTools.search_tool(mcp)  # Register search tools
        logger.info("Registered all tools")

        # Log environment information
        logger.info("Environment information:")
        logger.info("  ShotGrid URL: %s", os.getenv("SHOTGRID_URL"))
        logger.info("  Script Name: %s", os.getenv("SCRIPT_NAME"))

        return mcp

    except Exception as e:
        logger.error("Failed to create server: %s", str(e), exc_info=True)
        raise


# Create server instance
server = create_server()

if __name__ == "__main__":
    server.run()
