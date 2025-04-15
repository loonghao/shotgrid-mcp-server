"""Base module for ShotGrid tools.

This module contains common functions and utilities used by all tools.
"""

from datetime import datetime
from typing import Any, Dict

from shotgrid_mcp_server.error_handler import handle_tool_error


def serialize_entity(entity: Any) -> Dict[str, Any]:
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


def handle_error(err: Exception, operation: str) -> None:
    """Handle errors from tool operations.

    Args:
        err: Exception to handle.
        operation: Name of the operation that failed.

    Raises:
        ToolError: Always raised with formatted error message.
    """
    handle_tool_error(err, operation)
