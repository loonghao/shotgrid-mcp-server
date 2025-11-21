"""API tools for ShotGrid MCP server.

This module contains direct access to ShotGrid API methods, providing more flexibility
for advanced operations.
"""

from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType


def _get_sg(fallback: Shotgun) -> Shotgun:
    """Get current ShotGrid connection (from HTTP headers or fallback).

    Args:
        fallback: Fallback ShotGrid connection to use if no HTTP headers are present.

    Returns:
        Active ShotGrid connection.
    """
    from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection

    return get_current_shotgrid_connection(fallback_sg=fallback)


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

    @server.tool("sg_find")
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
        """Find entities in ShotGrid using the native ShotGrid API find method.

        Use this tool for direct access to ShotGrid's find API with full control over all parameters.
        This is a low-level tool that provides maximum flexibility.

        Common use cases:
        - When you need retired_only or include_archived_projects parameters
        - When you need additional_filter_presets
        - When you need precise control over pagination
        - When other search tools don't provide the needed parameters

        For most searches, use `search_entities` instead (simpler, auto-corrects field names).
        For searches with related fields, use `search_entities_with_related`.
        For time-based searches, use `sg_search_advanced`.
        For text searches, use `sg_text_search`.

        Args:
            entity_type: Type of entity to find.
                        Examples: "Shot", "Asset", "Task", "Version", "HumanUser"

            filters: List of filter conditions.
                    Format: [["field_name", "operator", value], ...]

                    Examples:
                    [["project", "is", {"type": "Project", "id": 123}]]
                    [["sg_status_list", "is", "ip"]]
                    [["code", "contains", "hero"]]

            fields: Optional list of fields to return.
                   If not provided, returns default fields.

                   Example: ["code", "description", "sg_status_list"]

            order: Optional sort order.
                  Format: [{"field_name": "field", "direction": "asc|desc"}]

                  Example: [{"field_name": "created_at", "direction": "desc"}]

            filter_operator: Logical operator for combining filters.
                           Values: "all" (AND, default) or "any" (OR)

            limit: Optional maximum number of entities to return.
                  MUST be a positive integer (1, 2, 3, ...) if provided.
                  Do NOT pass 0, negative numbers, or non-integer values.

                  Examples:
                  - limit=50 (correct)
                  - limit=100 (correct)
                  - limit=0 (WRONG - will cause error)
                  - limit=-1 (WRONG - will cause error)

            retired_only: Whether to return only retired (deleted) entities.
                         Default: False (return active entities)
                         Set to True to find deleted entities.

            page: Optional page number for pagination (1-based).
                 MUST be a positive integer (1, 2, 3, ...) if provided.
                 Used with limit for pagination.
                 Do NOT pass 0 or negative numbers.

                 Examples:
                 - page=1 (first page, correct)
                 - page=2 (second page, correct)
                 - page=0 (WRONG - will cause error)
                 - page=-1 (WRONG - will cause error)

            include_archived_projects: Whether to include entities from archived projects.
                                      Default: True
                                      Set to False to exclude archived projects.

            additional_filter_presets: Optional additional filter presets.
                                      Advanced parameter for complex filtering.

        Returns:
            List of entities found. Each entity is a dictionary with requested fields.

            Example:
            [
                {
                    "type": "Shot",
                    "id": 1234,
                    "code": "SH001",
                    "sg_status_list": "ip"
                },
                ...
            ]

        Raises:
            ToolError: If entity_type is invalid, filters are malformed, or limit is not a positive integer.

        Examples:
            Find active shots in a project:
            {
                "entity_type": "Shot",
                "filters": [["project", "is", {"type": "Project", "id": 123}]],
                "fields": ["code", "sg_status_list"],
                "limit": 50
            }

            Find retired tasks:
            {
                "entity_type": "Task",
                "filters": [["project", "is", {"type": "Project", "id": 123}]],
                "retired_only": true,
                "limit": 100
            }

            Find entities excluding archived projects:
            {
                "entity_type": "Asset",
                "filters": [["sg_asset_type", "is", "Character"]],
                "include_archived_projects": false,
                "limit": 50
            }

        Important:
            - limit parameter MUST be a positive integer (1, 2, 3, ...) or omitted
            - Do NOT pass limit=0 or negative values
            - This is a low-level API wrapper; use higher-level tools when possible
            - For most searches, `search_entities` is recommended (simpler, safer)
        """
        try:
            # Validate limit parameter
            if limit is not None and limit <= 0:
                raise ValueError(
                    "limit parameter must be a positive integer (1, 2, 3, ...). Do not pass 0 or negative values."
                )

            # Validate page parameter
            if page is not None and page <= 0:
                raise ValueError(
                    "page parameter must be a positive integer (1, 2, 3, ...). Do not pass 0 or negative values."
                )

            result = _get_sg(sg).find(
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

    @server.tool("sg_find_one")
    def sg_find_one(
        entity_type: EntityType,
        filters: List[Any],
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        retired_only: bool = False,
        include_archived_projects: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Find a single entity in ShotGrid using the native ShotGrid API find_one method.

        Use this tool to find exactly one entity matching the filters.
        Returns the first matching entity, or None if no match is found.

        Common use cases:
        - Find a specific entity by unique identifier (code, name)
        - Find the most recent entity matching criteria (with order)
        - When you need retired_only or include_archived_projects parameters
        - When you need precise control over which entity is returned

        For most single entity searches, use `find_one_entity` instead (simpler, auto-corrects field names).
        For finding multiple entities, use `search_entities` or `sg_find`.

        Args:
            entity_type: Type of entity to find.
                        Examples: "Shot", "Asset", "Task", "Version", "HumanUser"

            filters: List of filter conditions.
                    Format: [["field_name", "operator", value], ...]

                    Examples:
                    [["code", "is", "SH001"]]
                    [["project", "is", {"type": "Project", "id": 123}]]

            fields: Optional list of fields to return.
                   If not provided, returns default fields.

                   Example: ["code", "description", "sg_status_list"]

            order: Optional sort order to determine which entity is returned.
                  Format: [{"field_name": "field", "direction": "asc|desc"}]

                  Example: [{"field_name": "created_at", "direction": "desc"}]
                  (returns the most recently created entity)

            filter_operator: Logical operator for combining filters.
                           Values: "all" (AND, default) or "any" (OR)

            retired_only: Whether to search only retired (deleted) entities.
                         Default: False (search active entities)
                         Set to True to find deleted entities.

            include_archived_projects: Whether to include entities from archived projects.
                                      Default: True
                                      Set to False to exclude archived projects.

        Returns:
            Entity found (dictionary with requested fields), or None if no match.

            Example (entity found):
            {
                "type": "Shot",
                "id": 1234,
                "code": "SH001",
                "sg_status_list": "ip"
            }

            Example (no match):
            None

        Raises:
            ToolError: If entity_type is invalid or filters are malformed.

        Examples:
            Find shot by code:
            {
                "entity_type": "Shot",
                "filters": [["code", "is", "SH001"]],
                "fields": ["code", "sg_status_list", "description"]
            }

            Find most recent version:
            {
                "entity_type": "Version",
                "filters": [["entity", "is", {"type": "Shot", "id": 1234}]],
                "order": [{"field_name": "created_at", "direction": "desc"}],
                "fields": ["code", "sg_status_list"]
            }

            Find retired task:
            {
                "entity_type": "Task",
                "filters": [["id", "is", 5678]],
                "retired_only": true
            }

        Important:
            - Returns only the FIRST matching entity (use order to control which one)
            - Returns None if no entity matches the filters
            - For most searches, `find_one_entity` is recommended (simpler, safer)
            - This is a low-level API wrapper; use higher-level tools when possible
        """
        try:
            result = _get_sg(sg).find_one(
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

    @server.tool("sg_create")
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
            result = _get_sg(sg).create(entity_type, data, return_fields=return_fields)
            return result
        except Exception as err:
            handle_error(err, operation="sg.create")
            raise

    @server.tool("sg_update")
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
            result = _get_sg(sg).update(
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

    @server.tool("sg_delete")
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
            result = _get_sg(sg).delete(entity_type, entity_id)
            return result
        except Exception as err:
            handle_error(err, operation="sg.delete")
            raise

    @server.tool("sg_revive")
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
            result = _get_sg(sg).revive(entity_type, entity_id)
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

    @server.tool("sg_batch")
    def sg_batch(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform a batch operation in ShotGrid.

        This is a direct wrapper around the ShotGrid API's batch method.

        Args:
            requests: List of batch requests.

        Returns:
            List of results from the batch operation.
        """
        try:
            result = _get_sg(sg).batch(requests)
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

    @server.tool("sg_summarize")
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
            result = _get_sg(sg).summarize(
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

    @server.tool("sg_text_search")
    def sg_text_search(
        text: str,
        entity_types: List[EntityType],
        project_ids: Optional[List[int]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a full-text search across multiple entity types in ShotGrid.

        Use this tool when you need to search for text across multiple entity types
        or when you don't know which specific entity type contains the data you're
        looking for. This is ShotGrid's global search functionality.

        Common use cases:
        - Search for a shot/asset/task by name across all entity types
        - Find all entities mentioning a specific keyword
        - Search across multiple projects
        - Quick lookup when entity type is unknown
        - Search for user-entered text (like a search bar)

        For structured searches with filters, use `search_entities` instead.
        For searches with related data, use `search_entities_with_related` instead.
        For time-based searches, use `sg_search_advanced` instead.

        How Text Search Works:
            ShotGrid's text search looks for matches in key text fields across
            entity types, including:
            - code: Entity code/name
            - description: Entity description
            - name: Entity name (for some types)
            - Other searchable text fields

            The search is case-insensitive and supports partial matches.

        Args:
            text: The text to search for.
                 Can be a partial match (e.g., "anim" will match "animation").
                 Case-insensitive.

                 Examples:
                 - "SH001" - Find entities with code containing SH001
                 - "animation" - Find entities mentioning animation
                 - "John" - Find entities related to user John

            entity_types: List of entity types to search within.
                         Must provide at least one entity type.

                         Common types:
                         - "Shot": Shots in sequences
                         - "Asset": Assets (characters, props, environments)
                         - "Task": Work assignments
                         - "Version": Published versions
                         - "Note": Notes and comments
                         - "PublishedFile": Published files
                         - "Sequence": Shot sequences
                         - "HumanUser": Users

                         Examples:
                         - ["Shot"] - Search only shots
                         - ["Shot", "Asset"] - Search shots and assets
                         - ["Shot", "Asset", "Task", "Version"] - Search multiple types

            project_ids: Optional list of project IDs to limit search scope.
                        If omitted, searches across all projects the user has access to.

                        Examples:
                        - None - Search all projects
                        - [123] - Search only project 123
                        - [123, 456] - Search projects 123 and 456

            limit: Optional maximum number of results per entity type.
                  If omitted, returns all matches (up to ShotGrid's internal limit).

                  Examples:
                  - None - Return all matches
                  - 10 - Return up to 10 results per entity type
                  - 100 - Return up to 100 results per entity type

        Returns:
            Dictionary with entity types as keys and lists of matching entities as values.
            Each entity contains basic fields (id, type, code/name, etc.).

            Format:
            {
                "Shot": [
                    {"id": 1234, "type": "Shot", "code": "SH001", ...},
                    {"id": 1235, "type": "Shot", "code": "SH002", ...}
                ],
                "Asset": [
                    {"id": 5678, "type": "Asset", "code": "CHAR_hero", ...}
                ],
                ...
            }

            Example:
            {
                "Shot": [
                    {
                        "id": 1234,
                        "type": "Shot",
                        "code": "SH001_animation",
                        "project": {"id": 123, "type": "Project", "name": "Demo"}
                    }
                ],
                "Task": [
                    {
                        "id": 5678,
                        "type": "Task",
                        "content": "Animation",
                        "entity": {"id": 1234, "type": "Shot", "name": "SH001"}
                    }
                ]
            }

        Raises:
            ToolError: If entity_types is empty, contains invalid types, or the
                      ShotGrid API returns an error.

        Examples:
            Search for "animation" across shots and tasks:
            {
                "text": "animation",
                "entity_types": ["Shot", "Task"]
            }

            Search for shot "SH001" in specific project:
            {
                "text": "SH001",
                "entity_types": ["Shot"],
                "project_ids": [123]
            }

            Search for user "John" across multiple types:
            {
                "text": "John",
                "entity_types": ["HumanUser", "Task", "Version"],
                "limit": 20
            }

            Quick search across all common types:
            {
                "text": "hero",
                "entity_types": ["Shot", "Asset", "Task", "Version", "PublishedFile"],
                "limit": 10
            }

        Performance Considerations:
            - Text search is optimized for speed but may not return all fields
            - For detailed entity data, use the returned IDs with `find_one_entity`
            - Searching many entity types may be slower than searching one
            - Use project_ids to limit scope and improve performance

        Note:
            - This is a wrapper around ShotGrid's native text_search API
            - Results are grouped by entity type
            - Each entity type can return up to `limit` results
            - The search looks in predefined searchable fields (not all fields)
            - For exact field matching, use `search_entities` with filters instead
            - Empty results for an entity type are omitted from the response
        """
        try:
            result = _get_sg(sg).text_search(
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

    @server.tool("sg_schema_entity_read")
    def sg_schema_entity_read() -> Dict[str, Dict[str, Any]]:
        """Read entity schema from ShotGrid.

        This is a direct wrapper around the ShotGrid API's schema_entity_read method.

        Returns:
            Entity schema.
        """
        try:
            result = _get_sg(sg).schema_entity_read()
            return result
        except Exception as err:
            handle_error(err, operation="sg.schema_entity_read")
            raise

    @server.tool("sg_schema_field_read")
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
            result = _get_sg(sg).schema_field_read(entity_type, field_name=field_name)
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

    @server.tool("sg_upload")
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
            result = _get_sg(sg).upload(
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

    @server.tool("sg_download_attachment")
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
            result = _get_sg(sg).download_attachment(attachment, file_path=file_path)
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

    @server.tool("sg_activity_stream_read")
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
            result = _get_sg(sg).activity_stream_read(
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
