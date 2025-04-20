"""Response models for ShotGrid MCP server.

This module contains Pydantic models for standardizing responses from ShotGrid MCP tools.
"""

import json
from datetime import date, datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field


class ShotGridJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles ShotGrid special data types.

    This encoder handles datetime objects, Pydantic models, and other ShotGrid-specific data types
    to ensure proper serialization in JSON responses.
    """

    def default(self, obj: Any) -> Any:
        """Convert special data types to JSON-serializable formats.

        Args:
            obj: Object to encode.

        Returns:
            JSON-serializable representation of the object.
        """
        if isinstance(obj, datetime):
            # Format datetime with timezone info if available
            if obj.tzinfo is not None:
                return obj.isoformat()
            # Add Z suffix for UTC time without timezone
            return f"{obj.isoformat()}Z"
        elif isinstance(obj, date):
            # Format date as YYYY-MM-DD
            return obj.isoformat()
        # Handle Pydantic models
        elif hasattr(obj, "model_dump") and callable(obj.model_dump):
            return obj.model_dump()
        # Handle older Pydantic models or other objects with to_dict method
        elif hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return str(obj)
        # Handle timedelta objects
        elif hasattr(obj, "total_seconds") and callable(obj.total_seconds):
            # Convert timedelta to seconds
            return obj.total_seconds()
        return super().default(obj)

T = TypeVar("T")


class ResponseMetadata(BaseModel):
    """Metadata for a response."""

    status: str = "success"
    message: Optional[str] = None
    error_type: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None


class BaseResponse(BaseModel, Generic[T]):
    """Base response model for all ShotGrid MCP tools."""

    data: T
    metadata: ResponseMetadata = Field(default_factory=ResponseMetadata)


class EntityResponse(BaseResponse[Dict[str, Any]]):
    """Response model for a single entity."""

    url: Optional[str] = None


class EntitiesResponse(BaseResponse[List[Dict[str, Any]]]):
    """Response model for multiple entities."""

    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


class PlaylistResponse(EntityResponse):
    """Response model for a playlist."""

    url: str


class NoteResponse(EntityResponse):
    """Response model for a note."""


class VersionResponse(EntityResponse):
    """Response model for a version."""


class UserResponse(EntityResponse):
    """Response model for a user."""


class ProjectResponse(EntityResponse):
    """Response model for a project."""


class ErrorResponse(BaseResponse[None]):
    """Response model for an error."""

    def __init__(self, message: str, error_type: str, error_details: Optional[Dict[str, Any]] = None):
        """Initialize the error response.

        Args:
            message: Error message.
            error_type: Type of error.
            error_details: Optional details about the error.
        """
        metadata = ResponseMetadata(
            status="error",
            message=message,
            error_type=error_type,
            error_details=error_details,
        )
        super().__init__(data=None, metadata=metadata)


def create_success_response(
    data: Any,
    message: Optional[str] = None,
    url: Optional[str] = None,
    total_count: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """Create a success response.

    Args:
        data: Response data.
        message: Optional success message.
        url: Optional URL for the entity.
        total_count: Optional total count of entities.
        page: Optional current page number.
        page_size: Optional page size.

    Returns:
        Dict[str, Any]: Standardized response dictionary.
    """
    if isinstance(data, dict):
        # Single entity response
        response = EntityResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
        )
        if url:
            response.url = url
        return response.model_dump(exclude_none=True)
    elif isinstance(data, list):
        # Multiple entities response
        response = EntitiesResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
            total_count=total_count or len(data),
            page=page,
            page_size=page_size,
        )
        return response.model_dump(exclude_none=True)
    else:
        # Generic response
        response = BaseResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
        )
        return response.model_dump(exclude_none=True)


def create_error_response(
    message: str,
    error_type: str,
    error_details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create an error response.

    Args:
        message: Error message.
        error_type: Type of error.
        error_details: Optional details about the error.

    Returns:
        Dict[str, Any]: Standardized error response dictionary.
    """
    response = ErrorResponse(
        message=message,
        error_type=error_type,
        error_details=error_details,
    )
    return response.model_dump(exclude_none=True)


def create_playlist_response(
    data: Dict[str, Any],
    url: str,
    message: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a playlist response.

    Args:
        data: Playlist data.
        url: URL for the playlist.
        message: Optional success message.

    Returns:
        Dict[str, Any]: Standardized playlist response dictionary.
    """
    response = PlaylistResponse(
        data=data,
        metadata=ResponseMetadata(status="success", message=message),
        url=url,
    )
    return response.model_dump(exclude_none=True)


def generate_playlist_url(base_url: str, playlist_id: int) -> str:
    """Generate ShotGrid URL for a playlist.

    Args:
        base_url: ShotGrid base URL.
        playlist_id: ID of the playlist.

    Returns:
        str: URL to access the playlist in ShotGrid web interface.
    """
    # Remove trailing slash if present
    if base_url.endswith("/"):
        base_url = base_url[:-1]

    # Construct the playlist URL
    # Format: https://<shotgrid-domain>/Playlist/detail/<playlist_id>
    return f"{base_url}/Playlist/detail/{playlist_id}"


def serialize_response(response: Dict[str, Any]) -> List[Dict[str, str]]:
    """Serialize a response for FastMCP.

    Args:
        response: Response dictionary.

    Returns:
        List[Dict[str, str]]: Serialized response for FastMCP.
    """
    return [{"text": json.dumps(response, cls=ShotGridJSONEncoder)}]
