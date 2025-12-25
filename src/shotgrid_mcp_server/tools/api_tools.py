"""API tools for ShotGrid MCP server.

This module contains direct access to ShotGrid API methods, providing more flexibility
for advanced operations.
"""

from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.response_models import generate_entity_url
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.utils import (
    normalize_batch_request,
    normalize_data_dict,
    normalize_filters,
    normalize_grouping,
)


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

    # Register note thread tools
    register_note_thread_tools(server, sg)

    # Register project tools
    register_project_tools(server, sg)

    # Register preferences tools
    register_preferences_tools(server, sg)


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

        **When to use this tool:**
        - You need retired_only parameter to find deleted entities
        - You need include_archived_projects parameter
        - You need additional_filter_presets for complex filtering
        - You need precise control over pagination (page parameter)
        - Other search tools don't provide the needed parameters
        - You need direct access to ShotGrid API without field name normalization

        **When NOT to use this tool:**
        - For basic searches - Use `search_entities` instead (simpler, auto-corrects field names)
        - For searches with related entity data - Use `search_entities_with_related` instead
        - For time-based filtering - Use `sg_search_advanced` instead
        - For full-text search - Use `sg_text_search` instead
        - For finding a single entity - Use `find_one_entity` instead

        **Common use cases:**
        - Find retired (deleted) entities: Set retired_only=True
        - Exclude archived projects: Set include_archived_projects=False
        - Paginate through large result sets: Use limit and page parameters
        - Apply complex filter presets: Use additional_filter_presets

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
            - Integer entity IDs in filters are automatically normalized to dict format
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

            # Normalize filters to convert integer entity IDs to dict format
            normalized_filters = normalize_filters(filters)

            # Build kwargs, only including optional parameters if they have values
            kwargs: Dict[str, Any] = {
                "fields": fields,
                "order": order,
                "filter_operator": filter_operator,
                "retired_only": retired_only,
                "include_archived_projects": include_archived_projects,
            }

            # Only add limit if it's not None
            if limit is not None:
                kwargs["limit"] = limit

            # Only add page if it's not None
            if page is not None:
                kwargs["page"] = page

            # Only add additional_filter_presets if it's not None
            if additional_filter_presets is not None:
                kwargs["additional_filter_presets"] = additional_filter_presets

            result = _get_sg(sg).find(
                entity_type,
                normalized_filters,
                **kwargs,
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

        **When to use this tool:**
        - You need to find exactly one entity matching the filters
        - You want to find a specific entity by unique identifier (code, name)
        - You need to find the most recent entity matching criteria (with order)
        - You need retired_only or include_archived_projects parameters
        - You need precise control over which entity is returned
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - For most single entity searches - Use `find_one_entity` instead (simpler, auto-corrects field names)
        - To find multiple entities - Use `search_entities` or `sg_find` instead
        - To search by text - Use `sg_text_search` instead
        - To get related entity data - Use `search_entities_with_related` instead

        **Common use cases:**
        - Find a specific entity by unique identifier (code, name)
        - Find the most recent entity matching criteria (with order)
        - When you need retired_only or include_archived_projects parameters
        - When you need precise control over which entity is returned

        **Note:** Returns the first matching entity, or None if no match is found.
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
            - Integer entity IDs in filters are automatically normalized to dict format
        """
        try:
            # Normalize filters to convert integer entity IDs to dict format
            normalized_filters = normalize_filters(filters)

            result = _get_sg(sg).find_one(
                entity_type,
                normalized_filters,
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
        """Create an entity in ShotGrid using the native ShotGrid API create method.

        **When to use this tool:**
        - You need low-level direct access to the ShotGrid API
        - You want the raw API response without additional processing
        - You're implementing custom logic that requires native API behavior

        **When NOT to use this tool:**
        - For most use cases - Use `create_entity` instead (better validation and error handling)
        - To create multiple entities - Use `batch_create_entities` or `batch_operations` instead

        **Note:** This is a direct wrapper around the ShotGrid API's create method.
        For most use cases, prefer using `create_entity` instead.
        Integer entity IDs in data are automatically normalized to dict format.

        Args:
            entity_type: Type of entity to create.
                        Example: "Shot"

            data: Data for the new entity.
                 Example: {"code": "SH001", "project": {"type": "Project", "id": 123}}
                 Note: Integer entity IDs (e.g., {"project": 123}) will be automatically
                 normalized to dict format.

            return_fields: Optional list of fields to return.
                          Example: ["code", "sg_status_list"]

        Returns:
            Created entity with raw ShotGrid API response, including sg_url field.
        """
        try:
            current_sg = _get_sg(sg)
            # Normalize data to convert integer entity IDs to dict format
            normalized_data = normalize_data_dict(data)
            result = current_sg.create(entity_type, normalized_data, return_fields=return_fields)
            # Add sg_url to the result
            entity_id = result.get("id") if isinstance(result, dict) else None
            if entity_id:
                result["sg_url"] = generate_entity_url(current_sg.base_url, entity_type, entity_id)
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
        """Update an entity in ShotGrid using the native ShotGrid API update method.

        **When to use this tool:**
        - You need low-level direct access to the ShotGrid API
        - You want the raw API response without additional processing
        - You need multi_entity_update_mode parameter

        **When NOT to use this tool:**
        - For most use cases - Use `update_entity` instead (better validation and error handling)
        - To update multiple entities - Use `batch_operations` instead

        **Note:** This is a direct wrapper around the ShotGrid API's update method.
        For most use cases, prefer using `update_entity` instead.
        Integer entity IDs in data are automatically normalized to dict format.

        Args:
            entity_type: Type of entity to update.
                        Example: "Shot"

            entity_id: ID of entity to update.
                      Example: 1234

            data: Data to update.
                 Example: {"sg_status_list": "ip"}
                 Note: Integer entity IDs (e.g., {"project": 123}) will be automatically
                 normalized to dict format.

            multi_entity_update_mode: Optional mode for multi-entity updates.

        Returns:
            Updated entity with raw ShotGrid API response.
        """
        try:
            # Normalize data to convert integer entity IDs to dict format
            normalized_data = normalize_data_dict(data)
            result = _get_sg(sg).update(
                entity_type,
                entity_id,
                normalized_data,
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
    def sg_delete(entity_type: EntityType, entity_id: int) -> Dict[str, Any]:
        """Delete an entity in ShotGrid using the native ShotGrid API delete method.

        **When to use this tool:**
        - You need low-level direct access to the ShotGrid API
        - You want to delete an entity directly

        **When NOT to use this tool:**
        - For most use cases - Use `delete_entity` instead (better error handling and response format)

        **Note:** This is a direct wrapper around the ShotGrid API's delete method.
        For most use cases, prefer using `delete_entity` instead.

        Args:
            entity_type: Type of entity to delete.
                        Example: "Shot"

            entity_id: ID of entity to delete.
                      Example: 1234

        Returns:
            Dictionary with delete operation result including:
            - success: Whether the delete was successful
            - entity_type: The type of entity deleted
            - entity_id: The ID of the deleted entity
            - message: AI-friendly status message
        """
        from shotgrid_mcp_server.response_models import DeleteResult

        try:
            result = _get_sg(sg).delete(entity_type, entity_id)
            return DeleteResult(
                success=bool(result),
                entity_type=entity_type,
                entity_id=entity_id,
                message=f"Successfully deleted {entity_type} with ID {entity_id}"
                if result
                else f"Failed to delete {entity_type} with ID {entity_id}",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="sg.delete")
            raise

    @server.tool("sg_revive")
    def sg_revive(entity_type: EntityType, entity_id: int) -> Dict[str, Any]:
        """Revive a deleted (retired) entity in ShotGrid using the native ShotGrid API revive method.

        **When to use this tool:**
        - You need to restore a deleted/retired entity
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - Entity is not deleted - No need to revive

        **Note:** This is a direct wrapper around the ShotGrid API's revive method.
        Revives entities that were previously deleted (retired).

        Args:
            entity_type: Type of entity to revive.
                        Example: "Shot"

            entity_id: ID of entity to revive.
                      Example: 1234

        Returns:
            Dictionary with revive operation result including:
            - success: Whether the revive was successful
            - entity_type: The type of entity revived
            - entity_id: The ID of the revived entity
            - message: AI-friendly status message
        """
        from shotgrid_mcp_server.response_models import ReviveResult

        try:
            result = _get_sg(sg).revive(entity_type, entity_id)
            return ReviveResult(
                success=bool(result),
                entity_type=entity_type,
                entity_id=entity_id,
                message=f"Successfully revived {entity_type} with ID {entity_id}"
                if result
                else f"Failed to revive {entity_type} with ID {entity_id}",
            ).model_dump()
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
        """Perform a batch operation in ShotGrid using the native ShotGrid API batch method.

        **When to use this tool:**
        - You need to perform multiple operations (create/update/delete) in a single API call
        - You need low-level direct access to the ShotGrid API batch method
        - You want to mix different operation types (create + update + delete)

        **When NOT to use this tool:**
        - To create multiple entities of same type - Use `batch_create_entities` instead (simpler)
        - For most use cases - Use `batch_operations` instead (better validation and error handling)

        **Note:** This is a direct wrapper around the ShotGrid API's batch method.
        For most use cases, prefer using `batch_operations` instead.
        Integer entity IDs in request data are automatically normalized to dict format.

        Args:
            requests: List of batch requests.
                     Each request is a dictionary with request_type, entity_type, and data.

                     Example:
                     [
                         {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
                         {"request_type": "update", "entity_type": "Shot", "entity_id": 1234, "data": {"sg_status_list": "ip"}}
                     ]
                     Note: Integer entity IDs in data (e.g., {"project": 123}) will be automatically
                     normalized to dict format.

        Returns:
            List of results from the batch operation (raw ShotGrid API response).
        """
        try:
            # Normalize each request to convert integer entity IDs to dict format
            normalized_requests = [normalize_batch_request(req) for req in requests]
            result = _get_sg(sg).batch(normalized_requests)
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
        """Summarize data in ShotGrid using the native ShotGrid API summarize method.

        **When to use this tool:**
        - You need to calculate aggregates (count, sum, average, min, max) on entities
        - You want to group entities and get statistics per group
        - You need low-level direct access to the ShotGrid API summarize method

        **When NOT to use this tool:**
        - To get individual entities - Use `search_entities` instead
        - For simple counting - Use `search_entities` and check total_count

        **Common use cases:**
        - Count shots by status
        - Calculate average frame count per sequence
        - Sum total hours on tasks by artist

        **Note:** This is a direct wrapper around the ShotGrid API's summarize method.

        **Entity Reference Normalization:**
        Integer entity IDs in filters and grouping are automatically converted to
        the proper dict format. For example:
        - Input: [["project", "is", 70]]
        - Normalized: [["project", "is", {"type": "Project", "id": 70}]]

        Args:
            entity_type: Type of entity to summarize.
                        Example: "Shot"

            filters: List of filters to apply.
                    Example: [["project.id", "is", 123]]
                    Note: Integer entity IDs will be automatically normalized.

            summary_fields: List of fields to summarize.
                           Each definition specifies field and aggregation type.

                           Example: [{"field": "id", "type": "count"}]

            filter_operator: Optional filter operator ("all" or "any").
                           Default: "all"

            grouping: Optional grouping.
                     Example: [{"field": "sg_status_list", "type": "exact", "direction": "asc"}]

            include_archived_projects: Whether to include archived projects (default: True).

        Returns:
            Summarized data (raw ShotGrid API response).
        """
        try:
            # Normalize filters and grouping to convert integer entity IDs to dict format
            normalized_filters = normalize_filters(filters)
            normalized_grouping = normalize_grouping(grouping)

            result = _get_sg(sg).summarize(
                entity_type,
                normalized_filters,
                summary_fields,
                filter_operator=filter_operator,
                grouping=normalized_grouping,
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

        **IMPORTANT: Text must be at least 3 characters long. Shorter text will cause an error.**

        **When to use this tool:**
        - Search for text across multiple entity types when you don't know which type contains the data
        - Find all entities mentioning a specific keyword (e.g., "explosion", "hero")
        - Quick lookup when entity type is unknown
        - Search for user-entered text (like a global search bar)
        - Search across multiple projects simultaneously

        **When NOT to use this tool:**
        - Text is less than 3 characters - Will fail with error. Use `search_entities` with specific filters instead
        - You know the exact entity type - Use `search_entities` instead (more efficient)
        - You need structured filtering (status, dates, etc.) - Use `search_entities` instead
        - You need related entity data - Use `search_entities_with_related` instead
        - You need time-based filtering - Use `sg_search_advanced` instead
        - You need exact field matching - Use `search_entities` with field filters instead

        **Common use cases:**
        - Search for "SH001" across Shots, Assets, and Tasks
        - Find all entities mentioning "animation" keyword
        - Look up entities related to user "John Doe"
        - Search for "explosion" across all entity types in a project

        **How Text Search Works:**
            ShotGrid's text search looks for matches in key text fields across
            entity types, including:
            - code: Entity code/name
            - description: Entity description
            - name: Entity name (for some types)
            - Other searchable text fields

            The search is case-insensitive and supports partial matches.

        Args:
            text: The text to search for.
                 **MUST be at least 3 characters long** (ShotGrid requirement).
                 Can be a partial match (e.g., "anim" will match "animation").
                 Case-insensitive.

                 Valid examples:
                 - "SH001" - Find entities with code containing SH001 (5 chars, OK)
                 - "animation" - Find entities mentioning animation (9 chars, OK)
                 - "John" - Find entities related to user John (4 chars, OK)
                 - "abc" - Minimum valid length (3 chars, OK)

                 Invalid examples:
                 - "ab" - Too short (2 chars, will fail)
                 - "姓名" - Too short if only 2 characters (will fail)
                 - "SH" - Too short (2 chars, will fail)

            entity_types: List of entity types to search within.
                         Must provide at least one entity type.
                         This will be automatically converted to the dictionary format
                         required by ShotGrid API (with empty filter lists for each type).

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
            ValueError: If text is less than 3 characters long.
            ToolError: If entity_types is empty, contains invalid types, or the
                      ShotGrid API returns an error.

        Examples:
            Search for "animation" across shots and tasks (valid - 9 chars):
            {
                "text": "animation",
                "entity_types": ["Shot", "Task"]
            }

            Search for shot "SH001" in specific project (valid - 5 chars):
            {
                "text": "SH001",
                "entity_types": ["Shot"],
                "project_ids": [123]
            }

            Search for user "John" across multiple types (valid - 4 chars):
            {
                "text": "John",
                "entity_types": ["HumanUser", "Task", "Version"],
                "limit": 20
            }

            Quick search across all common types (valid - 4 chars):
            {
                "text": "hero",
                "entity_types": ["Shot", "Asset", "Task", "Version", "PublishedFile"],
                "limit": 10
            }

            INVALID - Text too short (will fail with ValueError):
            {
                "text": "SH",  # Only 2 characters - ERROR!
                "entity_types": ["Shot"]
            }

        Performance Considerations:
            - Text search is optimized for speed but may not return all fields
            - For detailed entity data, use the returned IDs with `find_one_entity`
            - Searching many entity types may be slower than searching one
            - Use project_ids to limit scope and improve performance

        Note:
            - **CRITICAL: Text must be at least 3 characters** - This is enforced by ShotGrid API
            - Text length is validated before making the API call
            - If text is too short, a ValueError is raised with a clear error message
            - This is a wrapper around ShotGrid's native text_search API
            - Results are grouped by entity type
            - Each entity type can return up to `limit` results
            - The search looks in predefined searchable fields (not all fields)
            - For exact field matching, use `search_entities` with filters instead
            - Empty results for an entity type are omitted from the response
            - The entity_types list is automatically converted to the dictionary format
              required by ShotGrid API: {"EntityType": []} with empty filter lists
        """
        try:
            # Validate text length - ShotGrid requires at least 3 characters
            if not text or len(text.strip()) < 3:
                raise ValueError(
                    f"Text search requires at least 3 characters. Got: '{text}' ({len(text.strip())} characters)"
                )

            # Convert list of entity types to dictionary format required by ShotGrid API
            # ShotGrid text_search expects: {"EntityType": [filters], ...}
            # We provide empty filter lists for each entity type
            entity_types_dict = {entity_type: [] for entity_type in entity_types}

            result = _get_sg(sg).text_search(
                text,
                entity_types_dict,
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
        """Read entity schema from ShotGrid using the native ShotGrid API schema_entity_read method.

        **When to use this tool:**
        - You need to get all entity types available in ShotGrid
        - You want to see entity type properties and metadata
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - To get field schema for a specific entity - Use `schema_get` or `sg_schema_field_read` instead
        - For cached schema information - Check MCP resources first

        **Note:** This is a direct wrapper around the ShotGrid API's schema_entity_read method.

        Returns:
            Entity schema dictionary (raw ShotGrid API response).
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
        """Read field schema from ShotGrid using the native ShotGrid API schema_field_read method.

        **When to use this tool:**
        - You need to get field schema for a specific entity type
        - You want to see field properties and data types
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - For most use cases - Use `schema_get` instead (better response format)
        - To get all entity types - Use `sg_schema_entity_read` instead
        - For cached schema information - Check MCP resources first

        **Note:** This is a direct wrapper around the ShotGrid API's schema_field_read method.
        For most use cases, prefer using `schema_get` instead.

        Args:
            entity_type: Type of entity to read schema for.
                        Example: "Shot"

            field_name: Optional name of field to read schema for.
                       If not provided, returns all fields.

                       Example: "sg_status_list"

        Returns:
            Field schema dictionary (raw ShotGrid API response).
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
        """Upload a file to ShotGrid using the native ShotGrid API upload method.

        **When to use this tool:**
        - You need to upload a movie or file to an entity
        - You want to attach files to versions
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - To upload thumbnails - Use thumbnail tools instead

        **Common use cases:**
        - Upload movie to a version
        - Upload reference file to a shot
        - Attach document to a note

        **Note:** This is a direct wrapper around the ShotGrid API's upload method.
        Returns structured information including attachment ID, file details, and
        a human-readable status message suitable for AI progress reporting.

        Args:
            entity_type: Type of entity to upload to.
                        Example: "Version"

            entity_id: ID of entity to upload to.
                      Example: 1234

            path: Path to file to upload.
                 Example: "C:/movies/shot_001_v001.mov"

            field_name: Name of field to upload to (default: "sg_uploaded_movie").
                       Example: "sg_uploaded_movie"

            display_name: Optional display name for the file.

            tag_list: Optional list of tags for the file.

        Returns:
            Structured upload result containing:
            - attachment_id: The ShotGrid Attachment ID
            - entity_type, entity_id, field_name: Target entity info
            - file_name, file_size_bytes, file_size_display: File details
            - status, message: Human-readable status for AI reporting
        """
        import mimetypes
        import os

        from shotgrid_mcp_server.response_models import UploadResult, format_file_size

        try:
            # Get file information before upload
            file_name = os.path.basename(path)
            file_size_bytes = os.path.getsize(path) if os.path.exists(path) else 0
            file_size_display = format_file_size(file_size_bytes)
            content_type, _ = mimetypes.guess_type(path)

            # Perform the upload
            attachment_id = _get_sg(sg).upload(
                entity_type,
                entity_id,
                path,
                field_name=field_name,
                display_name=display_name,
                tag_list=tag_list,
            )

            # Create AI-friendly success message
            message = (
                f"Successfully uploaded '{file_name}' ({file_size_display}) "
                f"to {entity_type} ID {entity_id}. Attachment ID: {attachment_id}"
            )

            # Return structured result
            return UploadResult(
                attachment_id=attachment_id,
                success=True,
                entity_type=entity_type,
                entity_id=entity_id,
                field_name=field_name,
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                file_size_display=file_size_display,
                display_name=display_name or file_name,
                status="completed",
                message=message,
                content_type=content_type,
                tag_list=tag_list,
            ).model_dump()

        except Exception as err:
            handle_error(err, operation="sg.upload")
            raise

    @server.tool("sg_download_attachment")
    def sg_download_attachment(
        attachment: Dict[str, Any],
        file_path: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Download an attachment from ShotGrid using the native ShotGrid API download_attachment method.

        **When to use this tool:**
        - You need to download an attachment from an entity
        - You have an attachment dictionary from a query
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - To download thumbnails - Use thumbnail tools instead

        **Note:** This is a direct wrapper around the ShotGrid API's download_attachment method.

        Args:
            attachment: Attachment dictionary to download.
                       Usually obtained from entity query results.

                       Example: {"url": "https://...", "name": "file.pdf", "id": 123}

            file_path: Optional path to save the file to.
                      If not provided, saves to temp directory.

                      Example: "C:/downloads/file.pdf"

        Returns:
            Dictionary with download result including:
            - success: Whether the download was successful
            - file_path: Path where file was saved
            - file_name: Name of the downloaded file
            - file_size_bytes: Size of the downloaded file
            - file_size_display: Human-readable file size
            - message: AI-friendly status message
        """
        import os

        from shotgrid_mcp_server.response_models import DownloadResult, format_file_size

        try:
            # Perform download
            downloaded_path = _get_sg(sg).download_attachment(attachment, file_path=file_path)

            # Get file information
            file_size_bytes = os.path.getsize(downloaded_path) if os.path.exists(downloaded_path) else 0
            file_size_display = format_file_size(file_size_bytes)
            file_name = os.path.basename(downloaded_path)

            # Extract attachment info if available
            attachment_id = attachment.get("id")
            attachment_name = attachment.get("name")

            message = (
                f"Successfully downloaded '{attachment_name or file_name}' ({file_size_display}) "
                f"to '{downloaded_path}'"
            )

            return DownloadResult(
                success=True,
                file_path=downloaded_path,
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                file_size_display=file_size_display,
                attachment_id=attachment_id,
                attachment_name=attachment_name,
                message=message,
            ).model_dump()

        except Exception as err:
            handle_error(err, operation="sg.download_attachment")
            raise


def register_activity_stream_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register activity stream tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    _register_activity_stream_read(server, sg)
    _register_follow_tools(server, sg)


def _register_activity_stream_read(server: FastMCPType, sg: Shotgun) -> None:
    """Register activity stream read tool.

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
        """Read activity stream from ShotGrid using the native ShotGrid API activity_stream_read method.

        **When to use this tool:**
        - You need to get activity history for an entity
        - You want to see who made changes and when
        - You need to track entity updates over time
        - You need low-level direct access to the ShotGrid API

        **When NOT to use this tool:**
        - To get current entity data - Use `search_entities` or `find_one_entity` instead

        **Common use cases:**
        - Get recent activity for a shot
        - Track changes to a version
        - See who updated a task

        **Note:** This is a direct wrapper around the ShotGrid API's activity_stream_read method.

        Args:
            entity_type: Type of entity to read activity stream for.
                        Example: "Shot"

            entity_id: ID of entity to read activity stream for.
                      Example: 1234

            limit: Optional limit on number of activities to return.
                  Example: 50

            max_id: Optional maximum activity ID to return (for pagination).

            min_id: Optional minimum activity ID to return (for pagination).

        Returns:
            Activity stream data (raw ShotGrid API response).
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


def _register_follow_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register follow/unfollow tools.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg_follow")
    def sg_follow(
        entity_type: EntityType,
        entity_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Follow an entity in ShotGrid using the native ShotGrid API follow method.

        **When to use this tool:**
        - User wants to follow an entity to receive updates
        - Subscribe to changes on a specific entity
        - Enable notifications for entity updates

        **When NOT to use this tool:**
        - To get current followers - Use `sg_followers` instead
        - To get entities a user is following - Use `sg_following` instead

        **Common use cases:**
        - Follow a shot to get notified of status changes
        - Subscribe to a version for review updates
        - Track changes to a task

        Args:
            entity_type: Type of entity to follow.
                        Example: "Shot", "Version", "Task"

            entity_id: ID of entity to follow.
                      Example: 1234

            user_id: Optional user ID. If not provided, uses the current user.
                    Example: 42

        Returns:
            Dictionary with follow operation result including:
            - success: Whether the operation was successful
            - action: 'follow'
            - entity_type: The type of entity
            - entity_id: The ID of the entity
            - message: AI-friendly status message
        """
        from shotgrid_mcp_server.response_models import FollowResult

        try:
            result = _get_sg(sg).follow(entity_type, entity_id, user_id=user_id)
            return FollowResult(
                success=bool(result),
                action="follow",
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                message=f"Successfully started following {entity_type} with ID {entity_id}"
                if result
                else f"Failed to follow {entity_type} with ID {entity_id}",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="sg.follow")
            raise

    @server.tool("sg_unfollow")
    def sg_unfollow(
        entity_type: EntityType,
        entity_id: int,
        user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Unfollow an entity in ShotGrid using the native ShotGrid API unfollow method.

        **When to use this tool:**
        - User wants to stop following an entity
        - Unsubscribe from entity updates
        - Disable notifications for an entity

        **When NOT to use this tool:**
        - To get current followers - Use `sg_followers` instead
        - To get entities a user is following - Use `sg_following` instead

        **Common use cases:**
        - Stop receiving notifications for a completed shot
        - Unsubscribe from a version after review
        - Stop tracking a task

        Args:
            entity_type: Type of entity to unfollow.
                        Example: "Shot", "Version", "Task"

            entity_id: ID of entity to unfollow.
                      Example: 1234

            user_id: Optional user ID. If not provided, uses the current user.
                    Example: 42

        Returns:
            Dictionary with unfollow operation result including:
            - success: Whether the operation was successful
            - action: 'unfollow'
            - entity_type: The type of entity
            - entity_id: The ID of the entity
            - message: AI-friendly status message
        """
        from shotgrid_mcp_server.response_models import FollowResult

        try:
            result = _get_sg(sg).unfollow(entity_type, entity_id, user_id=user_id)
            return FollowResult(
                success=bool(result),
                action="unfollow",
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                message=f"Successfully stopped following {entity_type} with ID {entity_id}"
                if result
                else f"Failed to unfollow {entity_type} with ID {entity_id}",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="sg.unfollow")
            raise

    @server.tool("sg_followers")
    def sg_followers(
        entity_type: EntityType,
        entity_id: int,
    ) -> List[Dict[str, Any]]:
        """Get followers of an entity in ShotGrid using the native ShotGrid API followers method.

        **When to use this tool:**
        - Get list of users following an entity
        - See who is subscribed to entity updates
        - Check notification recipients for an entity

        **When NOT to use this tool:**
        - To follow an entity - Use `sg_follow` instead
        - To get entities a user is following - Use `sg_following` instead

        **Common use cases:**
        - See who is following a shot
        - Check subscribers for a version
        - List users tracking a task

        Args:
            entity_type: Type of entity to get followers for.
                        Example: "Shot", "Version", "Task"

            entity_id: ID of entity to get followers for.
                      Example: 1234

        Returns:
            List of user dictionaries with follower information.
        """
        try:
            result = _get_sg(sg).followers(entity_type, entity_id)
            return result
        except Exception as err:
            handle_error(err, operation="sg.followers")
            raise

    @server.tool("sg_following")
    def sg_following(
        user_id: Optional[int] = None,
        entity_type: Optional[EntityType] = None,
    ) -> List[Dict[str, Any]]:
        """Get entities followed by a user in ShotGrid using the native ShotGrid API following method.

        **When to use this tool:**
        - Get list of entities a user is following
        - See what a user is subscribed to
        - Check user's notification subscriptions

        **When NOT to use this tool:**
        - To follow an entity - Use `sg_follow` instead
        - To get followers of an entity - Use `sg_followers` instead

        **Common use cases:**
        - See all shots a user is following
        - Check what versions a user is subscribed to
        - List tasks a user is tracking

        Args:
            user_id: Optional user ID. If not provided, uses the current user.
                    Example: 42

            entity_type: Optional entity type to filter by.
                        If provided, only returns entities of this type.
                        Example: "Shot", "Version", "Task"

        Returns:
            List of entity dictionaries that the user is following.
        """
        try:
            result = _get_sg(sg).following(user_id=user_id, entity_type=entity_type)
            return result
        except Exception as err:
            handle_error(err, operation="sg.following")
            raise


def register_note_thread_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register note thread tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg_note_thread_read")
    def sg_note_thread_read(note_id: int) -> Dict[str, Any]:
        """Read a note thread from ShotGrid using the native ShotGrid API note_thread_read method.

        **When to use this tool:**
        - Get the full conversation thread for a note
        - Read all replies to a note
        - Get attachments associated with a note thread
        - View complete note history with all responses

        **When NOT to use this tool:**
        - To get basic note information - Use `shotgrid_note_read` instead
        - To create a note - Use `shotgrid_note_create` instead
        - To update a note - Use `shotgrid_note_update` instead

        **Common use cases:**
        - Read all feedback on a version review
        - Get complete conversation history for a note
        - View all replies and attachments in a note thread

        **Note:** This returns the full note thread including the original note,
        all replies, and attachments.

        Args:
            note_id: ID of the note to read the thread for.
                    Example: 1234

        Returns:
            Dictionary containing the note thread data with structure:
            {
                "note": {...},  # Original note
                "replies": [...],  # List of reply notes
                "attachments": [...]  # List of attachments
            }
        """
        try:
            result = _get_sg(sg).note_thread_read(note_id)
            return result
        except Exception as err:
            handle_error(err, operation="sg.note_thread_read")
            raise


def register_project_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register project-related tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg_update_project_last_accessed")
    def sg_update_project_last_accessed(project_id: int) -> Dict[str, Any]:
        """Update project last accessed time using the native ShotGrid API update_project_last_accessed method.

        **When to use this tool:**
        - Mark a project as recently accessed by the current user
        - Update the "last accessed" timestamp for a project
        - Track project usage for the current user

        **When NOT to use this tool:**
        - To update other project fields - Use `update_entity` instead
        - To get project information - Use `search_entities` or `find_one_entity` instead

        **Common use cases:**
        - User opens a project in the application
        - Track which projects a user is actively working on
        - Update project access history

        **Note:** This updates the last_accessed_by_current_user field for the project.

        Args:
            project_id: ID of the project to update.
                       Example: 123

        Returns:
            Dictionary with operation result including:
            - success: Whether the operation was successful
            - project_id: The project ID that was updated
            - message: AI-friendly status message
        """
        from shotgrid_mcp_server.response_models import ProjectAccessResult

        try:
            result = _get_sg(sg).update_project_last_accessed(project_id)
            return ProjectAccessResult(
                success=bool(result),
                project_id=project_id,
                message=f"Successfully updated last accessed time for Project ID {project_id}"
                if result
                else f"Failed to update last accessed time for Project ID {project_id}",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="sg.update_project_last_accessed")
            raise


def register_preferences_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register preferences tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("sg_preferences_read")
    def sg_preferences_read() -> Dict[str, Any]:
        """Read site preferences from ShotGrid using the native ShotGrid API preferences_read method.

        **When to use this tool:**
        - Get site-wide preference settings
        - Check configuration values
        - Read system settings

        **When NOT to use this tool:**
        - To update preferences - Not supported via API
        - To get user-specific settings - Use user entity fields instead

        **Common use cases:**
        - Check site timezone settings
        - Get default status list values
        - Read system configuration

        **Note:** This returns a subset of site preferences that are accessible via the API.
        Not all preferences are exposed.

        Returns:
            Dictionary containing site preferences.
        """
        try:
            result = _get_sg(sg).preferences_read()
            return result
        except Exception as err:
            handle_error(err, operation="sg.preferences_read")
            raise
