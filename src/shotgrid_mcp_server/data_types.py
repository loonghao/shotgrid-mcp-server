"""ShotGrid data type utilities.

This module provides utilities for working with ShotGrid data types,
making it easier to convert between Python types and ShotGrid types.
"""

import datetime
from typing import Any, Dict, List, Optional


class ShotGridTypes:
    """Constants for ShotGrid data types."""

    ADDRESSING = "addressing"
    CHECKBOX = "checkbox"
    COLOR = "color"
    CURRENCY = "currency"
    DATE = "date"
    DATE_TIME = "date_time"
    DURATION = "duration"
    ENTITY = "entity"
    FLOAT = "float"
    FOOTAGE = "footage"
    IMAGE = "image"
    LIST = "list"
    MULTI_ENTITY = "multi_entity"
    NUMBER = "number"
    PASSWORD = "password"
    PERCENT = "percent"
    SERIALIZABLE = "serializable"
    STATUS_LIST = "status_list"
    TAG_LIST = "tag_list"
    TEXT = "text"
    TIMECODE = "timecode"
    URL = "url"


def _convert_date_to_shotgrid(value: Any) -> Any:
    """Convert date value to ShotGrid format."""
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")
    return value


def _convert_datetime_to_shotgrid(value: Any) -> Any:
    """Convert datetime value to ShotGrid format."""
    if isinstance(value, datetime.datetime):
        return value
    return value


def _convert_number_to_shotgrid(value: Any) -> Any:
    """Convert number value to ShotGrid format."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return value


def _convert_float_to_shotgrid(value: Any) -> Any:
    """Convert float value to ShotGrid format."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return value


def _convert_entity_to_shotgrid(value: Any) -> Any:
    """Convert entity value to ShotGrid format."""
    if isinstance(value, dict) and "id" in value and "type" in value:
        return value
    elif isinstance(value, int):
        # Assuming this is an entity ID, but we need the type
        return value
    return value


def _convert_multi_entity_to_shotgrid(value: Any) -> Any:
    """Convert multi-entity value to ShotGrid format."""
    if isinstance(value, list):
        return value
    # If it's a single entity, wrap it in a list
    if isinstance(value, dict) and "id" in value and "type" in value:
        return [value]
    return value


def convert_to_shotgrid_type(value: Any, sg_type: str) -> Any:
    """Convert a Python value to the appropriate ShotGrid type.

    Args:
        value: Python value to convert
        sg_type: ShotGrid data type

    Returns:
        Converted value appropriate for ShotGrid API
    """
    if value is None:
        return None

    # Map ShotGrid types to conversion functions
    type_converters = {
        ShotGridTypes.DATE: _convert_date_to_shotgrid,
        ShotGridTypes.DATE_TIME: _convert_datetime_to_shotgrid,
        ShotGridTypes.CHECKBOX: bool,
        ShotGridTypes.NUMBER: _convert_number_to_shotgrid,
        ShotGridTypes.FLOAT: _convert_float_to_shotgrid,
        ShotGridTypes.DURATION: _convert_number_to_shotgrid,
        ShotGridTypes.ENTITY: _convert_entity_to_shotgrid,
        ShotGridTypes.MULTI_ENTITY: _convert_multi_entity_to_shotgrid,
    }

    # Get the appropriate converter function
    converter = type_converters.get(sg_type)
    if converter:
        return converter(value)

    # Default: return as is
    return value


def _convert_date_from_shotgrid(value: Any) -> Any:
    """Convert ShotGrid date value to Python type."""
    if isinstance(value, str):
        try:
            return datetime.datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError:
            pass
    return value


def _convert_datetime_from_shotgrid(value: Any) -> Any:
    """Convert ShotGrid datetime value to Python type."""
    if isinstance(value, str):
        try:
            # Try ISO format first
            return datetime.datetime.fromisoformat(value)
        except ValueError:
            try:
                # Try other common formats
                return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass
    return value


def _convert_duration_from_shotgrid(value: Any) -> Any:
    """Convert ShotGrid duration value to Python type."""
    # Duration is stored in minutes
    if isinstance(value, (int, float)):
        return datetime.timedelta(minutes=value)
    return value


def _convert_timecode_from_shotgrid(value: Any) -> Any:
    """Convert ShotGrid timecode value to Python type."""
    # Timecode is stored in milliseconds
    if isinstance(value, (int, float)):
        return datetime.timedelta(milliseconds=value)
    return value


def convert_from_shotgrid_type(value: Any, sg_type: str) -> Any:
    """Convert a ShotGrid value to the appropriate Python type.

    Args:
        value: ShotGrid value to convert
        sg_type: ShotGrid data type

    Returns:
        Converted value as appropriate Python type
    """
    if value is None:
        return None

    # Map ShotGrid types to conversion functions
    type_converters = {
        ShotGridTypes.DATE: _convert_date_from_shotgrid,
        ShotGridTypes.DATE_TIME: _convert_datetime_from_shotgrid,
        ShotGridTypes.DURATION: _convert_duration_from_shotgrid,
        ShotGridTypes.TIMECODE: _convert_timecode_from_shotgrid,
    }

    # Get the appropriate converter function
    converter = type_converters.get(sg_type)
    if converter:
        return converter(value)

    # Default: return as is
    return value


def get_field_type(schema: Dict[str, Any], entity_type: str, field_name: str) -> Optional[str]:
    """Get the ShotGrid data type for a field.

    Args:
        schema: ShotGrid schema dictionary
        entity_type: Entity type
        field_name: Field name

    Returns:
        ShotGrid data type or None if not found
    """
    if entity_type not in schema:
        return None

    entity_schema = schema[entity_type]
    if "fields" not in entity_schema:
        return None

    field_schema = entity_schema["fields"].get(field_name)
    if not field_schema:
        return None

    data_type = field_schema.get("data_type", {}).get("value")
    return data_type


def is_entity_field(schema: Dict[str, Any], entity_type: str, field_name: str) -> bool:
    """Check if a field is an entity field.

    Args:
        schema: ShotGrid schema dictionary
        entity_type: Entity type
        field_name: Field name

    Returns:
        True if the field is an entity field, False otherwise
    """
    field_type = get_field_type(schema, entity_type, field_name)
    return field_type == ShotGridTypes.ENTITY


def is_multi_entity_field(schema: Dict[str, Any], entity_type: str, field_name: str) -> bool:
    """Check if a field is a multi-entity field.

    Args:
        schema: ShotGrid schema dictionary
        entity_type: Entity type
        field_name: Field name

    Returns:
        True if the field is a multi-entity field, False otherwise
    """
    field_type = get_field_type(schema, entity_type, field_name)
    return field_type == ShotGridTypes.MULTI_ENTITY


def get_entity_field_types(schema: Dict[str, Any], entity_type: str, field_name: str) -> List[str]:
    """Get the valid entity types for an entity field.

    Args:
        schema: ShotGrid schema dictionary
        entity_type: Entity type
        field_name: Field name

    Returns:
        List of valid entity types for the field
    """
    if not is_entity_field(schema, entity_type, field_name) and not is_multi_entity_field(
        schema, entity_type, field_name
    ):
        return []

    field_schema = schema[entity_type]["fields"].get(field_name, {})
    properties = field_schema.get("properties", {})
    valid_types = properties.get("valid_types", {}).get("value", [])

    return valid_types


def format_entity_value(entity_type: str, entity_id: int) -> Dict[str, Any]:
    """Format an entity value for ShotGrid API.

    Args:
        entity_type: Entity type
        entity_id: Entity ID

    Returns:
        Formatted entity dictionary
    """
    return {"type": entity_type, "id": entity_id}


def format_multi_entity_value(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Format a multi-entity value for ShotGrid API.

    Args:
        entities: List of entity dictionaries

    Returns:
        Formatted list of entity dictionaries
    """
    return [{"type": e["type"], "id": e["id"]} for e in entities if "type" in e and "id" in e]
