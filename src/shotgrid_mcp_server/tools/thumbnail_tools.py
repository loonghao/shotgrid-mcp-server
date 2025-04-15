"""Thumbnail tools for ShotGrid MCP server.

This module contains tools for working with thumbnails in ShotGrid.
"""

import json
from typing import Dict, List, Optional

from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType
from shotgrid_mcp_server.types import EntityType


def register_thumbnail_tools(server: FastMCPType, sg: Shotgun) -> None:
    """Register thumbnail tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("get_thumbnail_url")
    def get_thumbnail_url(
        entity_type: EntityType,
        entity_id: int,
        field_name: str = "image",
        size: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Get thumbnail URL for an entity.

        Args:
            entity_type: Type of entity.
            entity_id: ID of entity.
            field_name: Name of field containing thumbnail.
            size: Optional size of thumbnail.

        Returns:
            List[Dict[str, str]]: Thumbnail URL.

        Raises:
            ToolError: If the URL retrieval fails.
        """
        try:
            result = sg.get_thumbnail_url(entity_type, entity_id, field_name)
            if not result:
                raise ToolError("No thumbnail URL found")
            return [{"text": str(result)}]
        except Exception as err:
            handle_error(err, operation="get_thumbnail_url")
            raise  # This is needed to satisfy the type checker

    @server.tool("download_thumbnail")
    def download_thumbnail(
        entity_type: EntityType,
        entity_id: int,
        field_name: str = "image",
        file_path: Optional[str] = None,
    ) -> List[Dict[str, str]]:
        """Download a thumbnail for an entity.

        Args:
            entity_type: Type of entity.
            entity_id: ID of entity.
            field_name: Name of field containing thumbnail.
            file_path: Optional path to save thumbnail to.

        Returns:
            List[Dict[str, str]]: Path to downloaded thumbnail.

        Raises:
            ToolError: If the download fails.
        """
        try:
            # Get thumbnail URL
            url = sg.get_thumbnail_url(entity_type, entity_id, field_name)
            if not url:
                raise ToolError("No thumbnail URL found")

            # Download thumbnail
            result = sg.download_attachment({"url": url}, file_path)
            if result is None:
                raise ToolError("Failed to download thumbnail")
            return [{"text": json.dumps({"file_path": str(result)})}]
        except Exception as err:
            handle_error(err, operation="download_thumbnail")
            raise  # This is needed to satisfy the type checker
