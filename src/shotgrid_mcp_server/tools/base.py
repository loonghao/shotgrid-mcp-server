"""Base module for ShotGrid tools.

This module contains common functions and utilities used by all tools.
"""

from shotgrid_mcp_server.error_handler import handle_tool_error

# Re-export serialize_entity for backward compatibility
from shotgrid_mcp_server.utils import serialize_entity  # noqa: F401


def handle_error(err: Exception, operation: str) -> None:
    """Handle errors from tool operations.

    Args:
        err: Exception to handle.
        operation: Name of the operation that failed.

    Raises:
        ToolError: Always raised with formatted error message.
    """
    handle_tool_error(err, operation)
