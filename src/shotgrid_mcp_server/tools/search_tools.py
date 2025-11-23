"""Search tools for ShotGrid MCP server.

This module contains tools for searching entities in ShotGrid.
"""

import logging
from typing import Any, Dict, List, Optional

# Import from shotgrid-query
from shotgrid_query import FilterModel as Filter
from shotgrid_query import TimeUnitEnum as TimeUnit
from shotgrid_query import process_filters
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.api_client import ShotGridAPIClient
from shotgrid_mcp_server.api_models import (
    AdvancedSearchRequest,
    FindOneEntityRequest,
    FindOneRequest,
    FindRequest,
    SearchEntitiesRequest,
    SearchEntitiesWithRelatedRequest,
)
from shotgrid_mcp_server.custom_types import EntityType

# Import MCP-specific models
from shotgrid_mcp_server.models import (
    EntitiesResponse,
    EntityDict,
    ProjectDict,
    ProjectsResponse,
    UserDict,
    UsersResponse,
    create_in_last_filter,
)
from shotgrid_mcp_server.response_models import (
    BaseResponse,
    ResponseMetadata,
    SearchEntitiesResult,
    SingleEntityResult,
    serialize_response,
)
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import FastMCPType

# Configure logging
logger = logging.getLogger(__name__)


def register_search_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register search tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Register basic search tool
    register_search_entities(server, sg)

    # Register advanced search tools
    register_search_with_related(server, sg)
    register_find_one_entity(server, sg)
    register_advanced_search_tool(server, sg)

    # Register helper functions
    register_helper_functions(server, sg)


def register_search_entities(server: FastMCPType, sg: Shotgun) -> None:
    """Register search_entities tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection (may be a mock in lazy mode).
    """

    @server.tool("search_entities")
    def search_entities(request: SearchEntitiesRequest) -> Dict[str, Any]:
        """Search for entities in ShotGrid using filters and field selection.

        Use this tool for basic entity searches when you need to:
        - Find multiple entities matching specific criteria
        - Filter by field values (status, dates, names, etc.)
        - Return specific fields from matched entities
        - Sort results by one or more fields

        For searches requiring related entity data (e.g., "get shots with their sequence names"),
        use `search_entities_with_related` instead.

        For finding a single entity by ID or unique field, use `find_one_entity` instead.

        For full-text search across multiple entity types, use `sg_text_search` instead.

        Args:
            request: SearchEntitiesRequest containing:

                entity_type: Type of entity to search.
                    Common types: "Shot", "Asset", "Task", "Version", "Note", "PublishedFile"

                filters: List of filter conditions (optional).
                    **IMPORTANT**: filters is a simple list of [field, operator, value] triplets.
                    To use AND/OR logic, set filter_operator parameter separately (NOT inside filters).

                    If omitted, returns all entities of the specified type.

                    Simple filter (single condition):
                    ["sg_status_list", "is", "ip"]

                    Multiple filters (default AND logic):
                    [
                        ["sg_status_list", "is", "ip"],
                        ["project", "is", {"type": "Project", "id": 123}]
                    ]

                    Time-based filter:
                    ["updated_at", "in_last", 7, "DAY"]

                    Text search (substring match):
                    ["code", "contains", "hero"]

                    Entity reference filter:
                    ["project", "is", {"type": "Project", "id": 123}]

                    Numeric comparison:
                    ["sg_cut_duration", "greater_than", 100]

                fields: List of field names to return (optional).
                    If omitted, returns default fields (id, type, code, etc.).

                    Example: ["code", "sg_status_list", "description", "project"]

                order: Sort order (optional).
                    Format: [{"field_name": "code", "direction": "asc"}]
                    Direction: "asc" (ascending) or "desc" (descending)

                    Multiple sort fields:
                    [
                        {"field_name": "project", "direction": "asc"},
                        {"field_name": "code", "direction": "asc"}
                    ]

                limit: Maximum number of results (optional).
                    Example: 100

                retired_only: Include only retired entities (optional, default: False).

        Returns:
            Dictionary containing:
            - items: List of matching entities
            - entity_type: The entity type searched
            - fields: Fields returned for each entity
            - filter_fields: Fields used in filters
            - total_count: Number of entities found
            - schema_resources: Links to schema information

            Example:
            {
                "items": [
                    {
                        "type": "Shot",
                        "id": 1234,
                        "code": "SH001",
                        "sg_status_list": "ip",
                        "project": {"type": "Project", "id": 123, "name": "Demo"}
                    },
                    ...
                ],
                "entity_type": "Shot",
                "total_count": 42,
                "schema_resources": {...}
            }

        Common Entity Types:
            - Shot: Individual shots in sequences
            - Asset: Reusable elements (characters, props, environments)
            - Task: Work assignments for artists
            - Version: Iterations of work
            - PublishedFile: Finalized files
            - Note: Comments and feedback
            - Playlist: Collections of versions for review

        Common Filter Operators:
            - is, is_not: Exact match
            - contains, not_contains: Substring match (case-insensitive)
            - in, not_in: Match any value in list
            - greater_than, less_than: Numeric/date comparison
            - between: Range (e.g., ["created_at", "between", date1, date2])
            - in_last, not_in_last: Time-based (e.g., ["updated_at", "in_last", 7, "DAY"])
            - in_next, not_in_next: Future time-based
            - starts_with, ends_with: String prefix/suffix match

        Common Status Codes:
            - wtg: Waiting to Start
            - rdy: Ready to Start
            - ip: In Progress
            - rev: Pending Review
            - fin: Final
            - omt: Omitted

        Time Units (for time-based filters):
            - DAY: Days
            - WEEK: Weeks
            - MONTH: Months
            - YEAR: Years

        Raises:
            ToolError: If entity_type is invalid or filters are malformed.

        Examples:
            Find all in-progress shots:
            {
                "entity_type": "Shot",
                "filters": [["sg_status_list", "is", "ip"]],
                "fields": ["code", "description", "sg_sequence"]
            }

            Find shots updated in last week:
            {
                "entity_type": "Shot",
                "filters": [["updated_at", "in_last", 7, "DAY"]],
                "order": [{"field_name": "updated_at", "direction": "desc"}]
            }

            Find tasks assigned to user:
            {
                "entity_type": "Task",
                "filters": [["task_assignees", "is", {"type": "HumanUser", "id": 42}]],
                "fields": ["content", "entity", "sg_status_list"]
            }

        Note:
            - Filters are automatically normalized (field_name → field)
            - Entity references must use {"type": "EntityType", "id": 123} format
            - Date filters support DAY, WEEK, MONTH, YEAR units
            - Text filters (contains, starts_with) are case-insensitive
        """
        try:
            # Get current ShotGrid connection (from HTTP headers or fallback)
            from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection

            current_sg = get_current_shotgrid_connection(fallback_sg=sg)

            # Create API client with current connection
            api_client = ShotGridAPIClient(current_sg)

            # Process filters through the shared normalization pipeline
            processed_filters = process_filters(request.filters or [])

            # Create FindRequest for API client
            find_request = FindRequest(
                entity_type=request.entity_type,
                filters=processed_filters,
                fields=request.fields,
                order=request.order,
                filter_operator=request.filter_operator,
                limit=request.limit,
                page=1,  # Avoid "page parameter must be a positive integer" errors
            )

            # Execute query through API client
            result = api_client.find(find_request) or []

            # Convert results to Pydantic models
            entity_dicts: List[EntityDict] = []
            for entity in result:
                serialized_entity = serialize_entity(entity)

                if "id" not in serialized_entity and entity.get("id"):
                    serialized_entity["id"] = entity["id"]

                try:
                    entity_dicts.append(EntityDict(**serialized_entity))
                except Exception as exc:
                    logger.warning("Failed to convert entity to EntityDict: %s", exc)
                    if "id" in serialized_entity and "type" in serialized_entity:
                        entity_dicts.append(EntityDict(id=serialized_entity["id"], type=serialized_entity["type"]))

            search_result = SearchEntitiesResult(
                items=entity_dicts,
                entity_type=request.entity_type,
                fields=request.fields,
                filter_fields=[f["field"] for f in (request.filters or []) if isinstance(f, dict) and "field" in f],
                total_count=len(entity_dicts),
            )

            response = BaseResponse(
                data=search_result,
                metadata=ResponseMetadata(status="success"),
            )
            return serialize_response(response)
        except Exception as err:
            handle_error(err, operation="search_entities")
            raise  # This is needed to satisfy the type checker

    # Expose search_entities implementation at module level for tests and internal use
    globals()["search_entities"] = search_entities


def register_search_with_related(server: FastMCPType, sg: Shotgun) -> None:
    """Register search_entities_with_related tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Create API client
    api_client = ShotGridAPIClient(sg)

    @server.tool("search_entities_with_related")
    def search_entities_with_related(request: SearchEntitiesWithRelatedRequest) -> Dict[str, Any]:
        """Search for entities in ShotGrid with related entity data (field hopping).

        Use this tool when you need to retrieve data from related entities in a single query.
        This is more efficient than making multiple separate queries.

        Common use cases:
        - Get shots with their sequence names
        - Get tasks with assignee details (name, email)
        - Get versions with linked entity information
        - Get published files with version and task details
        - Any query requiring data from linked entities

        For basic searches without related data, use `search_entities` instead.
        For time-based filters or complex queries, use `sg_search_advanced` instead.

        Field Hopping Explained:
            Field hopping allows you to retrieve fields from related entities by using
            dot notation in field names. For example:
            - "sg_sequence.Sequence.code" gets the sequence code for a shot
            - "task_assignees.HumanUser.name" gets assignee names for a task

            The format is: "field_name.EntityType.field_to_retrieve"

        Args:
            request: SearchEntitiesWithRelatedRequest containing:

                entity_type: Type of entity to search.
                    Common types: "Shot", "Asset", "Task", "Version", "PublishedFile"

                filters: List of filter conditions (optional).
                    Same format as `search_entities`.

                    Example:
                    [["sg_status_list", "is", "ip"]]

                fields: List of standard fields to return (optional).
                    Example: ["code", "description", "sg_status_list"]

                related_fields: Dictionary mapping entity link fields to lists of fields
                               to retrieve from the related entity.

                    Format:
                    {
                        "link_field": ["field1", "field2", ...],
                        ...
                    }

                    Examples:

                    Get sequence info for shots:
                    {
                        "sg_sequence": ["code", "description"]
                    }

                    Get assignee details for tasks:
                    {
                        "task_assignees": ["name", "email", "login"]
                    }

                    Get multiple related entities:
                    {
                        "entity": ["code", "sg_status_list"],
                        "user": ["name", "email"]
                    }

                order: Sort order (optional).
                    Example: [{"field_name": "code", "direction": "asc"}]

                filter_operator: Logical operator for combining filters (optional).
                    **IMPORTANT**: This is a TOP-LEVEL parameter in the request object, NOT nested inside filters!

                    Values: "all" (AND logic, default) or "any" (OR logic)

                    **CORRECT usage** (filter_operator at top level):
                    {
                        "entity_type": "Note",
                        "filters": [
                            ["user", "is", {"type": "HumanUser", "id": 121}],
                            ["addressings_to", "is", {"type": "HumanUser", "id": 121}]
                        ],
                        "filter_operator": "any",  # <-- Top-level parameter!
                        "fields": ["id", "subject", "content"]
                    }

                    **WRONG usage** (DO NOT nest filter_operator inside filters):
                    {
                        "entity_type": "Note",
                        "filters": {  # <-- WRONG! filters should be a list, not a dict
                            "filter_operator": "any",
                            "filters": [...]
                        }
                    }

                limit: Maximum number of results (optional).
                    Example: 100

        Returns:
            Dictionary containing:
            - items: List of entities with related data populated
            - entity_type: The type of entity searched
            - fields: All fields returned (including related fields)
            - total_count: Number of entities found
            - schema_resources: Links to schema information

            Example:
            {
                "items": [
                    {
                        "id": 1234,
                        "code": "SH001",
                        "sg_sequence": {
                            "id": 100,
                            "type": "Sequence",
                            "code": "SEQ01",
                            "description": "Opening sequence"
                        }
                    }
                ],
                "entity_type": "Shot",
                "fields": ["code", "sg_sequence.Sequence.code", "sg_sequence.Sequence.description"],
                "total_count": 1,
                "schema_resources": {...}
            }

        Raises:
            ToolError: If entity_type is invalid, filters are malformed, or related_fields
                      reference non-existent fields.

        Examples:
            Get shots with sequence names:
            {
                "entity_type": "Shot",
                "filters": [["sg_status_list", "is", "ip"]],
                "fields": ["code", "description"],
                "related_fields": {
                    "sg_sequence": ["code", "description"]
                }
            }

            Get tasks with assignee and entity details:
            {
                "entity_type": "Task",
                "filters": [["sg_status_list", "is", "ip"]],
                "fields": ["content", "sg_status_list"],
                "related_fields": {
                    "task_assignees": ["name", "email"],
                    "entity": ["code", "sg_status_list"]
                }
            }

            Get versions with user and entity info:
            {
                "entity_type": "Version",
                "filters": [["created_at", "in_last", 7, "DAY"]],
                "fields": ["code", "sg_status_list"],
                "related_fields": {
                    "user": ["name", "email"],
                    "entity": ["code"],
                    "sg_task": ["content"]
                },
                "order": [{"field_name": "created_at", "direction": "desc"}],
                "limit": 50
            }

        Performance Benefits:
            - Single API call instead of N+1 queries
            - Reduced network latency
            - More efficient for large result sets
            - Automatic handling of entity references

        Note:
            - Related fields are returned as nested dictionaries with type, id, and requested fields
            - Multi-entity fields (like task_assignees) return lists of entities
            - Invalid related field names will raise an error
            - Field hopping is limited to direct relationships (no chaining beyond one level)
        """
        try:
            # Use the shared filter processing pipeline
            processed_filters = process_filters(request.filters or [])

            # Process fields with related entity fields
            all_fields = prepare_fields_with_related(
                sg,
                request.entity_type,
                request.fields,
                request.related_fields,
            )

            # Create FindRequest for API client
            find_request = FindRequest(
                entity_type=request.entity_type,
                filters=processed_filters,
                fields=all_fields,
                order=request.order,
                filter_operator=request.filter_operator,
                limit=request.limit,
                page=1,  # Set a default page value to avoid "page parameter must be a positive integer" error
            )

            # Execute query through API client
            result = api_client.find(find_request) or []

            # Convert results to Pydantic models
            entity_dicts: List[EntityDict] = []
            for entity in result:
                serialized_entity = serialize_entity(entity)

                if "id" not in serialized_entity and entity.get("id"):
                    serialized_entity["id"] = entity["id"]

                try:
                    entity_dicts.append(EntityDict(**serialized_entity))
                except Exception as exc:
                    logger.warning("Failed to convert entity to EntityDict: %s", exc)
                    if "id" in serialized_entity and "type" in serialized_entity:
                        entity_dicts.append(EntityDict(id=serialized_entity["id"], type=serialized_entity["type"]))

            search_result = SearchEntitiesResult(
                items=entity_dicts,
                entity_type=request.entity_type,
                fields=all_fields,
                filter_fields=[f["field"] for f in (request.filters or []) if isinstance(f, dict) and "field" in f],
                total_count=len(entity_dicts),
            )

            response = BaseResponse(
                data=search_result,
                metadata=ResponseMetadata(status="success"),
            )
            return serialize_response(response)
        except Exception as err:
            handle_error(err, operation="search_entities_with_related")
            raise  # This is needed to satisfy the type checker

    # Expose search_entities_with_related implementation at module level for tests and internal use
    globals()["search_entities_with_related"] = search_entities_with_related


def register_find_one_entity(server: FastMCPType, sg: Shotgun) -> None:
    """Register find_one_entity tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Create API client
    api_client = ShotGridAPIClient(sg)

    @server.tool("entity_find_one")
    def find_one_entity(request: FindOneEntityRequest) -> Dict[str, Any]:
        """Find a single entity in ShotGrid by ID or unique field.

        Use this tool when you need to:
        - Look up a specific entity by its ID
        - Find an entity by a unique field (e.g., code)
        - Get detailed information about one entity
        - Verify if an entity exists

        For searching multiple entities, use `search_entities` instead.

        For searching with related entity data, use `search_entities_with_related` instead.

        Args:
            request: FindOneEntityRequest containing:

                entity_type: Type of entity to find.
                    Common types: "Shot", "Asset", "Task", "Version", "Note"

                filters: Filter conditions to identify the entity.
                    **IMPORTANT**: filters is a simple list of [field, operator, value] triplets.
                    To use AND/OR logic, set filter_operator parameter separately (NOT inside filters).

                    Find by ID:
                    [["id", "is", 1234]]

                    Find by unique code:
                    [["code", "is", "SH001"]]

                    Find by multiple conditions (AND logic):
                    [
                        ["code", "is", "SH001"],
                        ["project", "is", {"type": "Project", "id": 123}]
                    ]

                fields: List of field names to return (optional).
                    If omitted, returns default fields.

                    Example: ["code", "sg_status_list", "description", "project", "tasks"]

                order: Sort order if multiple entities match (optional).
                    Format: [{"field_name": "created_at", "direction": "desc"}]
                    Returns the first entity matching the sort order.

        Returns:
            Dictionary containing:
            - entity: The found entity (or None if not found)
            - entity_type: The entity type searched
            - fields: Fields returned
            - schema_resources: Links to schema information

            Example (entity found):
            {
                "entity": {
                    "type": "Shot",
                    "id": 1234,
                    "code": "SH001",
                    "sg_status_list": "ip",
                    "project": {"type": "Project", "id": 123, "name": "Demo"}
                },
                "entity_type": "Shot",
                "schema_resources": {...}
            }

            Example (entity not found):
            {
                "entity": None,
                "entity_type": "Shot",
                "schema_resources": {...}
            }

        Raises:
            ToolError: If entity_type is invalid or filters are malformed.

        Examples:
            Find shot by ID:
            {
                "entity_type": "Shot",
                "filters": [["id", "is", 1234]],
                "fields": ["code", "description", "sg_sequence"]
            }

            Find task by code and project:
            {
                "entity_type": "Task",
                "filters": {
                    "filter_operator": "all",
                    "filters": [
                        ["content", "is", "Animation"],
                        ["entity", "is", {"type": "Shot", "id": 789}]
                    ]
                },
                "fields": ["content", "sg_status_list", "task_assignees"]
            }

            Find version by code:
            {
                "entity_type": "Version",
                "filters": [["code", "is", "animation_v003"]],
                "fields": ["code", "sg_status_list", "entity", "user"]
            }

        Note:
            - Returns None if no entity matches the filters
            - If multiple entities match, returns the first one (use order to control which)
            - More efficient than search_entities when you only need one entity
            - Filters are automatically normalized (field_name → field)
        """
        try:
            # Convert filters to list format for process_filters
            # FindOneEntityRequest validator normalizes to dict format, but process_filters expects list format
            filter_objects: List[Any] = []
            for filter_item in request.filters or []:
                if isinstance(filter_item, dict):
                    # Convert dict format to list format: [field, operator, value]
                    filter_objects.append([filter_item["field"], filter_item["operator"], filter_item["value"]])
                else:
                    # Already in list format
                    filter_objects.append(filter_item)

            # Use the shared filter processing pipeline
            processed_filters = process_filters(filter_objects)

            # Create FindOneRequest for API client
            find_one_request = FindOneRequest(
                entity_type=request.entity_type,
                filters=processed_filters,
                fields=request.fields,
                order=request.order,
                filter_operator=request.filter_operator,
            )

            # Execute query through API client
            result = api_client.find_one(find_one_request)

            entity: Optional[EntityDict] = None
            if result is not None:
                serialized_entity = serialize_entity(result)

                if "id" not in serialized_entity and result.get("id"):
                    serialized_entity["id"] = result["id"]

                try:
                    entity = EntityDict(**serialized_entity)
                except Exception as exc:
                    logger.warning("Failed to convert entity to EntityDict: %s", exc)
                    if "id" in serialized_entity and "type" in serialized_entity:
                        entity = EntityDict(id=serialized_entity["id"], type=serialized_entity["type"])

            single_result = SingleEntityResult(
                entity=entity,
                entity_type=request.entity_type,
                schema_resources={
                    "entities": "shotgrid://schema/entities",
                    "statuses": "shotgrid://schema/statuses",
                },
            )

            response = BaseResponse(
                data=single_result,
                metadata=ResponseMetadata(status="success"),
            )
            return serialize_response(response)
        except Exception as err:
            handle_error(err, operation="find_one_entity")
            raise  # This is needed to satisfy the type checker


def _convert_filters_to_list_format(filters: List[Any]) -> List[Any]:
    """Convert filters from dict format to list format for process_filters.

    Args:
        filters: List of filters in dict or list format

    Returns:
        List of filters in list format [field, operator, value]
    """
    filter_objects: List[Any] = []
    for filter_item in filters or []:
        if isinstance(filter_item, dict):
            # Convert dict format to list format: [field, operator, value]
            filter_objects.append([filter_item["field"], filter_item["operator"], filter_item["value"]])
        else:
            # Already in list format
            filter_objects.append(filter_item)
    return filter_objects


def _convert_time_filters_to_list_format(time_filters: List[Any]) -> List[Any]:
    """Convert time filters to list format for process_filters.

    Args:
        time_filters: List of TimeFilter objects

    Returns:
        List of filters in list format [field, operator, value]
    """
    filter_objects: List[Any] = []
    for time_filter in time_filters or []:
        try:
            filter_obj = time_filter.to_filter()
            # Convert Filter object to list format: [field, operator, value]
            filter_objects.append(filter_obj.to_tuple())
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to convert time filter %s: %s", time_filter, exc)
    return filter_objects


def _convert_entities_to_dicts(entities: List[Dict[str, Any]]) -> List[EntityDict]:
    """Convert raw entity dicts to EntityDict models.

    Args:
        entities: List of raw entity dictionaries

    Returns:
        List of EntityDict models
    """
    entity_dicts: List[EntityDict] = []
    for entity in entities:
        serialized_entity = serialize_entity(entity)

        if "id" not in serialized_entity and entity.get("id"):
            serialized_entity["id"] = entity["id"]

        try:
            entity_dicts.append(EntityDict(**serialized_entity))
        except Exception as exc:
            logger.warning("Failed to convert entity to EntityDict: %s", exc)
            if "id" in serialized_entity and "type" in serialized_entity:
                entity_dicts.append(EntityDict(id=serialized_entity["id"], type=serialized_entity["type"]))

    return entity_dicts


def register_advanced_search_tool(server: FastMCPType, sg: Shotgun) -> None:
    """Register sg.search.advanced tool.

    This tool provides a more flexible search entry point that combines
    standard filters with time-based filters and related_fields support.
    """

    api_client = ShotGridAPIClient(sg)

    @server.tool("sg_search_advanced")
    def sg_search_advanced(request: AdvancedSearchRequest) -> Dict[str, Any]:
        """Advanced search for entities in ShotGrid with time-based filters and related fields.

        Use this tool when you need advanced filtering capabilities beyond basic searches.
        This tool combines standard filters, time-based filters, and related field retrieval
        in a single query.

        Common use cases:
        - Find entities created or updated within a time range (last N days/weeks/months)
        - Combine time-based filters with standard filters
        - Search with complex date logic (in_last, in_next, in_calendar_day, etc.)
        - Get related entity data along with time-based filtering

        For basic searches without time filters, use `search_entities` instead.
        For searches with related data but no time filters, use `search_entities_with_related` instead.
        For full-text search, use `sg_text_search` instead.

        Args:
            request: AdvancedSearchRequest containing:

                entity_type: Type of entity to search.
                    Common types: "Shot", "Asset", "Task", "Version", "PublishedFile"

                filters: List of standard filter conditions (optional).
                    Same format as `search_entities`.

                    Examples:
                    [["sg_status_list", "is", "ip"]]
                    [["project", "is", {"type": "Project", "id": 123}]]

                time_filters: List of time-based filter conditions (optional).
                    These are special filters for date/datetime fields that use
                    relative time expressions.

                    Format:
                    [
                        {
                            "field": "date_field_name",
                            "operator": "time_operator",
                            "count": number,
                            "unit": "DAY|WEEK|MONTH|YEAR"
                        },
                        ...
                    ]

                    Time Operators:
                    - in_last: Within the last N units (e.g., last 7 days)
                    - in_next: Within the next N units (e.g., next 30 days)
                    - in_calendar_day: On a specific calendar day
                    - in_calendar_week: Within a specific calendar week
                    - in_calendar_month: Within a specific calendar month
                    - in_calendar_year: Within a specific calendar year

                    Time Units:
                    - DAY: Calendar days
                    - WEEK: Calendar weeks
                    - MONTH: Calendar months
                    - YEAR: Calendar years

                    Examples:

                    Find entities updated in last 7 days:
                    [
                        {
                            "field": "updated_at",
                            "operator": "in_last",
                            "count": 7,
                            "unit": "DAY"
                        }
                    ]

                    Find entities created in last 2 weeks:
                    [
                        {
                            "field": "created_at",
                            "operator": "in_last",
                            "count": 2,
                            "unit": "WEEK"
                        }
                    ]

                    Find entities due in next 30 days:
                    [
                        {
                            "field": "due_date",
                            "operator": "in_next",
                            "count": 30,
                            "unit": "DAY"
                        }
                    ]

                fields: List of standard fields to return (optional).
                    Example: ["code", "description", "sg_status_list"]

                related_fields: Dictionary mapping entity link fields to lists of fields
                               to retrieve from the related entity (optional).
                    Same format as `search_entities_with_related`.

                    Example:
                    {
                        "user": ["name", "email"],
                        "entity": ["code"]
                    }

                order: Sort order (optional).
                    Example: [{"field_name": "updated_at", "direction": "desc"}]

                filter_operator: Logical operator for combining filters (optional).
                    **IMPORTANT**: This is a TOP-LEVEL parameter in the request object, NOT nested inside filters!

                    Values: "all" (AND logic, default) or "any" (OR logic)

                    **CORRECT usage** (filter_operator at top level):
                    {
                        "entity_type": "Version",
                        "filters": [
                            ["sg_status_list", "is", "rev"],
                            ["sg_status_list", "is", "apr"]
                        ],
                        "filter_operator": "any",  # <-- Top-level parameter!
                        "time_filters": [
                            {"field": "created_at", "operator": "in_last", "count": 7, "unit": "DAY"}
                        ]
                    }

                    **WRONG usage** (DO NOT nest filter_operator inside filters):
                    {
                        "entity_type": "Version",
                        "filters": {  # <-- WRONG! filters should be a list, not a dict
                            "filter_operator": "any",
                            "filters": [...]
                        }
                    }

                limit: Maximum number of results (optional).
                    Example: 100

        Returns:
            Dictionary containing:
            - items: List of entities matching the filters
            - entity_type: The type of entity searched
            - fields: All fields returned
            - filter_fields: Fields used in filters
            - total_count: Number of entities found
            - schema_resources: Links to schema information

            Example:
            {
                "items": [
                    {
                        "id": 1234,
                        "code": "SH001",
                        "updated_at": "2025-01-15T10:30:00Z",
                        "user": {
                            "id": 42,
                            "type": "HumanUser",
                            "name": "John Doe"
                        }
                    }
                ],
                "entity_type": "Shot",
                "fields": ["code", "updated_at", "user.HumanUser.name"],
                "filter_fields": ["updated_at"],
                "total_count": 1,
                "schema_resources": {...}
            }

        Raises:
            ToolError: If entity_type is invalid, filters are malformed, or time_filters
                      have invalid operators or units.

        Examples:
            Find shots updated in last week:
            {
                "entity_type": "Shot",
                "filters": [["sg_status_list", "is", "ip"]],
                "time_filters": [
                    {
                        "field": "updated_at",
                        "operator": "in_last",
                        "count": 7,
                        "unit": "DAY"
                    }
                ],
                "fields": ["code", "description"],
                "order": [{"field_name": "updated_at", "direction": "desc"}]
            }

            Find tasks created in last month with assignee info:
            {
                "entity_type": "Task",
                "time_filters": [
                    {
                        "field": "created_at",
                        "operator": "in_last",
                        "count": 1,
                        "unit": "MONTH"
                    }
                ],
                "fields": ["content", "sg_status_list"],
                "related_fields": {
                    "task_assignees": ["name", "email"],
                    "entity": ["code"]
                },
                "limit": 50
            }

            Find versions created today in a specific project:
            {
                "entity_type": "Version",
                "filters": [
                    ["project", "is", {"type": "Project", "id": 123}]
                ],
                "time_filters": [
                    {
                        "field": "created_at",
                        "operator": "in_calendar_day",
                        "count": 0,
                        "unit": "DAY"
                    }
                ],
                "fields": ["code", "sg_status_list"],
                "related_fields": {
                    "user": ["name"]
                }
            }

        Note:
            - Time filters and standard filters are combined with AND logic by default
            - Use filter_operator="any" to change to OR logic
            - Time filters are converted to standard ShotGrid filters internally
            - All time calculations are based on the server's timezone
            - Related fields work the same as in `search_entities_with_related`
        """
        try:
            # Convert filters to list format for process_filters
            # AdvancedSearchRequest validator normalizes to dict format, but process_filters expects list format
            filter_objects = _convert_filters_to_list_format(request.filters or [])

            # Convert any time_filters into Filter instances and then to list format
            time_filter_objects = _convert_time_filters_to_list_format(request.time_filters or [])
            filter_objects.extend(time_filter_objects)

            processed_filters = process_filters(filter_objects)

            all_fields = prepare_fields_with_related(
                sg,
                request.entity_type,
                request.fields,
                request.related_fields,
            )

            find_request = FindRequest(
                entity_type=request.entity_type,
                filters=processed_filters,
                fields=all_fields,
                order=request.order,
                filter_operator=request.filter_operator,
                limit=request.limit,
                page=1,
            )

            result = api_client.find(find_request) or []

            entity_dicts = _convert_entities_to_dicts(result)

            search_result = SearchEntitiesResult(
                items=entity_dicts,
                entity_type=request.entity_type,
                fields=all_fields,
                filter_fields=[f["field"] for f in (request.filters or []) if isinstance(f, dict) and "field" in f],
                total_count=len(entity_dicts),
            )

            response = BaseResponse(
                data=search_result,
                metadata=ResponseMetadata(status="success"),
            )
            return serialize_response(response)
        except Exception as err:  # pragma: no cover - error path
            handle_error(err, operation="sg.search.advanced")
            raise

    # Expose implementation at module level for tests and internal use
    globals()["sg_search_advanced"] = sg_search_advanced


def _find_recently_active_projects(sg: Shotgun, days: int = 90) -> ProjectsResponse:
    """Find projects that have been active in the last N days.

    Args:
        sg: ShotGrid connection.
        days: Number of days to look back (default: 90)

    Returns:
        ProjectsResponse with list of active projects
    """
    try:
        # Create filter using Pydantic model
        filter_obj = create_in_last_filter("updated_at", days, TimeUnit.DAY)
        filters = [filter_obj.to_tuple()]

        fields = ["id", "name", "sg_status", "updated_at", "updated_by"]
        order = [{"field_name": "updated_at", "direction": "desc"}]

        result = sg.find("Project", filters, fields=fields, order=order, page=1)

        if result is None:
            # Use Pydantic model for response
            return ProjectsResponse(projects=[])

        # Convert results to Pydantic models
        project_dicts = [ProjectDict(**serialize_entity(entity)) for entity in result]
        return ProjectsResponse(projects=project_dicts)
    except Exception as err:
        handle_error(err, operation="find_recently_active_projects")
        raise


def _find_active_users(sg: Shotgun, days: int = 30) -> UsersResponse:
    """Find users who have been active in the last N days.

    Note: This uses the 'updated_at' field as a proxy for user activity,
    since HumanUser entities don't have a 'last_login' field.
    A user is considered active if their record was updated recently.

    Args:
        sg: ShotGrid connection.
        days: Number of days to look back (default: 30)

    Returns:
        UsersResponse with list of active users
    """
    try:
        # Create filters using Pydantic models
        status_filter = Filter(field="sg_status_list", operator="is", value="act")
        activity_filter = create_in_last_filter("updated_at", days, TimeUnit.DAY)

        filters = [status_filter.to_tuple(), activity_filter.to_tuple()]
        fields = ["id", "name", "login", "email", "updated_at"]
        order = [{"field_name": "updated_at", "direction": "desc"}]

        result = sg.find("HumanUser", filters, fields=fields, order=order, page=1)

        if result is None:
            # Use Pydantic model for response
            return UsersResponse(users=[])

        # Convert results to Pydantic models
        user_dicts = [UserDict(**serialize_entity(entity)) for entity in result]
        return UsersResponse(users=user_dicts)
    except Exception as err:
        handle_error(err, operation="find_active_users")
        raise


def _find_entities_by_date_range(
    sg: Shotgun,
    entity_type: EntityType,
    date_field: str,
    start_date: str,
    end_date: str,
    additional_filters: Optional[List[Filter]] = None,
    fields: Optional[List[str]] = None,
) -> EntitiesResponse:
    """Find entities within a specific date range.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity to find
        date_field: Field name containing the date to filter on
        start_date: Start date (auto-normalized to ISO 8601, e.g., "2025-11-23" -> "2025-11-23T00:00:00Z")
        end_date: End date (auto-normalized to ISO 8601, e.g., "2025-11-23" -> "2025-11-23T00:00:00Z")
        additional_filters: Additional filters to apply
        fields: Fields to return

    Returns:
        EntitiesResponse with list of entities matching the date range
    """
    try:
        # Import datetime normalization function
        from shotgrid_mcp_server.api_models import _normalize_datetime_value

        # Auto-normalize date values to ISO 8601 format for AI convenience
        normalized_start = _normalize_datetime_value(start_date)
        normalized_end = _normalize_datetime_value(end_date)

        # Create date range filter using Pydantic model
        date_filter = Filter(field=date_field, operator="between", value=[normalized_start, normalized_end])

        filters = [date_filter.to_tuple()]

        # Add any additional filters
        if additional_filters:
            # Process each filter through Pydantic model
            for filter_item in additional_filters:
                if isinstance(filter_item, Filter):
                    filters.append(filter_item.to_tuple())
                else:
                    # Convert tuple to Filter if needed
                    filter_obj = Filter.from_tuple(filter_item)
                    filters.append(filter_obj.to_tuple())

        # Default fields if none provided
        if not fields:
            fields = ["id", "name", date_field]

        # Execute query
        result = sg.find(entity_type, filters, fields=fields, page=1)

        if result is None:
            # Use Pydantic model for response
            return EntitiesResponse(entities=[])

        # Convert results to Pydantic models
        entity_dicts = [EntityDict(**serialize_entity(entity)) for entity in result]
        return EntitiesResponse(entities=entity_dicts)
    except Exception as err:
        handle_error(err, operation="find_entities_by_date_range")
        raise


def register_helper_functions(server: FastMCPType, sg: Shotgun) -> None:
    """Register helper functions for common query patterns.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("project_find_active")
    def find_recently_active_projects(days: int = 90) -> ProjectsResponse:
        """Find projects that have been active in the last N days.

        Args:
            days: Number of days to look back (default: 90)

        Returns:
            ProjectsResponse containing list of active projects
        """
        return _find_recently_active_projects(sg, days)

    @server.tool("user_find_active")
    def find_active_users(days: int = 30) -> UsersResponse:
        """Find users who have been active in the last N days.

        Note: This uses the 'updated_at' field as a proxy for user activity,
        since HumanUser entities don't have a 'last_login' field in ShotGrid.
        A user is considered active if their record was updated recently.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            UsersResponse containing list of active users (status='act' and updated in the last N days)
        """
        return _find_active_users(sg, days)

    @server.tool("entity_find_by_date")
    def find_entities_by_date_range(
        entity_type: EntityType,
        date_field: str,
        start_date: str,
        end_date: str,
        additional_filters: Optional[List[Filter]] = None,
        fields: Optional[List[str]] = None,
    ) -> EntitiesResponse:
        """Find entities within a specific date range.

        Args:
            entity_type: Type of entity to find
            date_field: Field name containing the date to filter on
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            additional_filters: Additional filters to apply
            fields: Fields to return

        Returns:
            EntitiesResponse containing list of entities matching the date range
        """
        return _find_entities_by_date_range(
            sg, entity_type, date_field, start_date, end_date, additional_filters, fields
        )


def prepare_fields_with_related(
    sg: Shotgun,
    entity_type: EntityType,
    fields: Optional[List[str]],
    related_fields: Optional[Dict[str, List[str]]],
) -> List[str]:
    """Prepare fields list with related entity fields.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        fields: List of fields to return.
        related_fields: Dictionary mapping entity fields to lists of fields to return.

    Returns:
        List[str]: List of fields including related fields.
    """
    all_fields = fields or []

    # Add related fields using dot notation
    if related_fields:
        for entity_field, related_field_list in related_fields.items():
            # Get entity type from the field
            field_info = sg.schema_field_read(entity_type, entity_field)
            if not field_info:
                continue

            # Get the entity type for this field
            field_properties = field_info.get("properties", {})
            valid_types = field_properties.get("valid_types", {}).get("value", [])

            if not valid_types:
                continue

            # For each related field, add it with dot notation
            for related_field in related_field_list:
                # Use the first valid type (most common case)
                related_entity_type = valid_types[0]
                dot_field = f"{entity_field}.{related_entity_type}.{related_field}"
                all_fields.append(dot_field)

    return all_fields
