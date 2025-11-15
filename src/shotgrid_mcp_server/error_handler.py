"""Error handling utilities for ShotGrid MCP server.

This module provides consistent error handling for the ShotGrid MCP server.
"""

# Import built-in modules
import logging
import re
from datetime import datetime
from typing import Any, Dict, Optional, Type

# Import third-party modules
from fastmcp.exceptions import ToolError
from shotgun_api3 import ShotgunError

# Import local modules
from shotgrid_mcp_server.exceptions import (
    ConnectionError,
    EntityNotFoundError,
    FilterError,
    PermissionError,
    SerializationError,
)

# Configure logging
logger = logging.getLogger(__name__)


def format_error_message(error_msg: str) -> str:
    """Format an error message for consistent output.

    Args:
        error_msg: The original error message.

    Returns:
        str: The formatted error message.
    """
    # Remove common prefixes
    if "Error getting thumbnail URL:" in error_msg:
        error_msg = error_msg.replace("Error getting thumbnail URL: ", "")
    if "Error downloading thumbnail:" in error_msg:
        error_msg = error_msg.replace("Error downloading thumbnail: ", "")
    if "Error executing tool" in error_msg:
        error_msg = error_msg.split(": ", 1)[1]

    # Standardize terminology
    error_msg = error_msg.replace("with id", "with ID")
    if "has no image" in error_msg:
        error_msg = "No thumbnail URL found"

    return error_msg


def handle_tool_error(err: Exception, operation: str) -> None:
    """Handle errors from tool operations.

    Args:
        err: Exception to handle.
        operation: Name of the operation that failed.

    Raises:
        ToolError: Always raised with formatted error message.
    """
    error_msg = format_error_message(str(err))
    logger.error("Error in %s: %s", operation, error_msg)

    # Map ShotgunError to appropriate custom error types
    if isinstance(err, ShotgunError):
        error_msg_lower = str(err).lower()

        if "not found" in error_msg_lower or "does not exist" in error_msg_lower:
            # Try to extract entity type and ID from error message
            entity_type_match = re.search(r"entity (\w+) with", error_msg_lower)
            entity_id_match = re.search(r"with id (\d+)", error_msg_lower)

            entity_type = entity_type_match.group(1).capitalize() if entity_type_match else None
            entity_id = int(entity_id_match.group(1)) if entity_id_match else None

            raise EntityNotFoundError(entity_type=entity_type, entity_id=entity_id, message=error_msg) from err
        elif "connection" in error_msg_lower or "timeout" in error_msg_lower or "network" in error_msg_lower:
            raise ConnectionError(error_msg) from err
        elif "permission" in error_msg_lower or "access" in error_msg_lower or "not allowed" in error_msg_lower:
            raise PermissionError(error_msg) from err
        elif _is_invalid_status_value_error(str(err)):
            hint = (
                f"{error_msg}. "
                "Hint: this looks like an invalid status value for a status_list field. "
                "Use the MCP resources 'shotgrid://schema/statuses' or "
                "'shotgrid://schema/statuses/{entity_type}' to discover the allowed "
                "status codes before calling update tools."
            )
            raise ToolError(hint) from err
    # Handle other specific error types
    elif "filter" in error_msg.lower() or "invalid filter" in error_msg.lower():
        raise FilterError(error_msg) from err
    elif "serialize" in error_msg.lower() or "json" in error_msg.lower():
        raise SerializationError(error_msg) from err

    # Default case: use generic ToolError
    raise ToolError(f"Error executing tool {operation}: {error_msg}") from err


def create_error_response(
    error: Exception, operation: str, error_type: Optional[Type[Exception]] = None
) -> Dict[str, Any]:
    """Create a standardized error response.

    Args:
        error: The exception that occurred.
        operation: Name of the operation that failed.
        error_type: Optional type of error to report.

    Returns:
        Dict[str, Any]: Dictionary containing error details.
    """
    error_msg = format_error_message(str(error))
    logger.error("Error in %s: %s", operation, error_msg)

    # Determine error category
    error_category = "unknown"
    if isinstance(error, EntityNotFoundError) or is_entity_not_found_error(error):
        error_category = "not_found"
    elif isinstance(error, PermissionError) or is_permission_error(error):
        error_category = "permission"
    elif isinstance(error, FilterError):
        error_category = "filter"
    elif isinstance(error, SerializationError):
        error_category = "serialization"
    elif isinstance(error, ConnectionError):
        error_category = "connection"
    elif isinstance(error, ShotgunError):
        error_category = "shotgrid"

    # Create detailed error response
    response = {
        "error": f"Error executing {operation}: {error_msg}",
        "error_type": error_type.__name__ if error_type else error.__class__.__name__,
        "error_category": error_category,
        "operation": operation,
        "timestamp": datetime.now().isoformat(),
    }

    # Add additional context for specific error types
    if hasattr(error, "entity_type") and hasattr(error, "entity_id"):
        response["entity_type"] = error.entity_type
        response["entity_id"] = error.entity_id

    return response


def is_entity_not_found_error(error: Exception) -> bool:
    """Check if an error is an entity not found error.

    Args:
        error: The exception to check.

    Returns:
        bool: True if the error is an entity not found error.
    """
    if isinstance(error, ShotgunError):
        error_msg = str(error).lower()
        return "not found" in error_msg or "does not exist" in error_msg
    return False


def is_permission_error(error: Exception) -> bool:
    """Check if an error is a permission error.

    Args:
        error: The exception to check.

    Returns:
        bool: True if the error is a permission error.
    """
    if isinstance(error, ShotgunError):
        error_msg = str(error).lower()
        return "permission" in error_msg or "access" in error_msg or "not allowed" in error_msg
    return False


def _is_invalid_status_value_error(raw_message: str) -> bool:
    """Heuristically detect invalid status-field value errors.

    This relies on patterns commonly seen in ShotGrid error messages
    when a status_list field receives an unsupported value. It is
    deliberately conservative: if the message does not clearly look like
    a status validation error, we return False so that the generic
    ToolError path is used instead.
    """

    msg = raw_message.lower()

    # Fast path: only consider messages that mention status fields.
    if "sg_status_list" not in msg and "status_list" not in msg and "status" not in msg:
        return False

    markers = [
        "invalid value",
        "invalid status",
        "must be one of",
        "valid values are",
        "valid values:",
        "not in",
        "is not a valid choice",
        "is not a valid value",
    ]

    return any(marker in msg for marker in markers)
