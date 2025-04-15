"""Search tools for ShotGrid MCP server.

This module contains tools for searching entities in ShotGrid.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.types import EntityType, Filter


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


def register_search_entities(server: FastMCPType, sg: Shotgun) -> None:
    """Register search_entities tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("search_entities")
    def search_entities(
        entity_type: EntityType,
        filters: List[Filter],
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
            processed_filters = process_filters(filters)

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
                return [{"text": json.dumps({"entities": []})}]
            return [{"text": json.dumps({"entities": result})}]
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
        filters: List[Filter],
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
            filters: List of filters to apply. Each filter is a list of [field, operator, value].
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
            # Process filters
            processed_filters = process_filters(filters)

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
                return [{"text": json.dumps({"entities": []})}]
            return [{"text": json.dumps({"entities": result})}]
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
        filters: List[Filter],
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
            result = sg.find_one(
                entity_type,
                filters,
                fields=fields,
                order=order,
                filter_operator=filter_operator,
            )
            if result is None:
                return [{"text": json.dumps({"text": None})}]
            return [{"text": json.dumps({"text": serialize_entity(result)})}]
        except Exception as err:
            handle_error(err, operation="find_one_entity")
            raise  # This is needed to satisfy the type checker


def process_filters(filters: List[Filter]) -> List[Tuple[str, str, Any]]:
    """Process filters to handle special values.

    Args:
        filters: List of filters to process.

    Returns:
        List[Filter]: Processed filters.
    """
    processed_filters = []
    for field, operator, value in filters:
        if isinstance(value, str) and value.startswith("$"):
            # Handle special values
            if value == "$today":
                value = datetime.now().strftime("%Y-%m-%d")
        processed_filters.append([field, operator, value])
    return processed_filters  # type: ignore[return-value]


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
