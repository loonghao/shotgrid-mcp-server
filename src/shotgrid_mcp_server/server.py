"""ShotGrid MCP server implementation."""

# Import built-in modules
import json
import logging
import os
from typing import Any, Dict, List, Optional, Tuple, Union

# Import third-party modules
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.logger import setup_logging

# Import local modules
from .utils import DateTimeEncoder

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

    def _register_create_tools(self) -> None:
        """Register create tools."""
        @self.server.tool("create_entity")
        def create_entity(
            entity_type: str,
            data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Create an entity in ShotGrid.

            Args:
                entity_type: Type of entity to create.
                data: Data to set on the entity.

            Returns:
                Dict[str, Any]: Created entity.

            Raises:
                ToolError: If the create operation fails.
            """
            try:
                result = self.sg.create(entity_type, data)
                return result
            except Exception as err:
                ShotGridTools.handle_error(err, operation="create_entity")

        @self.server.tool("batch_create_entities")
        def batch_create_entities(
            entity_type: str,
            data_list: List[Dict[str, Any]],
        ) -> List[Dict[str, Any]]:
            """Create multiple entities in ShotGrid.

            Args:
                entity_type: Type of entity to create.
                data_list: List of data to set on each entity.

            Returns:
                List[Dict[str, Any]]: List of created entities.

            Raises:
                ToolError: If the batch create operation fails.
            """
            try:
                result = self.sg.batch(
                    [{"request_type": "create", "entity_type": entity_type, "data": d} for d in data_list]
                )
                return result
            except Exception as err:
                ShotGridTools.handle_error(err, operation="batch_create_entities")

    def _register_read_tools(self) -> None:
        """Register read tools."""
        @self.server.tool("get_schema")
        def get_schema(
            entity_type: str,
        ) -> Dict[str, Any]:
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
                result["type"] = {"data_type": {"value": "text"}, "properties": {"default_value": {"value": entity_type}}}
                return {"fields": result}
            except Exception as err:
                ShotGridTools.handle_error(err, operation="get_schema")

    def _register_update_tools(self) -> None:
        """Register update tools."""
        @self.server.tool("update_entity")
        def update_entity(
            entity_type: str,
            entity_id: int,
            data: Dict[str, Any],
        ) -> Dict[str, Any]:
            """Update an entity in ShotGrid.

            Args:
                entity_type: Type of entity to update.
                entity_id: ID of entity to update.
                data: Data to update on the entity.

            Returns:
                Dict[str, Any]: Updated entity.

            Raises:
                ToolError: If the update operation fails.
            """
            try:
                result = self.sg.update(entity_type, entity_id, data)
                return result
            except Exception as err:
                ShotGridTools.handle_error(err, operation="update_entity")

    def _register_delete_tools(self) -> None:
        """Register delete tools."""
        @self.server.tool("delete_entity")
        def delete_entity(
            entity_type: str,
            entity_id: int,
        ) -> None:
            """Delete an entity in ShotGrid.

            Args:
                entity_type: Type of entity to delete.
                entity_id: ID of entity to delete.

            Raises:
                ToolError: If the delete operation fails.
            """
            try:
                self.sg.delete(entity_type, entity_id)
            except Exception as err:
                ShotGridTools.handle_error(err, operation="delete_entity")

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
                    else:
                        processed_filters.append([field, operator, value])

                result = self.sg.find(
                    entity_type,
                    processed_filters,
                    fields=fields,
                    order=order,
                    filter_operator=filter_operator,
                    limit=limit,
                )
                return [{"text": json.dumps({"entities": result})}]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="search_entities")

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
                return [{"text": json.dumps({"text": result})}] if result else [{"text": json.dumps({"text": None})}]
            except Exception as err:
                ShotGridTools.handle_error(err, operation="find_one_entity")

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
                return result
            except Exception as err:
                ShotGridTools.handle_error(err, operation="get_thumbnail_url")

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
                return {"file_path": result}
            except Exception as err:
                ShotGridTools.handle_error(err, operation="download_thumbnail")

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

        # Create tools instance and register tools
        sg = Shotgun(os.getenv("SHOTGRID_URL"), os.getenv("SCRIPT_NAME"), os.getenv("SCRIPT_KEY"))
        tools = ShotGridTools(mcp, sg)
        tools.register_tools()
        logger.info("Registered all tools")

        # Log environment information
        logger.info("Environment information:")
        logger.info("  ShotGrid URL: %s", os.getenv("SHOTGRID_URL"))
        logger.info("  Script Name: %s", os.getenv("SCRIPT_NAME"))

        return mcp

    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


def main():
    """Entry point for the ShotGrid MCP server."""
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
