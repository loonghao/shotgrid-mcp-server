"""Thumbnail tools for ShotGrid MCP server.

This module contains tools for working with thumbnails in ShotGrid.
"""

from typing import Any, Dict, List, Optional

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.types import EntityType


def get_thumbnail_url(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    field_name: str = "image",
    size: Optional[str] = None,
    image_format: Optional[str] = None,
) -> str:
    """Get thumbnail URL for an entity.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        entity_id: ID of entity.
        field_name: Name of field containing thumbnail.
        size: Optional size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600").
        image_format: Optional format of the image (e.g. "jpg", "png").

    Returns:
        str: Thumbnail URL.

    Raises:
        ToolError: If the URL retrieval fails.
    """
    try:
        # Get the base thumbnail URL
        result = sg.get_thumbnail_url(entity_type, entity_id, field_name)
        if not result:
            raise ToolError("No thumbnail URL found")

        # Add size and format parameters if provided
        url = str(result)
        params = []

        if size:
            params.append(f"size={size}")

        if image_format:
            params.append(f"image_format={image_format}")

        # Append parameters to URL if any were provided
        if params:
            url_separator = "&" if "?" in url else "?"
            joined_params = "&".join(params)
            url = f"{url}{url_separator}{joined_params}"

        return url
    except Exception as err:
        handle_error(err, operation="get_thumbnail_url")
        raise  # This is needed to satisfy the type checker


def download_thumbnail(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    field_name: str = "image",
    file_path: Optional[str] = None,
    size: Optional[str] = None,
    image_format: Optional[str] = None,
) -> Dict[str, str]:
    """Download a thumbnail for an entity.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        entity_id: ID of entity.
        field_name: Name of field containing thumbnail.
        file_path: Optional path to save thumbnail to.
        size: Optional size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600").
        image_format: Optional format of the image (e.g. "jpg", "png").

    Returns:
        Dict[str, str]: Path to downloaded thumbnail.

    Raises:
        ToolError: If the download fails.
    """
    try:
        # Get thumbnail URL with size and format parameters
        url = get_thumbnail_url(
            sg=sg,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            size=size,
            image_format=image_format,
        )

        # Download thumbnail
        result = sg.download_attachment({"url": url}, file_path)
        if result is None:
            raise ToolError("Failed to download thumbnail")
        return {"file_path": str(result)}
    except Exception as err:
        handle_error(err, operation="download_thumbnail")
        raise  # This is needed to satisfy the type checker


def batch_download_thumbnails(sg: Shotgun, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Download multiple thumbnails in a single batch operation.

    Args:
        sg: ShotGrid connection.
        operations: List of thumbnail download operations. Each operation should have:
            - request_type: "download_thumbnail"
            - entity_type: Type of entity
            - entity_id: ID of entity
            - field_name: (Optional) Name of field containing thumbnail, defaults to "image"
            - file_path: (Optional) Path to save thumbnail to
            - size: (Optional) Size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600")
            - image_format: (Optional) Format of the image (e.g. "jpg", "png")

    Returns:
        List[Dict[str, Any]]: Results of the batch operations, each containing file_path.

    Raises:
        ToolError: If the batch operation fails.
    """
    try:
        # Validate operations
        validate_thumbnail_batch_operations(operations)

        # Execute each download operation
        results = []
        for op in operations:
            entity_type = op["entity_type"]
            entity_id = op["entity_id"]
            field_name = op.get("field_name", "image")
            file_path = op.get("file_path")
            size = op.get("size")
            image_format = op.get("image_format")

            try:
                # Use the download_thumbnail function to handle the operation
                result = download_thumbnail(
                    sg=sg,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    file_path=file_path,
                    size=size,
                    image_format=image_format,
                )
                results.append(result)
            except Exception as download_err:
                results.append({"error": str(download_err)})

        return results
    except Exception as err:
        handle_error(err, operation="batch_download_thumbnails")
        raise  # This is needed to satisfy the type checker


def register_thumbnail_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register thumbnail tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    # Register get_thumbnail_url tool
    @server.tool("thumbnail_get_url")
    def get_thumbnail_url_tool(
        entity_type: EntityType,
        entity_id: int,
        field_name: str = "image",
        size: Optional[str] = None,
        image_format: Optional[str] = None,
    ) -> str:
        return get_thumbnail_url(
            sg=sg,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            size=size,
            image_format=image_format,
        )

    # Register download_thumbnail tool
    @server.tool("thumbnail_download")
    def download_thumbnail_tool(
        entity_type: EntityType,
        entity_id: int,
        field_name: str = "image",
        file_path: Optional[str] = None,
        size: Optional[str] = None,
        image_format: Optional[str] = None,
    ) -> Dict[str, str]:
        return download_thumbnail(
            sg=sg,
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            file_path=file_path,
            size=size,
            image_format=image_format,
        )

    # Register batch_download_thumbnails tool
    @server.tool("batch_thumbnail_download")
    def batch_download_thumbnails_tool(operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        return batch_download_thumbnails(sg=sg, operations=operations)


def validate_thumbnail_batch_operations(operations: List[Dict[str, Any]]) -> None:
    """Validate thumbnail batch operations.

    Args:
        operations: List of operations to validate.

    Raises:
        ToolError: If any operation is invalid.
    """
    if not operations:
        raise ToolError("No operations provided for batch thumbnail download")

    # Validate each operation
    for i, op in enumerate(operations):
        request_type = op.get("request_type")
        if request_type != "download_thumbnail":
            raise ToolError(f"Invalid request_type in operation {i}: {request_type}. Must be 'download_thumbnail'")

        if "entity_type" not in op:
            raise ToolError(f"Missing entity_type in operation {i}")

        if "entity_id" not in op:
            raise ToolError(f"Missing entity_id in operation {i}")
