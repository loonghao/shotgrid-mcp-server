"""Thumbnail tools for ShotGrid MCP server.

This module contains tools for working with thumbnails in ShotGrid.
"""

import logging
import os
import ssl
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional, Set

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun
from tenacity import retry, stop_after_attempt, wait_fixed

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.schema_loader import get_entity_types_from_schema, get_entity_fields_with_image_type
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.tools.utils_date import to_iso8601
from shotgrid_mcp_server.tools.utils_file import safe_slug_filename
from shotgrid_mcp_server.utils import generate_default_file_path

# Configure logging
logger = logging.getLogger(__name__)

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

        # Handle different types of field_value
        if isinstance(field_value, str):
            # If field_value is already a URL string, use it directly
            url = field_value
            logger.info("Field value is already a URL: %s", url[:100] + "..." if len(url) > 100 else url)
        elif isinstance(field_value, dict) and 'id' in field_value:
            # If field_value is a dict with id, get the download URL
            attachment_id = field_value['id']
            url = sg.get_attachment_download_url(attachment_id)
        elif isinstance(field_value, int):
            # If field_value is an integer ID, get the download URL
            attachment_id = field_value
            url = sg.get_attachment_download_url(attachment_id)
        else:
            # Try to get the URL using get_attachment_download_url directly
            try:
                url = sg.get_attachment_download_url(field_value)
            except Exception as url_err:
                logger.warning("Failed to get attachment URL: %s", str(url_err))
                raise ToolError(f"Invalid attachment data format: {field_value}") from url_err

        if not url:
            raise ToolError("No thumbnail URL found")

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
) -> Dict[str, Any]:
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

        logger.info("Downloading thumbnail for %s %s to %s", entity_type, entity_id, file_path)

        # Get entity data to get the thumbnail field
        entity = sg.find_one(entity_type, [["id", "is", entity_id]], [field_name])
        if not entity or not entity.get(field_name):
            raise ToolError(f"No thumbnail found for {entity_type} {entity_id}")

        # Get the attachment data
        attachment = entity[field_name]

        # Simplified approach based on sg_thumbnail.py reference
        try:
            # Method 1: Try direct download using download_attachment with URL dict
            if isinstance(attachment, str):
                # If attachment is a URL string, wrap it in a dict
                url_dict = {"url": attachment}
            elif isinstance(attachment, dict) and "url" in attachment:
                # If attachment already has a url key, use it directly
                url_dict = attachment
            elif isinstance(attachment, dict) and "id" in attachment:
                # If attachment has an id, use it directly
                url_dict = attachment
            elif isinstance(attachment, int):
                # If attachment is an integer ID, wrap it in a dict
                url_dict = {"id": attachment}
            else:
                # For other cases, try to use the attachment directly
                url_dict = {"url": attachment} if attachment else None

            if not url_dict:
                raise ToolError(f"Invalid attachment data: {attachment}")

            logger.info("Trying download_attachment with: %s", str(url_dict)[:100] + "..." if len(str(url_dict)) > 100 else str(url_dict))
            result = sg.download_attachment(url_dict, file_path=file_path)

            if result:
                logger.info("Successfully downloaded thumbnail for %s %s to %s using download_attachment",
                           entity_type, entity_id, result)
                return {"file_path": str(result), "entity_type": entity_type, "entity_id": entity_id}
            else:
                raise ToolError("download_attachment returned None")

        except Exception as download_err:
            logger.warning("Method 1 (download_attachment) failed: %s", str(download_err))

            # Method 2: Try to get URL and download with our utility function
            try:
                # Get URL from attachment
                if isinstance(attachment, str):
                    url = attachment
                elif isinstance(attachment, dict) and "url" in attachment:
                    url = attachment["url"]
                elif isinstance(attachment, dict) and "id" in attachment:
                    url = sg.get_attachment_download_url(attachment["id"])
                elif isinstance(attachment, int):
                    url = sg.get_attachment_download_url(attachment)
                else:
                    # Try to get URL directly
                    url = sg.get_attachment_download_url(attachment)

                if not url:
                    raise ToolError("Could not get thumbnail URL")

                logger.info("Got download URL: %s", url[:100] + "..." if len(url) > 100 else url)
                from shotgrid_mcp_server.utils import download_file

                # Try to download with our enhanced download_file function
                download_file(url, file_path)

                logger.info("Successfully downloaded thumbnail for %s %s to %s using download_file",
                           entity_type, entity_id, file_path)
                return {"file_path": str(file_path), "entity_type": entity_type, "entity_id": entity_id}

            except Exception as url_err:
                logger.warning("Method 2 (download_file) failed: %s", str(url_err))

                # Method 3: Last resort - try direct download with completely disabled SSL
                try:
                    # Make sure we have a URL
                    if 'url' not in locals() or not url:
                        raise ToolError("No URL available for direct download")

                    logger.info("Trying direct download with completely disabled SSL")
                    import ssl
                    import urllib.request

                    # Create a context with no verification at all
                    context = ssl._create_unverified_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    # Try with older protocol versions
                    context.options |= ssl.OP_NO_TLSv1_3
                    context.options |= ssl.OP_NO_TLSv1_2
                    context.options |= ssl.OP_NO_TLSv1_1
                    # Force TLSv1.0
                    context.minimum_version = ssl.TLSVersion.TLSv1
                    context.maximum_version = ssl.TLSVersion.TLSv1

                    with urllib.request.urlopen(url, context=context, timeout=30) as response:
                        with open(file_path, 'wb') as out_file:
                            out_file.write(response.read())

                    logger.info("Successfully downloaded thumbnail for %s %s to %s using direct urllib with disabled SSL",
                               entity_type, entity_id, file_path)
                    return {"file_path": str(file_path), "entity_type": entity_type, "entity_id": entity_id}

                except Exception as direct_err:
                    error_msg = f"All download methods failed for {entity_type} {entity_id}: Method 1: {str(download_err)}, Method 2: {str(url_err)}, Method 3: {str(direct_err)}"
                    logger.error(error_msg)
                    raise ToolError(error_msg)

    except Exception as err:
        error_msg = f"Failed to download thumbnail for {entity_type} {entity_id}: {str(err)}"
        logger.error(error_msg)
        handle_error(err, operation="download_thumbnail")
        raise  # This is needed to satisfy the type checker


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

        # Use a smaller number of workers to avoid overwhelming the server
        max_workers = min(5, len(operations))
        logger.info("Starting batch download of %d thumbnails with %d workers", len(operations), max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
            success_count = 0
            error_count = 0
            for future, op_info in futures:
                try:
                    result = future.result()
                    results.append(result)
                    success_count += 1
                except Exception as download_err:
                    error_info = {
                        "error": str(download_err),
                        "entity_type": op_info["entity_type"],
                        "entity_id": op_info["entity_id"],
                    }
                    results.append(error_info)
                    error_count += 1
                    logger.warning("Error downloading thumbnail for %s %s: %s",
                                  op_info["entity_type"], op_info["entity_id"], str(download_err))

        logger.info("Batch download complete: %d successful, %d failed", success_count, error_count)
        return results
    except Exception as err:
        handle_error(err, operation="batch_download_thumbnails")
        raise  # This is needed to satisfy the type checker



@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def download_recent_asset_thumbnails(
    sg: Shotgun,
    days: int = 7,
    project_id: Optional[int] = None,
    field_name: str = "image",
    size: Optional[str] = None,
    image_format: Optional[str] = None,
    directory: Optional[str] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Download thumbnails for recently updated assets.

    Args:
        sg: ShotGrid connection.
        days: Number of days to look back (default: 7).
        project_id: Optional project ID to filter assets by.
        field_name: Name of field containing thumbnail (default: "image").
        size: Optional size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600").
        image_format: Optional format of the image (e.g. "jpg", "png").
        directory: Optional directory to save thumbnails to.
        limit: Maximum number of assets to process (default: 10).

    Returns:
        List[Dict[str, Any]]: Results of the batch operations, each containing file_path.

    Raises:
        ToolError: If the batch operation fails.
    """
    try:
        # Build filters for recently updated assets
        from datetime import datetime, timedelta
        threshold = datetime.now() - timedelta(days=days)

        # Make sure to include the field_name in the query to avoid missing field errors
        fields = ["id", "code", "updated_at", field_name]

        # Create filters for recently updated assets
        filters = [["updated_at", "greater_than", threshold]]

        # Add project filter if provided
        if project_id:
            filters.append(["project", "is", {"type": "Project", "id": project_id}])

        # Order by update date, newest first
        order = [{"field_name": "updated_at", "direction": "desc"}]

        # Find assets
        logger.info("Finding recently updated assets in the last %d days (limit: %d)", days, limit)
        assets = sg.find(
            "Asset",
            filters,
            fields,
            order=order,
            limit=limit
        )

        if not assets:
            logger.info("No recently updated assets found")
            return [{"message": "No recently updated assets found"}]

        logger.info("Found %d recently updated assets", len(assets))

        # Prepare operations for batch download
        operations = []
        for asset in assets:
            asset_id = asset["id"]
            code = asset.get("code", str(asset_id))

            # Check if the asset has the specified field
            if field_name not in asset or not asset[field_name]:
                logger.warning("Asset %s (ID: %s) has no %s field or it's empty", code, asset_id, field_name)
                operations.append({
                    "entity_type": "Asset",
                    "entity_id": asset_id,
                    "error": f"No {field_name} field found or it's empty"
                })
                continue

            file_path = None
            if directory:
                os.makedirs(directory, exist_ok=True)
                image_format_value = image_format or "jpg"
                filename = safe_slug_filename(code, image_format_value)
                file_path = os.path.join(directory, filename)

            operations.append({
                "entity_type": "Asset",
                "entity_id": asset_id,
                "field_name": field_name,
                "file_path": file_path,
                "size": size,
                "image_format": image_format,
            })

        # Execute batch download
        return batch_download_thumbnails(sg=sg, operations=operations)

    except Exception as err:
        handle_error(err, operation="download_recent_asset_thumbnails")
        raise


@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def batch_download_entity_thumbnails(
    sg: Shotgun,
    entity_type: EntityType,
    filters: Optional[List] = None,
    field_name: str = "image",
    size: Optional[str] = None,
    image_format: Optional[str] = None,
    directory: Optional[str] = None,
    limit: Optional[int] = None,
    file_naming_func: Optional[callable] = None,
    filter_operator: str = "and",
) -> List[Dict[str, Any]]:
    """
    Download thumbnails for multiple entities matching filters.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        filters: Filters to find entities. If None, defaults to [].
        field_name: Name of field containing thumbnail.
        size: Optional size of thumbnail (e.g. "thumbnail", "large", or dimensions like "800x600").
        image_format: Optional format of the image (e.g. "jpg", "png").
        directory: Optional directory to save thumbnails to.
        limit: Optional limit on number of entities to process.
        file_naming_func: Optional function to generate file name by entity dict. Defaults to asset name safe conversion.
        filter_operator: Logical operator for combining filters. Must be 'and' or 'or'. Default is 'and'.

    Returns:
        List[Dict[str, Any]]: Results of the batch operations, each containing file_path.

    Raises:
        ToolError: If the batch operation fails.
    """

    try:
        filters = filters or []

        # Validate filter_operator
        if filter_operator not in ["and", "or"]:
            logger.warning("Invalid filter_operator: %s. Must be 'and' or 'or'. Using 'and' as default.", filter_operator)
            filter_operator = "and"

        # Find entities matching filters, include code for file naming and the field_name
        # If filters contain date, ensure ISO8601 using to_iso8601
        patched_filters = []
        for f in (filters or []):
            if isinstance(f, (list, tuple)) and len(f) >= 3 and ("date" in str(f[0]).lower()):
                patched_filters.append([f[0], f[1], to_iso8601(f[2])])
            else:
                patched_filters.append(f)

        # Make sure to include the field_name in the query
        fields = ["id", "code", field_name]

        # Pass filter_operator to sg.find
        entities = sg.find(
            entity_type,
            patched_filters,
            fields,
            limit=limit,
            filter_operator=filter_operator
        )

        if not entities:
            return [{"message": "No entities found matching filters"}]

        operations = []
        for entity in entities:
            entity_id = entity["id"]
            code = entity.get("code", str(entity_id))

            # Check if the entity has the specified field
            if field_name not in entity or not entity[field_name]:
                logger.warning("Entity %s (ID: %s) has no %s field or it's empty", code, entity_id, field_name)
                operations.append({
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                    "error": f"No {field_name} field found or it's empty"
                })
                continue

            file_path = None
            if directory:
                os.makedirs(directory, exist_ok=True)
                image_format_value = image_format or "jpg"
                # Use custom file_naming_func or default to slugified asset name
                if file_naming_func:
                    filename = file_naming_func(entity)
                else:
                    filename = safe_slug_filename(code, image_format_value)
                file_path = os.path.join(directory, filename)
            operations.append({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "field_name": field_name,
                "file_path": file_path,
                "size": size,
                "image_format": image_format,
            })
        return batch_download_thumbnails(sg=sg, operations=operations)

    except Exception as err:
        handle_error(err, operation="batch_download_entity_thumbnails")
        raise


def register_thumbnail_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register thumbnail tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """
    # Get entity types from schema
    entity_types = get_entity_types_from_schema(sg)
    logger.info(f"Registering thumbnail tools with {len(entity_types)} entity types from schema")

    # Register get_thumbnail_url tool
    @server.tool("thumbnail_get_url")
    def get_thumbnail_url_tool(
        entity_type: str,
        entity_id: int,
        field_name: str = "image",
        size: Optional[str] = None,
        image_format: Optional[str] = None,
    ) -> str:
        # Validate entity type if we have schema information
        if entity_types and entity_type not in entity_types:
            raise ToolError(f"Invalid entity type: {entity_type}. Valid types: {', '.join(sorted(entity_types))}")

        # Get image fields for this entity type
        image_fields = get_entity_fields_with_image_type(sg, entity_type)

        # Validate field name
        if image_fields and field_name not in image_fields:
            raise ToolError(f"Invalid field name: {field_name}. Valid image fields for {entity_type}: {', '.join(sorted(image_fields))}")

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
        entity_type: str,
        entity_id: int,
        field_name: str = "image",
        file_path: Optional[str] = None,
        size: Optional[str] = None,
        image_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        # Validate entity type if we have schema information
        if entity_types and entity_type not in entity_types:
            raise ToolError(f"Invalid entity type: {entity_type}. Valid types: {', '.join(sorted(entity_types))}")

        # Get image fields for this entity type
        image_fields = get_entity_fields_with_image_type(sg, entity_type)

        # Validate field name
        if image_fields and field_name not in image_fields:
            raise ToolError(f"Invalid field name: {field_name}. Valid image fields for {entity_type}: {', '.join(sorted(image_fields))}")

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
        # Validate operations
        for i, op in enumerate(operations):
            if "entity_type" in op and entity_types and op["entity_type"] not in entity_types:
                raise ToolError(f"Invalid entity type in operation {i}: {op['entity_type']}")

            if "entity_type" in op and "field_name" in op:
                image_fields = get_entity_fields_with_image_type(sg, op["entity_type"])
                if image_fields and op["field_name"] not in image_fields:
                    raise ToolError(f"Invalid field name in operation {i}: {op['field_name']}. Valid image fields: {', '.join(sorted(image_fields))}")

        return batch_download_thumbnails(sg=sg, operations=operations)

    # Register batch_download_entity_thumbnails tool
    @server.tool("thumbnail_batch_download_by_filter")
    def batch_download_entity_thumbnails_tool(
        entity_type: str,
        filters: List[Dict[str, Any]],
        field_name: str = "image",
        size: Optional[str] = None,
        image_format: Optional[str] = None,
        directory: Optional[str] = None,
        limit: Optional[int] = None,
        filter_operator: str = "and",
    ) -> List[Dict[str, Any]]:
        # Validate entity type if we have schema information
        if entity_types and entity_type not in entity_types:
            raise ToolError(f"Invalid entity type: {entity_type}. Valid types: {', '.join(sorted(entity_types))}")

        # Get image fields for this entity type
        image_fields = get_entity_fields_with_image_type(sg, entity_type)

        # Validate field name
        if image_fields and field_name not in image_fields:
            raise ToolError(f"Invalid field name: {field_name}. Valid image fields for {entity_type}: {', '.join(sorted(image_fields))}")

        return batch_download_entity_thumbnails(
            sg=sg,
            entity_type=entity_type,
            filters=filters,
            field_name=field_name,
            size=size,
            image_format=image_format,
            directory=directory,
            limit=limit,
            filter_operator=filter_operator,
        )

    # Register download_recent_asset_thumbnails tool
    @server.tool("thumbnail_download_recent_assets")
    def download_recent_asset_thumbnails_tool(
        days: int = 7,
        project_id: Optional[int] = None,
        field_name: str = "image",
        size: Optional[str] = None,
        image_format: Optional[str] = None,
        directory: Optional[str] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        # Validate entity type "Asset" if we have schema information
        if entity_types and "Asset" not in entity_types:
            raise ToolError(f"Entity type 'Asset' not found in schema")

        # Get image fields for Asset entity type
        image_fields = get_entity_fields_with_image_type(sg, "Asset")

        # Validate field name
        if image_fields and field_name not in image_fields:
            raise ToolError(f"Invalid field name: {field_name}. Valid image fields for Asset: {', '.join(sorted(image_fields))}")

        return download_recent_asset_thumbnails(
            sg=sg,
            days=days,
            project_id=project_id,
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
            raise ToolError(
                f"Invalid size in operation {i}: {size}. Must be 'thumbnail', 'large', or dimensions like '800x600'."
            )

        # Validate image_format if provided
        image_format = op.get("image_format")
        if image_format and image_format not in ["jpg", "jpeg", "png", "gif"]:
            raise ToolError(
                f"Invalid image_format in operation {i}: {image_format}. Must be 'jpg', 'jpeg', 'png', or 'gif'."
            )
