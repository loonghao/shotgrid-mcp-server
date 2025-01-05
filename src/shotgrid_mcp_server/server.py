"""ShotGrid MCP server implementation."""

# Import built-in modules
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Import third-party modules
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.connection_pool import (
    ShotGridConnectionContext,
    ShotgunClientFactory,
)
from shotgrid_mcp_server.logger import setup_logging

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()


class ShotGridTools:
    """Class containing tools for interacting with ShotGrid."""

    def __init__(self, server: FastMCP, sg: Shotgun) -> None:
        """Initialize ShotGridTools.

        Args:
            server: FastMCP server instance.
            sg: ShotGrid connection.
        """
        self.server = server
        self.sg = sg
        self.register_tools()

    @staticmethod
    def handle_error(err: Exception, operation: str) -> None:
        """Handle errors from tool operations.

        Args:
            err: Exception to handle.
            operation: Name of the operation that failed.

        Raises:
            ToolError: Always raised with formatted error message.
        """
        error_msg = str(err)
        if "Error getting thumbnail URL:" in error_msg:
            error_msg = error_msg.replace("Error getting thumbnail URL: ", "")
        if "Error downloading thumbnail:" in error_msg:
            error_msg = error_msg.replace("Error downloading thumbnail: ", "")
        if "Error executing tool" in error_msg:
            error_msg = error_msg.split(": ", 1)[1]

        # Standardize error messages
        error_msg = error_msg.replace("with id", "with ID")
        if "has no image" in error_msg:
            error_msg = "No thumbnail URL found"

        logger.error("Error in %s: %s", operation, error_msg)
        raise ToolError(f"Error executing tool {operation}: {error_msg}") from err

    @staticmethod
    def _serialize_entity(entity: Any) -> Dict[str, Any]:
        """Serialize entity data for JSON response.

        Args:
            entity: Entity data to serialize.

        Returns:
            Dict[str, Any]: Serialized entity data.
        """

        def _serialize_value(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: _serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [_serialize_value(v) for v in value]
            return value

        if not isinstance(entity, dict):
            return {}
        return {k: _serialize_value(v) for k, v in entity.items()}

    def _register_create_tools(self) -> None:
        """Register create tools."""

        @self.server.tool("create_entity")
        def create_entity(entity_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
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
                result = self.sg.create(entity_type, data)
                if result is None:
                    raise ToolError(f"Failed to create {entity_type}")

                # Return serialized entity
                return self._serialize_entity(result)
            except Exception as err:
                ShotGridTools.handle_error(err, operation="create_entity")
                raise  # This is needed to satisfy the type checker

        @self.server.tool("batch_create_entities")
        def batch_create_entities(entity_type: str, data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
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
                # Create entities one by one
                results = []
                for data in data_list:
                    result = self.sg.create(entity_type, data)
                    if result is None:
                        raise ToolError(f"Failed to create {entity_type}")
                    results.append(result)

                # Return serialized entities
                return [self._serialize_entity(result) for result in results]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="batch_create_entities")
                raise  # This is needed to satisfy the type checker

    def _register_read_tools(self) -> None:
        """Register read tools."""

        @self.server.tool("get_schema")
        def get_schema(entity_type: str) -> Dict[str, Any]:
            """Get schema for an entity type.

            Args:
                entity_type: Type of entity to get schema for.

            Returns:
                Dict[str, Any]: Entity schema.

            Raises:
                ToolError: If the schema retrieval fails.
            """
            try:
                result = self.sg.schema_field_read(entity_type)
                if result is None:
                    raise ToolError(f"Failed to read schema for {entity_type}")
                result["type"] = {
                    "data_type": {"value": "text"},
                    "properties": {"default_value": {"value": entity_type}},
                }
                return {"fields": dict(result)}  # Ensure we return Dict[str, Any]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="get_schema")
                raise  # This is needed to satisfy the type checker

    def _register_update_tools(self) -> None:
        """Register update tools."""

        @self.server.tool("update_entity")
        def update_entity(
            entity_type: str,
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
                result = self.sg.update(entity_type, entity_id, data)
                if result is None:
                    raise ToolError(f"Failed to update {entity_type} with ID {entity_id}")
                return None
            except Exception as err:
                ShotGridTools.handle_error(err, operation="update_entity")
                raise  # This is needed to satisfy the type checker

    def _register_delete_tools(self) -> None:
        """Register delete tools."""

        @self.server.tool("delete_entity")
        def delete_entity(entity_type: str, entity_id: int) -> None:
            """Delete an entity in ShotGrid.

            Args:
                entity_type: Type of entity to delete.
                entity_id: ID of entity to delete.

            Raises:
                ToolError: If the delete operation fails.
            """
            try:
                # First check if the entity exists
                entity = self.sg.find_one(entity_type, [["id", "is", entity_id]])
                if entity is None:
                    raise ToolError(f"Entity {entity_type} with ID {entity_id} not found")

                # Then try to delete it
                result = self.sg.delete(entity_type, entity_id)
                if result is False:  # ShotGrid API returns False on failure
                    raise ToolError(f"Failed to delete {entity_type} with ID {entity_id}")
                return None
            except Exception as err:
                ShotGridTools.handle_error(err, operation="delete_entity")
                raise  # This is needed to satisfy the type checker

    def _register_search_tools(self) -> None:
        """Register search tools."""

        @self.server.tool("search_entities")
        def search_entities(
            entity_type: str,
            filters: List[List[Any]],
            fields: Optional[List[str]] = None,
            order: Optional[List[Dict[str, str]]] = None,
            filter_operator: Optional[str] = None,
            limit: Optional[int] = None,
        ) -> List[Dict[str, str]]:
            """Find entities in ShotGrid.

            Args:
                entity_type: Type of entity to find.
                filters: List of filters to apply. Each filter is a list of [field, operator, value].
                fields: Optional list of fields to return.
                order: Optional list of fields to order by.
                filter_operator: Optional filter operator.
                limit: Optional limit on number of entities to return.

            Returns:
                List[Dict[str, str]]: List of entities found.

            Raises:
                ToolError: If the find operation fails.
            """
            try:
                # Process filters
                processed_filters = []
                for field, operator, value in filters:
                    if isinstance(value, str) and value.startswith("$"):
                        # Handle special values
                        if value == "$today":
                            value = datetime.now().strftime("%Y-%m-%d")
                    processed_filters.append([field, operator, value])

                result = self.sg.find(
                    entity_type,
                    processed_filters,
                    fields=fields,
                    order=order,
                    filter_operator=filter_operator,
                    limit=limit,
                )
                if result is None:
                    return [{"text": json.dumps({"entities": []})}]
                return [{"text": json.dumps({"entities": result})}]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="search_entities")
                raise  # This is needed to satisfy the type checker

        @self.server.tool("find_one_entity")
        def find_one_entity(
            entity_type: str,
            filters: List[List[Any]],
            fields: Optional[List[str]] = None,
            order: Optional[List[Dict[str, str]]] = None,
            filter_operator: Optional[str] = None,
        ) -> List[Dict[str, str]]:
            """Find a single entity in ShotGrid.

            Args:
                entity_type: Type of entity to find.
                filters: List of filters to apply. Each filter is a list of [field, operator, value].
                fields: Optional list of fields to return.
                order: Optional list of fields to order by.
                filter_operator: Optional filter operator.

            Returns:
                List[Dict[str, str]]: Entity found, or None if not found.

            Raises:
                ToolError: If the find operation fails.
            """
            try:
                result = self.sg.find_one(
                    entity_type,
                    filters,
                    fields=fields,
                    order=order,
                    filter_operator=filter_operator,
                )
                if result is None:
                    return [{"text": json.dumps({"text": None})}]
                return [{"text": json.dumps({"text": self._serialize_entity(result)})}]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="find_one_entity")
                raise  # This is needed to satisfy the type checker

    def _register_thumbnail_tools(self) -> None:
        """Register thumbnail tools."""

        @self.server.tool("get_thumbnail_url")
        def get_thumbnail_url(
            entity_type: str,
            entity_id: int,
            field_name: str = "image",
            size: Optional[str] = None,
        ) -> str:
            """Get thumbnail URL for an entity.

            Args:
                entity_type: Type of entity.
                entity_id: ID of entity.
                field_name: Name of field containing thumbnail.
                size: Optional size of thumbnail.

            Returns:
                str: Thumbnail URL.

            Raises:
                ToolError: If the URL retrieval fails.
            """
            try:
                result = self.sg.get_thumbnail_url(entity_type, entity_id, field_name)
                if not result:
                    raise ToolError("No thumbnail URL found")
                return str(result)
            except Exception as err:
                ShotGridTools.handle_error(err, operation="get_thumbnail_url")
                raise  # This is needed to satisfy the type checker

        @self.server.tool("download_thumbnail")
        def download_thumbnail(
            entity_type: str,
            entity_id: int,
            field_name: str = "image",
            file_path: Optional[str] = None,
        ) -> Dict[str, str]:
            """Download a thumbnail for an entity.

            Args:
                entity_type: Type of entity.
                entity_id: ID of entity.
                field_name: Name of field containing thumbnail.
                file_path: Optional path to save thumbnail to.

            Returns:
                Dict[str, str]: Path to downloaded thumbnail.

            Raises:
                ToolError: If the download fails.
            """
            try:
                # Get thumbnail URL
                url = self.sg.get_thumbnail_url(entity_type, entity_id, field_name)
                if not url:
                    raise ToolError("No thumbnail URL found")

                # Download thumbnail
                result = self.sg.download_attachment({"url": url}, file_path)
                if result is None:
                    raise ToolError("Failed to download thumbnail")
                return {"file_path": str(result)}
            except Exception as err:
                ShotGridTools.handle_error(err, operation="download_thumbnail")
                raise  # This is needed to satisfy the type checker

    def register_tools(self) -> None:
        """Register all tools with the FastMCP server."""
        # Create tools
        self._register_create_tools()

        # Read tools
        self._register_read_tools()

        # Update tools
        self._register_update_tools()

        # Delete tools
        self._register_delete_tools()

        # Search tools
        self._register_search_tools()

        # Thumbnail tools
        self._register_thumbnail_tools()


def create_server(factory: Optional[ShotgunClientFactory] = None) -> FastMCP:
    """Create a FastMCP server instance.

    Args:
        factory: Optional factory for creating ShotGrid clients, used in testing.

    Returns:
        FastMCP: The server instance.

    Raises:
        Exception: If server creation fails.
    """
    try:
        mcp = FastMCP(name="shotgrid-server")
        logger.debug("Created FastMCP instance")

        # Create tools instance and register tools using connection context
        with ShotGridConnectionContext(factory=factory) as sg:
            tools = ShotGridTools(mcp, sg)
            tools.register_tools()
            logger.debug("Registered all tools")
            return mcp
    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


def main() -> None:
    """Entry point for the ShotGrid MCP server."""
    app = create_server()
    app.run()


if __name__ == "__main__":
    main()
else:
    # When imported, create a mock server for testing
    from shotgrid_mcp_server.connection_pool import MockShotgunFactory

    mock_factory = MockShotgunFactory(
        schema_path="tests/data/schema.bin",
        schema_entity_path="tests/data/entity_schema.bin",
    )
    app = create_server(factory=mock_factory)
