"""Search tools for ShotGrid MCP server.

This module contains tools for searching entities in ShotGrid.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

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
from shotgrid_mcp_server.types import EntityType
from shotgrid_mcp_server.utils import ShotGridJSONEncoder

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

    # Register helper functions
    register_helper_functions(server, sg)


def register_search_entities(server: FastMCPType, sg: Shotgun) -> None:
    """Register search_entities tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("search_entities")
    def search_entities(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],  # Use Dict instead of Filter for FastMCP compatibility
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
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
            # Convert dict filters to Filter objects
            filter_objects = []
            for filter_dict in filters:
                filter_obj = Filter(
                    field=filter_dict["field"], operator=filter_dict["operator"], value=filter_dict["value"]
                )
                filter_objects.append(filter_obj)

            # Process filters
            processed_filters = process_filters(filter_objects)

            # Execute query
            result = sg.find(
                entity_type,
                processed_filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
            )

            # Format response
            if result is None:
                # Use Pydantic model for response
                response = EntitiesResponse(entities=[])
                return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]

            # Convert results to Pydantic models
            entity_dicts = [EntityDict(**serialize_entity(entity)) for entity in result]
            response = EntitiesResponse(entities=entity_dicts)

            return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]
        except Exception as err:
            handle_error(err, operation="search_entities")
            raise  # This is needed to satisfy the type checker


def register_search_with_related(server: FastMCPType, sg: Shotgun) -> None:
    """Register search_entities_with_related tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("search_entities_with_related")
    def search_entities_with_related(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],  # Use Dict instead of Filter for FastMCP compatibility
        fields: Optional[List[str]] = None,
        related_fields: Optional[Dict[str, List[str]]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, str]]:
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
            # Convert dict filters to Filter objects
            filter_objects = []
            for filter_dict in filters:
                filter_obj = Filter(
                    field=filter_dict["field"], operator=filter_dict["operator"], value=filter_dict["value"]
                )
                filter_objects.append(filter_obj)

            # Process filters
            processed_filters = process_filters(filter_objects)

            # Process fields with related entity fields
            all_fields = prepare_fields_with_related(sg, entity_type, fields, related_fields)

            # Execute query
            result = sg.find(
                entity_type,
                processed_filters,
                fields=all_fields,
                order=order,
                filter_operator=filter_operator,
                limit=limit,
            )

            # Format response
            if result is None:
                # Use Pydantic model for response
                response = EntitiesResponse(entities=[])
                return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]

            # Convert results to Pydantic models
            entity_dicts = [EntityDict(**serialize_entity(entity)) for entity in result]
            response = EntitiesResponse(entities=entity_dicts)

            return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]
        except Exception as err:
            handle_error(err, operation="search_entities_with_related")
            raise  # This is needed to satisfy the type checker


def register_find_one_entity(server: FastMCPType, sg: Shotgun) -> None:
    """Register find_one_entity tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("find_one_entity")
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
            # Convert dict filters to Filter objects
            filter_objects = []
            for filter_dict in filters:
                filter_obj = Filter(
                    field=filter_dict["field"], operator=filter_dict["operator"], value=filter_dict["value"]
                )
                filter_objects.append(filter_obj)

            # Process filters
            processed_filters = process_filters(filter_objects)

            result = sg.find_one(
                entity_type,
                processed_filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
            )
            if result is None:
                return [{"text": json.dumps({"entity": None}, cls=ShotGridJSONEncoder)}]

            # Convert result to Pydantic model
            entity_dict = EntityDict(**serialize_entity(result))
            return [{"text": json.dumps({"entity": entity_dict.model_dump()}, cls=ShotGridJSONEncoder)}]
        except Exception as err:
            handle_error(err, operation="find_one_entity")
            raise  # This is needed to satisfy the type checker


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

        result = sg.find("Project", filters, fields=fields, order=order)

        if result is None:
            # Use Pydantic model for response
            response = ProjectsResponse(projects=[])
            return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]

        # Convert results to Pydantic models
        project_dicts = [ProjectDict(**serialize_entity(entity)) for entity in result]
        response = ProjectsResponse(projects=project_dicts)

        return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]
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

        result = sg.find("HumanUser", filters, fields=fields, order=order)

        if result is None:
            # Use Pydantic model for response
            response = UsersResponse(users=[])
            return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]

        # Convert results to Pydantic models
        user_dicts = [UserDict(**serialize_entity(entity)) for entity in result]
        response = UsersResponse(users=user_dicts)

        return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]
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
        result = sg.find(entity_type, filters, fields=fields)

        if result is None:
            # Use Pydantic model for response
            response = EntitiesResponse(entities=[])
            return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]

        # Convert results to Pydantic models
        entity_dicts = [EntityDict(**serialize_entity(entity)) for entity in result]
        response = EntitiesResponse(entities=entity_dicts)

        return [{"text": json.dumps(response.model_dump(), cls=ShotGridJSONEncoder)}]
    except Exception as err:
        handle_error(err, operation="find_entities_by_date_range")
        raise


def register_helper_functions(server: FastMCPType, sg: Shotgun) -> None:
    """Register helper functions for common query patterns.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("find_recently_active_projects")
    def find_recently_active_projects(days: int = 90) -> List[Dict[str, str]]:
        """Find projects that have been active in the last N days.

        Args:
            days: Number of days to look back (default: 90)

        Returns:
            List of active projects
        """
        return _find_recently_active_projects(sg, days)

    @server.tool("find_active_users")
    def find_active_users(days: int = 30) -> List[Dict[str, str]]:
        """Find users who have been active in the last N days.

        Args:
            days: Number of days to look back (default: 30)

        Returns:
            List of active users
        """
        return _find_active_users(sg, days)

    @server.tool("find_entities_by_date_range")
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
