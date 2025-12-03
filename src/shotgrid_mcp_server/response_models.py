"""Response models for ShotGrid MCP server.

This module contains Pydantic models for standardizing responses from ShotGrid MCP tools.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar, Union

from pydantic import BaseModel, Field

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.models import EntityDict

T = TypeVar("T")


def get_default_schema_resources() -> Dict[str, str]:
    """Get default schema resource URIs.

    Returns a dictionary of schema resource URIs that can be included in responses
    to provide AI clients with contextual schema information.

    Returns:
        Dict[str, str]: Dictionary mapping resource names to their URIs.
    """
    return {
        "entities": "shotgrid://schema/entities",
        "statuses": "shotgrid://schema/statuses",
    }


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format.

    Args:
        size_bytes: File size in bytes.

    Returns:
        Human-readable file size string (e.g., '15.2 MB').
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


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


class SearchEntitiesResult(BaseModel):
    """Structured payload for entity search results.

    This model is designed to be AI-friendly while still mapping cleanly to
    the underlying ShotGrid Python API results.
    """

    items: List[EntityDict]
    entity_type: EntityType
    fields: Optional[List[str]] = None
    filter_fields: Optional[List[str]] = None
    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class SingleEntityResult(BaseModel):
    """Structured payload for a single-entity lookup.

    Used by tools such as entity_find_one so that responses remain
    consistent with the BaseResponse[T] pattern.
    """

    entity: Optional[EntityDict] = None
    entity_type: Optional[EntityType] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)

    total_count: Optional[int] = None
    page: Optional[int] = None
    page_size: Optional[int] = None


class EntityCreateResult(BaseModel):
    """Structured payload for entity creation results."""

    entity: EntityDict
    entity_type: EntityType
    sg_url: Optional[str] = Field(default=None, description="ShotGrid URL to view the created entity")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class EntityUpdateResult(BaseModel):
    """Structured payload for entity update results."""

    entity: EntityDict
    entity_type: EntityType
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class EntityDeleteResult(BaseModel):
    """Structured payload for entity deletion results."""

    success: bool
    entity_type: EntityType
    entity_id: int
    message: Optional[str] = None


class SchemaResult(BaseModel):
    """Structured payload for schema query results."""

    entity_type: EntityType
    fields: Dict[str, Any]
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class VendorUsersResult(BaseModel):
    """Structured payload for vendor users query results."""

    users: List[EntityDict]
    total_count: int
    message: Optional[str] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class VendorVersionsResult(BaseModel):
    """Structured payload for vendor versions query results."""

    versions: List[EntityDict]
    total_count: int
    message: Optional[str] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class PlaylistsResult(BaseModel):
    """Structured payload for playlists query results."""

    playlists: List[EntityDict]
    total_count: int
    message: Optional[str] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class BatchOperationsResult(BaseModel):
    """Structured payload for batch operations results."""

    results: List[EntityDict]
    total_count: int
    success_count: int
    failure_count: int
    message: Optional[str] = None
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class UploadResult(BaseModel):
    """Structured payload for file upload results.

    This model provides AI-friendly information about the upload operation,
    including file details and progress information that can be used for
    reporting to users.
    """

    # Core result fields
    attachment_id: int = Field(..., description="The ShotGrid Attachment entity ID created for the uploaded file")
    success: bool = Field(default=True, description="Whether the upload completed successfully")

    # Entity context
    entity_type: EntityType = Field(..., description="The entity type the file was uploaded to")
    entity_id: int = Field(..., gt=0, description="The entity ID the file was uploaded to")
    field_name: str = Field(..., description="The field name the file was uploaded to")

    # File information (AI-friendly for progress reporting)
    file_name: str = Field(..., description="Original file name")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    file_size_display: str = Field(..., description="Human-readable file size (e.g., '15.2 MB')")
    display_name: Optional[str] = Field(None, description="Display name used for the file in ShotGrid")

    # Progress information (useful for AI to report)
    status: str = Field(default="completed", description="Upload status: 'completed', 'failed'")
    message: str = Field(..., description="Human-readable status message for AI to report to users")

    # Optional metadata
    content_type: Optional[str] = Field(None, description="MIME type of the uploaded file")
    tag_list: Optional[List[str]] = Field(None, description="Tags applied to the uploaded file")

    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class DeleteResult(BaseModel):
    """Structured payload for delete operation results.

    Provides AI-friendly information about the delete operation result.
    """

    success: bool = Field(..., description="Whether the delete operation was successful")
    entity_type: EntityType = Field(..., description="The type of entity that was deleted")
    entity_id: int = Field(..., gt=0, description="The ID of the deleted entity")
    message: str = Field(..., description="Human-readable status message for AI to report")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class ReviveResult(BaseModel):
    """Structured payload for revive operation results.

    Provides AI-friendly information about the revive operation result.
    """

    success: bool = Field(..., description="Whether the revive operation was successful")
    entity_type: EntityType = Field(..., description="The type of entity that was revived")
    entity_id: int = Field(..., gt=0, description="The ID of the revived entity")
    message: str = Field(..., description="Human-readable status message for AI to report")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class DownloadResult(BaseModel):
    """Structured payload for download attachment results.

    Provides AI-friendly information about the download operation.
    """

    success: bool = Field(default=True, description="Whether the download completed successfully")
    file_path: str = Field(..., description="Path where the file was saved")
    file_name: str = Field(..., description="Name of the downloaded file")
    file_size_bytes: int = Field(..., ge=0, description="File size in bytes")
    file_size_display: str = Field(..., description="Human-readable file size")
    attachment_id: Optional[int] = Field(None, description="ShotGrid Attachment ID if available")
    attachment_name: Optional[str] = Field(None, description="Original attachment name from ShotGrid")
    message: str = Field(..., description="Human-readable status message for AI to report")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class FollowResult(BaseModel):
    """Structured payload for follow/unfollow operation results.

    Provides AI-friendly information about the follow operation.
    """

    success: bool = Field(..., description="Whether the operation was successful")
    action: str = Field(..., description="Action performed: 'follow' or 'unfollow'")
    entity_type: EntityType = Field(..., description="The type of entity")
    entity_id: int = Field(..., gt=0, description="The ID of the entity")
    user_id: Optional[int] = Field(None, description="The user ID if specified")
    message: str = Field(..., description="Human-readable status message for AI to report")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


class ProjectAccessResult(BaseModel):
    """Structured payload for project last accessed update results.

    Provides AI-friendly information about the operation.
    """

    success: bool = Field(..., description="Whether the operation was successful")
    project_id: int = Field(..., gt=0, description="The project ID that was updated")
    message: str = Field(..., description="Human-readable status message for AI to report")
    schema_resources: Dict[str, str] = Field(default_factory=get_default_schema_resources)


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
) -> Union[EntityResponse, EntitiesResponse, BaseResponse]:
    """Create a success response.

    Args:
        data: Response data.
        message: Optional success message.
        url: Optional URL for the entity.
        total_count: Optional total count of entities.
        page: Optional current page number.
        page_size: Optional page size.

    Returns:
        Union[EntityResponse, EntitiesResponse, BaseResponse]: Standardized response model.
    """
    if isinstance(data, dict):
        # Single entity response
        response = EntityResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
        )
        if url:
            response.url = url
        return response
    elif isinstance(data, list):
        # Multiple entities response
        response = EntitiesResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
            total_count=total_count or len(data),
            page=page,
            page_size=page_size,
        )
        return response
    else:
        # Generic response
        response = BaseResponse(
            data=data,
            metadata=ResponseMetadata(status="success", message=message),
        )
        return response


def create_error_response(
    message: str,
    error_type: str,
    error_details: Optional[Dict[str, Any]] = None,
) -> ErrorResponse:
    """Create an error response.

    Args:
        message: Error message.
        error_type: Type of error.
        error_details: Optional details about the error.

    Returns:
        ErrorResponse: Standardized error response model.
    """
    return ErrorResponse(
        message=message,
        error_type=error_type,
        error_details=error_details,
    )


def create_playlist_response(
    data: Dict[str, Any],
    url: str,
    message: Optional[str] = None,
) -> PlaylistResponse:
    """Create a playlist response.

    Args:
        data: Playlist data.
        url: URL for the playlist.
        message: Optional success message.

    Returns:
        PlaylistResponse: Standardized playlist response model.
    """
    return PlaylistResponse(
        data=data,
        metadata=ResponseMetadata(status="success", message=message),
        url=url,
    )


def generate_entity_url(base_url: str, entity_type: str, entity_id: int) -> str:
    """Generate ShotGrid URL for any entity.

    This returns the detail page URL for an entity, which is the standard
    way to view any entity in ShotGrid.

    Args:
        base_url: The base URL for the ShotGrid instance (e.g., https://your-site.shotgunstudio.com).
        entity_type: The type of entity (e.g., "Asset", "Shot", "Task").
        entity_id: The ID of the entity.

    Returns:
        str: The detail page URL for the entity.

    Examples:
        >>> generate_entity_url("https://example.shotgunstudio.com", "Asset", 123)
        'https://example.shotgunstudio.com/detail/Asset/123'
    """
    base = base_url.rstrip("/")
    return f"{base}/detail/{entity_type}/{entity_id}"


def generate_playlist_url_variants(base_url: str, playlist_id: int, project_id: Optional[int] = None) -> Dict[str, str]:
    """Generate multiple ShotGrid URLs for a playlist.

    This returns several commonly used entrypoints so that clients or
    AI assistants can choose the most appropriate one for the context.
    """
    base = base_url.rstrip("/")

    urls: Dict[str, str] = {
        "screening_room": f"{base}/page/screening_room?entity_type=Playlist&entity_id={playlist_id}",
        "detail": f"{base}/detail/Playlist/{playlist_id}",
    }

    if project_id is not None:
        urls["media_center"] = f"{base}/page/media_center?type=Playlist&id={playlist_id}&project_id={project_id}"

    return urls


def generate_playlist_url(base_url: str, playlist_id: int) -> str:
    """Generate default ShotGrid URL for a playlist.

    Currently this returns the Screening Room URL, which is the
    recommended entrypoint for review.
    """
    urls = generate_playlist_url_variants(base_url, playlist_id)
    return urls["screening_room"]


def serialize_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare a response for FastMCP.

    Args:
        response: Response dictionary.

    Returns:
        Dict[str, Any]: Structured response for FastMCP.
    """
    # If response is already a Pydantic model, use model_dump
    if hasattr(response, "model_dump") and callable(response.model_dump):
        return response.model_dump(exclude_none=True)

    # Otherwise, return the response directly
    return response
