"""Custom exceptions for ShotGrid MCP server.

This module defines custom exception types for the ShotGrid MCP server.
"""

from fastmcp.exceptions import ToolError


class ShotGridMCPError(ToolError):
    """Base class for all ShotGrid MCP server errors."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(message)


class FilterError(ShotGridMCPError):
    """Error raised when a filter is invalid."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(f"Filter error: {message}")


class SerializationError(ShotGridMCPError):
    """Error raised when serialization fails."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(f"Serialization error: {message}")


class EntityNotFoundError(ShotGridMCPError):
    """Error raised when an entity is not found."""

    def __init__(self, entity_type: str = None, entity_id: int = None, message: str = None):
        """Initialize the error.

        Args:
            entity_type: Type of entity that was not found.
            entity_id: Optional ID of the entity.
            message: Optional custom message.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id

        if message:
            error_message = message
        elif entity_type and entity_id:
            error_message = f"{entity_type} with ID {entity_id} not found"
        elif entity_type:
            error_message = f"{entity_type} not found"
        else:
            error_message = "Entity not found"
        super().__init__(error_message)


class PermissionError(ShotGridMCPError):
    """Error raised when a user does not have permission to perform an action."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(f"Permission denied: {message}")


class ConnectionError(ShotGridMCPError):
    """Error raised when a connection to ShotGrid fails."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(f"Connection error: {message}")


class ConfigurationError(ShotGridMCPError):
    """Error raised when there is a configuration error."""

    def __init__(self, message: str):
        """Initialize the error.

        Args:
            message: Error message.
        """
        super().__init__(f"Configuration error: {message}")


class NoAvailableInstancesError(Exception):
    """Pool manager does not have any available instances to provide"""
