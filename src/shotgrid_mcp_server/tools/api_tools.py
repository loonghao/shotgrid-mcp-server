"""API tools for ShotGrid MCP server.

This module contains direct access to ShotGrid API methods, providing more flexibility
for advanced operations.
"""

from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType


def register_api_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register API tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Register CRUD tools
    register_crud_tools(server, sg)

    # Register advanced query tools
    register_advanced_query_tools(server, sg)

    # Register schema tools
    register_schema_tools(server, sg)

    # Register file tools
    register_file_tools(server, sg)

    # Register activity stream tools
    register_activity_stream_tools(server, sg)


def _register_find_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register find tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.find")
    def sg_find(
        entity_type: EntityType,
        filters: List[Any],
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
        retired_only: bool = False,
        page: Optional[int] = None,
        include_archived_projects: bool = True,
        additional_filter_presets: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Find entities in ShotGrid.

        This is a direct wrapper around the ShotGrid API's find method.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply.
            fields: Optional list of fields to return.
            order: Optional list of fields to order by.
            filter_operator: Optional filter operator.
            limit: Optional limit on number of entities to return.
            retired_only: Whether to return only retired entities.
            page: Optional page number for pagination.
            include_archived_projects: Whether to include archived projects.
            additional_filter_presets: Optional additional filter presets.

        Returns:
            List of entities found.
        """
        try:
            result = sg.find(
                entity_type,
                filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
                retired_only=retired_only,
                page=page,
                include_archived_projects=include_archived_projects,
                additional_filter_presets=additional_filter_presets,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.find")
            raise

    @server.tool("sg.find_one")
    def sg_find_one(
        entity_type: EntityType,
        filters: List[Any],
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        retired_only: bool = False,
        include_archived_projects: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Find a single entity in ShotGrid.

        This is a direct wrapper around the ShotGrid API's find_one method.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply.
            fields: Optional list of fields to return.
            order: Optional list of fields to order by.
            filter_operator: Optional filter operator.
            retired_only: Whether to return only retired entities.
            include_archived_projects: Whether to include archived projects.

        Returns:
            Entity found, or None if not found.
        """
        try:
            result = sg.find_one(
                entity_type,
                filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
                retired_only=retired_only,
                include_archived_projects=include_archived_projects,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.find_one")
            raise


def _register_create_update_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register create and update tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.create")
    def sg_create(
        entity_type: EntityType,
        data: Dict[str, Any],
        return_fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an entity in ShotGrid.

        This is a direct wrapper around the ShotGrid API's create method.

        Args:
            entity_type: Type of entity to create.
            data: Data for the new entity.
            return_fields: Optional list of fields to return.

        Returns:
            Created entity.
        """
        try:
            result = sg.create(entity_type, data, return_fields=return_fields)
            return result
        except Exception as err:
            handle_error(err, operation="sg.create")
            raise

    @server.tool("sg.update")
    def sg_update(
        entity_type: EntityType,
        entity_id: int,
        data: Dict[str, Any],
        multi_entity_update_mode: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update an entity in ShotGrid.

        This is a direct wrapper around the ShotGrid API's update method.

        Args:
            entity_type: Type of entity to update.
            entity_id: ID of entity to update.
            data: Data to update.
            multi_entity_update_mode: Optional mode for multi-entity updates.

        Returns:
            Updated entity.
        """
        try:
            result = sg.update(
                entity_type,
                entity_id,
                data,
                multi_entity_update_mode=multi_entity_update_mode,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.update")
            raise


def _register_delete_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register delete and revive tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.delete")
    def sg_delete(entity_type: EntityType, entity_id: int) -> bool:
        """Delete an entity in ShotGrid.

        This is a direct wrapper around the ShotGrid API's delete method.

        Args:
            entity_type: Type of entity to delete.
            entity_id: ID of entity to delete.

        Returns:
            True if successful, False otherwise.
        """
        try:
            result = sg.delete(entity_type, entity_id)
            return result
        except Exception as err:
            handle_error(err, operation="sg.delete")
            raise

    @server.tool("sg.revive")
    def sg_revive(entity_type: EntityType, entity_id: int) -> bool:
        """Revive a deleted entity in ShotGrid.

        This is a direct wrapper around the ShotGrid API's revive method.

        Args:
            entity_type: Type of entity to revive.
            entity_id: ID of entity to revive.

        Returns:
            True if successful, False otherwise.
        """
        try:
            result = sg.revive(entity_type, entity_id)
            return result
        except Exception as err:
            handle_error(err, operation="sg.revive")
            raise


def _register_batch_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register batch tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.batch")
    def sg_batch(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform a batch operation in ShotGrid.

        This is a direct wrapper around the ShotGrid API's batch method.

        Args:
            requests: List of batch requests.

        Returns:
            List of results from the batch operation.
        """
        try:
            result = sg.batch(requests)
            return result
        except Exception as err:
            handle_error(err, operation="sg.batch")
            raise


def register_crud_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register CRUD tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Register find tools
    _register_find_tools(server, sg)

    # Register create and update tools
    _register_create_update_tools(server, sg)

    # Register delete tools
    _register_delete_tools(server, sg)

    # Register batch tools
    _register_batch_tools(server, sg)


def register_advanced_query_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register advanced query tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.summarize")
    def sg_summarize(
        entity_type: EntityType,
        filters: List[Any],
        summary_fields: List[Dict[str, Any]],
        filter_operator: Optional[str] = None,
        grouping: Optional[List[Dict[str, Any]]] = None,
        include_archived_projects: bool = True,
    ) -> Dict[str, Any]:
        """Summarize data in ShotGrid.

        This is a direct wrapper around the ShotGrid API's summarize method.

        Args:
            entity_type: Type of entity to summarize.
            filters: List of filters to apply.
            summary_fields: List of fields to summarize.
            filter_operator: Optional filter operator.
            grouping: Optional grouping.
            include_archived_projects: Whether to include archived projects.

        Returns:
            Summarized data.
        """
        try:
            result = sg.summarize(
                entity_type,
                filters,
                summary_fields,
                filter_operator=filter_operator,
                grouping=grouping,
                include_archived_projects=include_archived_projects,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.summarize")
            raise

    @server.tool("sg.text_search")
    def sg_text_search(
        text: str,
        entity_types: List[EntityType],
        project_ids: Optional[List[int]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a text search in ShotGrid.

        This is a direct wrapper around the ShotGrid API's text_search method.

        Args:
            text: Text to search for.
            entity_types: List of entity types to search.
            project_ids: Optional list of project IDs to search in.
            limit: Optional limit on number of results.

        Returns:
            Search results.
        """
        try:
            result = sg.text_search(
                text,
                entity_types,
                project_ids=project_ids,
                limit=limit,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.text_search")
            raise


def register_schema_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register schema tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.schema_entity_read")
    def sg_schema_entity_read() -> Dict[str, Dict[str, Any]]:
        """Read entity schema from ShotGrid.

        This is a direct wrapper around the ShotGrid API's schema_entity_read method.

        Returns:
            Entity schema.
        """
        try:
            result = sg.schema_entity_read()
            return result
        except Exception as err:
            handle_error(err, operation="sg.schema_entity_read")
            raise

    @server.tool("sg.schema_field_read")
    def sg_schema_field_read(
        entity_type: EntityType,
        field_name: Optional[str] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Read field schema from ShotGrid.

        This is a direct wrapper around the ShotGrid API's schema_field_read method.

        Args:
            entity_type: Type of entity to read schema for.
            field_name: Optional name of field to read schema for.

        Returns:
            Field schema.
        """
        try:
            result = sg.schema_field_read(entity_type, field_name=field_name)
            return result
        except Exception as err:
            handle_error(err, operation="sg.schema_field_read")
            raise


def register_file_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register file tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.upload")
    def sg_upload(
        entity_type: EntityType,
        entity_id: int,
        path: str,
        field_name: str = "sg_uploaded_movie",
        display_name: Optional[str] = None,
        tag_list: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Upload a file to ShotGrid.

        This is a direct wrapper around the ShotGrid API's upload method.

        Args:
            entity_type: Type of entity to upload to.
            entity_id: ID of entity to upload to.
            path: Path to file to upload.
            field_name: Name of field to upload to.
            display_name: Optional display name for the file.
            tag_list: Optional list of tags for the file.

        Returns:
            Upload result.
        """
        try:
            result = sg.upload(
                entity_type,
                entity_id,
                path,
                field_name=field_name,
                display_name=display_name,
                tag_list=tag_list,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.upload")
            raise

    @server.tool("sg.download_attachment")
    def sg_download_attachment(
        attachment: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> str:
        """Download an attachment from ShotGrid.

        This is a direct wrapper around the ShotGrid API's download_attachment method.

        Args:
            attachment: Attachment to download.
            file_path: Optional path to save the file to.

        Returns:
            Path to downloaded file.
        """
        try:
            result = sg.download_attachment(attachment, file_path=file_path)
            return result
        except Exception as err:
            handle_error(err, operation="sg.download_attachment")
            raise


def register_activity_stream_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register activity stream tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg.activity_stream_read")
    def sg_activity_stream_read(
        entity_type: EntityType,
        entity_id: int,
        limit: Optional[int] = None,
        max_id: Optional[int] = None,
        min_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Read activity stream from ShotGrid.

        This is a direct wrapper around the ShotGrid API's activity_stream_read method.

        Args:
            entity_type: Type of entity to read activity stream for.
            entity_id: ID of entity to read activity stream for.
            limit: Optional limit on number of activities to return.
            max_id: Optional maximum activity ID to return.
            min_id: Optional minimum activity ID to return.

        Returns:
            Activity stream data.
        """
        try:
            result = sg.activity_stream_read(
                entity_type,
                entity_id,
                limit=limit,
                max_id=max_id,
                min_id=min_id,
            )
            return result
        except Exception as err:
            handle_error(err, operation="sg.activity_stream_read")
            raise
