"""Search tools for ShotGrid MCP server.

This module contains tools for searching entities in ShotGrid.
"""

import logging
from typing import Any, Dict, List, Optional

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
from shotgrid_mcp_server.models import (
    EntitiesResponse,
    EntityDict,
    Filter,
    ProjectDict,
    ProjectsResponse,
    TimeUnit,
    UserDict,
    UsersResponse,
    create_in_last_filter,
    process_filters,
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
        sg: ShotGrid connection.
    """
    # Create API client
    api_client = ShotGridAPIClient(sg)

    @server.tool("search_entities")
    def search_entities(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],  # Use Dict instead of Filter for FastMCP compatibility
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> EntitiesResponse:
        """Find entities in ShotGrid.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply. Each filter is a dictionary with field, operator, and value keys.
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
            # Create request model with validation
            request = SearchEntitiesRequest(
                entity_type=entity_type,
                filters=filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
            )

            # Convert dict filters to Filter objects
            filter_objects = []
            for filter_dict in request.filters:
                try:
                    filter_obj = Filter(
                        field=filter_dict["field"], operator=filter_dict["operator"], value=filter_dict["value"]
                    )
                    filter_objects.append(filter_obj)
                except Exception as e:
                    # Fallback to tuple format if Filter validation fails
                    logger.warning(f"Filter validation failed: {e}. Using tuple format instead.")
                    filter_objects.append((filter_dict["field"], filter_dict["operator"], filter_dict["value"]))

            # Process filters
            processed_filters = process_filters(filter_objects)

            # Create FindRequest for API client
            find_request = FindRequest(
                entity_type=request.entity_type,
                filters=processed_filters,
                fields=request.fields,
                order=request.order,
                filter_operator=request.filter_operator,
                limit=request.limit,
                page=1,  # Set a default page value to avoid "page parameter must be a positive integer" error
            )

            # Execute query through API client
            result = api_client.find(find_request)

            # Format response
            if result is None:
                # Use Pydantic model for response
                return EntitiesResponse(entities=[])

            # Convert results to Pydantic models
            entity_dicts = []
            for entity in result:
                # Serialize entity data
                serialized_entity = serialize_entity(entity)

                # Ensure id field is present
                if "id" not in serialized_entity and entity.get("id"):
                    serialized_entity["id"] = entity["id"]

                # Convert to Pydantic model if possible
                try:
                    entity_dict = EntityDict(**serialized_entity)
                    entity_dicts.append(entity_dict)
                except Exception as e:
                    # Log warning and skip this entity
                    logger.warning(f"Failed to convert entity to EntityDict: {e}")
                    # Add a minimal valid entity
                    if "id" in serialized_entity and "type" in serialized_entity:
                        entity_dicts.append(EntityDict(id=serialized_entity["id"], type=serialized_entity["type"]))

            return EntitiesResponse(entities=entity_dicts)
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
    def search_entities_with_related(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],  # Use Dict instead of Filter for FastMCP compatibility
        fields: Optional[List[str]] = None,
        related_fields: Optional[Dict[str, List[str]]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> EntitiesResponse:
        """Find entities in ShotGrid with related entity fields.

        This method uses field hopping to efficiently retrieve data from related entities
        in a single query, reducing the number of API calls needed.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply. Each filter is a dictionary with field, operator, and value keys.
            fields: Optional list of fields to return from the main entity.
            related_fields: Optional dictionary mapping entity fields to lists of fields to return
                from related entities. For example: {"project": ["name", "sg_status"]}
            order: Optional list of fields to order by.
            filter_operator: Optional filter operator.
            limit: Optional limit on number of entities to return.

        Returns:
            List[Dict[str, str]]: List of entities found with related fields.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Create request model with validation
            request = SearchEntitiesWithRelatedRequest(
                entity_type=entity_type,
                filters=filters,
                fields=fields,
                related_fields=related_fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
            )

            # Use the new process_filters function that can handle dictionaries directly
            processed_filters = process_filters(request.filters)

            # Process fields with related entity fields
            all_fields = prepare_fields_with_related(sg, request.entity_type, request.fields, request.related_fields)

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
            result = api_client.find(find_request)

            # Format response
            if result is None:
                # Use Pydantic model for response
                return EntitiesResponse(entities=[])

            # Convert results to Pydantic models
            entity_dicts = []
            for entity in result:
                # Serialize entity data
                serialized_entity = serialize_entity(entity)

                # Ensure id field is present
                if "id" not in serialized_entity and entity.get("id"):
                    serialized_entity["id"] = entity["id"]

                # Convert to Pydantic model if possible
                try:
                    entity_dict = EntityDict(**serialized_entity)
                    entity_dicts.append(entity_dict)
                except Exception as e:
                    # Log warning and skip this entity
                    logger.warning(f"Failed to convert entity to EntityDict: {e}")
                    # Add a minimal valid entity
                    if "id" in serialized_entity and "type" in serialized_entity:
                        entity_dicts.append(EntityDict(id=serialized_entity["id"], type=serialized_entity["type"]))

            return EntitiesResponse(entities=entity_dicts)
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
    def find_one_entity(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],  # Use Dict instead of Filter for FastMCP compatibility
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Find a single entity in ShotGrid.

        Args:
            entity_type: Type of entity to find.
            filters: List of filters to apply. Each filter is a dictionary with field, operator, and value keys.
            fields: Optional list of fields to return.
            order: Optional list of fields to order by.
            filter_operator: Optional filter operator.

        Returns:
            List[Dict[str, str]]: Entity found, or None if not found.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Create request model with validation
            request = FindOneEntityRequest(
                entity_type=entity_type,
                filters=filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
            )

            # Use the new process_filters function that can handle dictionaries directly
            processed_filters = process_filters(request.filters)

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

            if result is None:
                return {"entity": None}

            # Serialize entity data
            serialized_entity = serialize_entity(result)

            # Ensure id field is present
            if "id" not in serialized_entity and result.get("id"):
                serialized_entity["id"] = result["id"]

            # Convert to Pydantic model if possible
            try:
                entity_dict = EntityDict(**serialized_entity)
                return {"entity": entity_dict}
            except Exception as e:
                # Fallback to returning the serialized entity directly
                logger.warning(f"Failed to convert entity to EntityDict: {e}")
                return {"entity": serialized_entity}
        except Exception as err:
            handle_error(err, operation="find_one_entity")
            raise  # This is needed to satisfy the type checker


def register_advanced_search_tool(server: FastMCPType, sg: Shotgun) -> None:
    """Register sg.search.advanced tool.

    This tool provides a more flexible search entry point that combines
    standard filters with time-based filters and related_fields support.
    """

    api_client = ShotGridAPIClient(sg)

    @server.tool("sg.search.advanced")
    def sg_search_advanced(
        entity_type: EntityType,
        filters: Optional[List[Dict[str, Any]]] = None,
        time_filters: Optional[List[Dict[str, Any]]] = None,
        fields: Optional[List[str]] = None,
        related_fields: Optional[Dict[str, List[str]]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> EntitiesResponse:
        """Advanced search for entities in ShotGrid.

        Args:
            entity_type: Type of entity to find.
            filters: List of standard filters to apply.
            time_filters: Optional list of time-based filters, such as
                ``in_last`` or ``in_next`` filters.
            fields: Optional list of fields to return from the main entity.
            related_fields: Optional dictionary mapping entity fields to lists
                of fields to return from related entities.
            order: Optional list of fields to order by.
            filter_operator: Optional logical operator for combining filters.
            limit: Optional limit on number of entities to return.

        Returns:
            List of entities found.
        """
        try:
            request = AdvancedSearchRequest(
                entity_type=entity_type,
                filters=filters or [],
                time_filters=time_filters or [],
                fields=fields,
                related_fields=related_fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
            )

            filter_objects: List[Any] = []

            # Standard filters are passed through to process_filters as
            # dictionaries to reuse existing normalization logic.
            filter_objects.extend(request.filters)

            # Convert any time_filters into Filter instances so they can be
            # processed in the same way as other filters.
            for time_filter in request.time_filters:
                try:
                    filter_objects.append(time_filter.to_filter())
                except Exception as exc:  # pragma: no cover - defensive
                    logger.warning("Failed to convert time filter %s: %s", time_filter, exc)

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

            result = api_client.find(find_request)

            if result is None:
                return EntitiesResponse(entities=[])

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

            return EntitiesResponse(entities=entity_dicts)
        except Exception as err:  # pragma: no cover - error path
            handle_error(err, operation="sg.search.advanced")
            raise

    # Expose implementation at module level for tests and internal use
    globals()["sg_search_advanced"] = sg_search_advanced


def _find_recently_active_projects(sg: Shotgun, days: int = 90) -> List[Dict[str, str]]:
    """Find projects that have been active in the last N days.

    Args:
        sg: ShotGrid connection.
        days: Number of days to look back (default: 90)

    Returns:
        List of active projects
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


def _find_active_users(sg: Shotgun, days: int = 30) -> List[Dict[str, str]]:
    """Find users who have been active in the last N days.

    Args:
        sg: ShotGrid connection.
        days: Number of days to look back (default: 30)

    Returns:
        List of active users
    """
    try:
        # Create filters using Pydantic models
        status_filter = Filter(field="sg_status_list", operator="is", value="act")
        login_filter = create_in_last_filter("last_login", days, TimeUnit.DAY)

        filters = [status_filter.to_tuple(), login_filter.to_tuple()]
        fields = ["id", "name", "login", "email", "last_login"]
        order = [{"field_name": "last_login", "direction": "desc"}]

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
) -> List[Dict[str, str]]:
    """Find entities within a specific date range.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity to find
        date_field: Field name containing the date to filter on
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        additional_filters: Additional filters to apply
        fields: Fields to return

    Returns:
        List of entities matching the date range
    """
    try:
        # Create date range filter using Pydantic model
        date_filter = Filter(field=date_field, operator="between", value=[start_date, end_date])

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
    def find_recently_active_projects(days: int = 90) -> List[Dict[str, str]]:
        """Find projects that have been active in the last N days.

        Args:
            days: Number of days to look back (default: 90)

        Returns:
            List of active projects
        """
        return _find_recently_active_projects(sg, days)

    @server.tool("user_find_active")
    def find_active_users(days: int = 30) -> List[Dict[str, str]]:
        """Find users who have been active in the last N days.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            List of active users
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
    ) -> List[Dict[str, str]]:
        """Find entities within a specific date range.

        Args:
            entity_type: Type of entity to find
            date_field: Field name containing the date to filter on
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            additional_filters: Additional filters to apply
            fields: Fields to return

        Returns:
            List of entities matching the date range
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
