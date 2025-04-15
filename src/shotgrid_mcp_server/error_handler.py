"""Error handling utilities for ShotGrid MCP server.

This module provides consistent error handling for the ShotGrid MCP server.
"""

# Import built-in modules
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Type

# Import third-party modules
from fastmcp.exceptions import ToolError
from shotgun_api3 import ShotgunError

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

    return {
        "error": f"Error executing {operation}: {error_msg}",
        "error_type": error_type.__name__ if error_type else error.__class__.__name__,
        "timestamp": datetime.now().isoformat(),
    }


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
