"""Thumbnail tools for ShotGrid MCP server.

This module contains tools for working with thumbnails in ShotGrid.
"""

import asyncio
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

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
        # Find the entity to get the field value
        entity = sg.find_one(entity_type, [["id", "is", entity_id]], [field_name])
        if not entity or field_name not in entity or not entity[field_name]:
            raise ToolError(f"No thumbnail found for {entity_type} with ID {entity_id} in field {field_name}")

        # Get the field value which contains the thumbnail URL or reference
        field_value = entity[field_name]

        # If the field value is a dict with a URL key, use that
        if isinstance(field_value, dict) and "url" in field_value:
            url = field_value["url"]
        else:
            # Otherwise, construct an attachment URL
            attachment = {"id": entity_id, "type": entity_type, "field_name": field_name}
            url = sg.get_attachment_download_url(attachment)

        if not url:
            raise ToolError("No thumbnail URL found")

        # Add size and format parameters if provided
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
        # Generate a default file path if none is provided
        if not file_path:
            image_format_value = image_format or "jpg"
            file_path = generate_default_file_path(entity_type, entity_id, field_name, image_format_value)

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
        return {"file_path": str(result), "entity_type": entity_type, "entity_id": entity_id}
    except Exception as err:
        handle_error(err, operation="download_thumbnail")
        raise  # This is needed to satisfy the type checker


def generate_default_file_path(entity_type: str, entity_id: int, field_name: str = "image", image_format: str = "jpg") -> str:
    """Generate a default file path for a thumbnail.

    Args:
        entity_type: Type of entity.
        entity_id: ID of entity.
        field_name: Name of field containing thumbnail.
        image_format: Format of the image.

    Returns:
        str: Default file path.
    """
    # Create a temporary directory if it doesn't exist
    temp_dir = Path(os.path.expanduser("~")) / ".shotgrid_mcp" / "thumbnails"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate a filename based on entity type, id, and field name
    filename = f"{entity_type}_{entity_id}_{field_name}.{image_format}"
    return str(temp_dir / filename)


async def download_thumbnail_async(sg: Shotgun, op: Dict[str, Any]) -> Dict[str, Any]:
    """Download a thumbnail asynchronously.

    Args:
        sg: ShotGrid connection.
        op: Thumbnail download operation.

    Returns:
        Dict[str, Any]: Result of the download operation.
    """
    entity_type = op["entity_type"]
    entity_id = op["entity_id"]
    field_name = op.get("field_name", "image")
    file_path = op.get("file_path")
    size = op.get("size")
    image_format = op.get("image_format", "jpg")

    # Generate a default file path if none is provided
    if not file_path:
        file_path = generate_default_file_path(entity_type, entity_id, field_name, image_format)

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
        return result
    except Exception as download_err:
        return {"error": str(download_err), "entity_type": entity_type, "entity_id": entity_id}


def batch_download_thumbnails(sg: Shotgun, operations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Download multiple thumbnails in a single batch operation.

    Args:
        sg: ShotGrid connection.
        operations: List of thumbnail download operations. Each operation should have:
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

        # Execute each download operation in parallel using ThreadPoolExecutor
        results = []
        with ThreadPoolExecutor(max_workers=min(10, len(operations))) as executor:
            futures = []
            for op in operations:
                entity_type = op["entity_type"]
                entity_id = op["entity_id"]
                field_name = op.get("field_name", "image")
                file_path = op.get("file_path")
                size = op.get("size")
                image_format = op.get("image_format")

                # Submit download task to executor
                future = executor.submit(
                    download_thumbnail,
                    sg=sg,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    field_name=field_name,
                    file_path=file_path,
                    size=size,
                    image_format=image_format,
                )
                futures.append((future, {"entity_type": entity_type, "entity_id": entity_id}))

            # Collect results
            for future, op_info in futures:
                try:
                    result = future.result()
                    results.append(result)
                except Exception as download_err:
                    results.append({
                        "error": str(download_err),
                        "entity_type": op_info["entity_type"],
                        "entity_id": op_info["entity_id"]
                    })

        return results
    except Exception as err:
        handle_error(err, operation="batch_download_thumbnails")
        raise  # This is needed to satisfy the type checker


def batch_download_entity_thumbnails(
    sg: Shotgun,
    entity_type: EntityType,
    filters: List[Dict[str, Any]],
    field_name: str = "image",
    size: Optional[str] = None,
    image_format: Optional[str] = None,
    directory: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Download thumbnails for multiple entities matching filters.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        filters: Filters to find entities.
        field_name: Name of field containing thumbnail.
        size: Optional size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600").
        image_format: Optional format of the image (e.g. "jpg", "png").
        directory: Optional directory to save thumbnails to.
        limit: Optional limit on number of entities to process.

    Returns:
        List[Dict[str, Any]]: Results of the batch operations, each containing file_path.

    Raises:
        ToolError: If the batch operation fails.
    """
    try:
        # Find entities matching filters
        entities = sg.find(entity_type, filters, ["id"], limit=limit)
        if not entities:
            return [{"message": "No entities found matching filters"}]

        # Create operations for each entity
        operations = []
        for entity in entities:
            entity_id = entity["id"]
            file_path = None
            if directory:
                # Create directory if it doesn't exist
                os.makedirs(directory, exist_ok=True)
                # Generate filename
                image_format_value = image_format or "jpg"
                filename = f"{entity_type}_{entity_id}_{field_name}.{image_format_value}"
                file_path = os.path.join(directory, filename)

            operations.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "field_name": field_name,
                "file_path": file_path,
                "size": size,
                "image_format": image_format,
            })

        # Download thumbnails in batch
        return batch_download_thumbnails(sg=sg, operations=operations)
    except Exception as err:
        handle_error(err, operation="batch_download_entity_thumbnails")
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

    # Register batch_download_entity_thumbnails tool
    @server.tool("thumbnail_batch_download_by_filter")
    def batch_download_entity_thumbnails_tool(
        entity_type: EntityType,
        filters: List[Dict[str, Any]],
        field_name: str = "image",
        size: Optional[str] = None,
        image_format: Optional[str] = None,
        directory: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        return batch_download_entity_thumbnails(
            sg=sg,
            entity_type=entity_type,
            filters=filters,
            field_name=field_name,
            size=size,
            image_format=image_format,
            directory=directory,
            limit=limit,
        )


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
        # Check for required fields
        if "entity_type" not in op:
            raise ToolError(f"Missing entity_type in operation {i}")

        if "entity_id" not in op:
            raise ToolError(f"Missing entity_id in operation {i}")

        # Validate entity_id is an integer
        entity_id = op.get("entity_id")
        if not isinstance(entity_id, int):
            raise ToolError(f"Invalid entity_id in operation {i}: {entity_id}. Must be an integer.")

        # Validate size format if provided
        size = op.get("size")
        if size and not (size in ["thumbnail", "large"] or "x" in size):
            raise ToolError(f"Invalid size in operation {i}: {size}. Must be 'thumbnail', 'large', or dimensions like '800x600'.")

        # Validate image_format if provided
        image_format = op.get("image_format")
        if image_format and image_format not in ["jpg", "jpeg", "png", "gif"]:
            raise ToolError(f"Invalid image_format in operation {i}: {image_format}. Must be 'jpg', 'jpeg', 'png', or 'gif'.")

