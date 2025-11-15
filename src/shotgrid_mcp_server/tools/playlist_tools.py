"""Playlist tools for ShotGrid MCP server.

This module contains tools for working with Playlists in ShotGrid.
"""

import logging
from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.models import (
    TimeUnit,
    create_in_last_filter,
    create_in_project_filter,
    process_filters,
)
from shotgrid_mcp_server.response_models import (
    create_playlist_response,
    generate_playlist_url_variants,
    serialize_response,
)
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import FastMCPType

# Configure logging
logger = logging.getLogger(__name__)


def _get_default_playlist_fields() -> List[str]:
    """Get default fields for playlist queries.

    Returns:
        List[str]: Default fields to retrieve for playlists.
    """
    return ["id", "code", "description", "created_at", "updated_at", "created_by", "versions", "project"]


def _serialize_playlists_response(playlists: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Serialize playlists to JSON response.

    Args:
        playlists: List of playlists to serialize.

    Returns:
        List[Dict[str, str]]: Serialized playlists response.
    """
    from shotgrid_mcp_server.response_models import create_success_response

    # Serialize each playlist
    serialized_playlists = [serialize_entity(playlist) for playlist in playlists]

    # Create standardized response
    response = create_success_response(
        data=serialized_playlists,
        message=f"Found {len(serialized_playlists)} playlists",
        total_count=len(serialized_playlists),
    )

    # Return serialized response for FastMCP
    return serialize_response(response)


def _find_playlists_impl(
    sg: Shotgun,
    filters: Optional[List] = None,
    fields: Optional[List[str]] = None,
    order: Optional[List[Dict[str, str]]] = None,
    filter_operator: Optional[str] = None,
    limit: Optional[int] = None,
    page: Optional[int] = None,
    page_size: Optional[int] = None,
) -> Dict[str, Any]:
    """Implementation for finding playlists.

    Args:
        sg: ShotGrid connection.
        filters: List of filters to apply.
        fields: Optional list of fields to return.
        order: Optional list of fields to order by.
        filter_operator: Optional filter operator.
        limit: Optional limit on number of entities to return.

    Returns:
        List[Dict[str, str]]: List of playlists found.
    """
    # Default fields if none provided
    if fields is None:
        fields = _get_default_playlist_fields()

    # Default filters if none provided
    if filters is None:
        filters = []

    # Handle pagination
    if page is not None and page_size is not None:
        # Set limit to page_size
        limit = page_size

    # Execute query
    # Note: Mockgun doesn't support retired_only parameter
    try:
        result = sg.find(
            "Playlist",
            filters,
            fields=fields,
            order=order,
            filter_operator=filter_operator,
            limit=limit,
            retired_only=False,
        )
    except TypeError:
        # Fallback for Mockgun which doesn't support retired_only
        result = sg.find(
            "Playlist",
            filters,
            fields=fields,
            order=order,
            filter_operator=filter_operator,
            limit=limit,
        )

    # Add ShotGrid URLs to each playlist
    for playlist in result:
        if "id" in playlist:
            playlist_id = playlist["id"]
            project_id = None
            project = playlist.get("project")
            if isinstance(project, dict):
                project_id = project.get("id")

            urls = generate_playlist_url_variants(sg.base_url, playlist_id, project_id)

            # Primary URL used by existing clients
            playlist["sg_url"] = urls["screening_room"]
            # Full set of URL variants for AI/clients to choose from
            playlist["sg_urls"] = urls

    # Serialize and return results
    return _serialize_playlists_response(result)


def register_playlist_tools(server: FastMCPType, sg: Shotgun) -> None:  # noqa: C901
    """Register playlist tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("find_playlists")
    def find_playlists(
        filters: Optional[List[Dict[str, Any]]] = None,
        fields: Optional[List[str]] = None,
        order: Optional[List[Dict[str, str]]] = None,
        filter_operator: Optional[str] = None,
        limit: Optional[int] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Find playlists in ShotGrid.

        Args:
            filters: Optional list of filters to apply. Each filter is a dictionary with field, operator, and value keys.
                     If not provided, all playlists will be returned (subject to other filters).
            fields: Optional list of fields to return.
            order: Optional list of fields to order by.
            filter_operator: Optional filter operator.
            limit: Optional limit on number of entities to return.
            page: Optional page number for pagination.
            page_size: Optional page size for pagination.

        Returns:
            List[Dict[str, str]]: List of playlists found.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Process filters if provided
            processed_filters = process_filters(filters) if filters else []

            # Find playlists
            return _find_playlists_impl(
                sg,
                processed_filters,
                fields,
                order,
                filter_operator,
                limit,
                page,
                page_size,
            )
        except Exception as err:
            handle_error(err, operation="find_playlists")
            raise  # This is needed to satisfy the type checker

    @server.tool("find_project_playlists")
    def find_project_playlists(
        project_id: int,
        fields: Optional[List[str]] = None,
        days: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Find playlists in a specific project.

        Args:
            project_id: ID of project to find playlists for.
            fields: Optional list of fields to return.
            days: Optional number of days to look back.
            limit: Optional limit on number of playlists to return.

        Returns:
            List[Dict[str, str]]: List of playlists found.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Build filters
            filters = [["project", "is", {"type": "Project", "id": project_id}]]

            # Add date filter if days provided
            if days:
                date_filter = create_in_last_filter("created_at", days, "DAY")
                filters.append(date_filter.to_tuple())

            # Order by creation date, newest first
            order = [{"field_name": "created_at", "direction": "desc"}]

            # Find playlists
            return _find_playlists_impl(
                sg,
                filters,
                fields,
                order,
                None,
                limit,
            )
        except Exception as err:
            handle_error(err, operation="find_project_playlists")
            raise  # This is needed to satisfy the type checker

    @server.tool("find_recent_playlists")
    def find_recent_playlists(
        days: int = 7,
        project_id: Optional[int] = None,
        limit: Optional[int] = 20,
        fields: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Find recent playlists in ShotGrid.

        Args:
            days: Number of days to look back (default: 7).
            project_id: Optional project ID to filter playlists by.
            limit: Optional limit on number of playlists to return (default: 20).
            fields: Optional list of fields to return.

        Returns:
            List[Dict[str, str]]: List of playlists found.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Build filters
            filters = []

            # Add project filter if provided
            if project_id:
                project_filter = create_in_project_filter(project_id)
                filters.append(project_filter.to_tuple())

            # Add date filter
            date_filter = create_in_last_filter("created_at", days, TimeUnit.DAY)
            filters.append(date_filter.to_tuple())

            # Order by creation date, newest first
            order = [{"field_name": "created_at", "direction": "desc"}]

            # Find playlists
            return _find_playlists_impl(
                sg,
                filters,
                fields,
                order,
                None,
                limit,
            )
        except Exception as err:
            handle_error(err, operation="find_recent_playlists")
            raise  # This is needed to satisfy the type checker

    @server.tool("create_playlist")
    def create_playlist(
        code: str,
        project_id: int,
        description: Optional[str] = None,
        versions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a playlist in ShotGrid.

        Args:
            code: Code/name of the playlist.
            project_id: ID of the project to create the playlist in.
            description: Optional description of the playlist.
            versions: Optional list of versions to add to the playlist.

        Returns:
            Dict[str, Any]: Created playlist.

        Raises:
            ToolError: If the create operation fails.
        """
        try:
            # Build playlist data
            data = {
                "code": code,
                "project": {"type": "Project", "id": project_id},
            }

            # Add description if provided
            if description:
                data["description"] = description

            # Add versions if provided
            if versions:
                data["versions"] = versions

            # Create playlist
            result = sg.create("Playlist", data)
            if result is None:
                raise ValueError("Failed to create playlist")

            # Generate playlist URLs
            playlist_id = result["id"]
            project_id = None
            project = result.get("project")
            if isinstance(project, dict):
                project_id = project.get("id")

            urls = generate_playlist_url_variants(sg.base_url, playlist_id, project_id)
            playlist_url = urls["screening_room"]
            result["sg_url"] = playlist_url
            result["sg_urls"] = urls

            # Serialize the entity
            serialized_entity = serialize_entity(result)

            # Create standardized response
            response = create_playlist_response(
                data=serialized_entity,
                url=playlist_url,
                message="Playlist created successfully",
            )

            # Return serialized response for FastMCP
            return serialize_response(response)
        except Exception as err:
            handle_error(err, operation="create_playlist")
            raise  # This is needed to satisfy the type checker

    @server.tool("update_playlist")
    def update_playlist(
        playlist_id: int,
        code: Optional[str] = None,
        description: Optional[str] = None,
        versions: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        """Update a playlist in ShotGrid.

        Args:
            playlist_id: ID of the playlist to update.
            code: Optional new code/name for the playlist.
            description: Optional new description for the playlist.
            versions: Optional new list of versions for the playlist.

        Raises:
            ToolError: If the update operation fails.
        """
        try:
            # Build update data
            data = {}

            if code is not None:
                data["code"] = code

            if description is not None:
                data["description"] = description

            if versions is not None:
                data["versions"] = versions

            # Ensure we have data to update
            if not data:
                raise ValueError("No update data provided")

            # Update playlist
            result = sg.update("Playlist", playlist_id, data)
            if result is None:
                raise ValueError(f"Failed to update playlist with ID {playlist_id}")

            return None
        except Exception as err:
            handle_error(err, operation="update_playlist")
            raise  # This is needed to satisfy the type checker

    @server.tool("add_versions_to_playlist")
    def add_versions_to_playlist(
        playlist_id: int,
        version_ids: List[int],
    ) -> None:
        """Add versions to a playlist in ShotGrid.

        Args:
            playlist_id: ID of the playlist to update.
            version_ids: List of version IDs to add to the playlist.

        Raises:
            ToolError: If the update operation fails.
        """
        try:
            # Get current versions in playlist
            playlist = sg.find_one("Playlist", [["id", "is", playlist_id]], ["versions"])
            if playlist is None:
                raise ValueError(f"Playlist with ID {playlist_id} not found")

            # Get current version IDs
            current_versions = playlist.get("versions", [])
            current_version_ids = [v["id"] for v in current_versions] if current_versions else []

            # Add new versions
            version_entities = []
            for version_id in version_ids:
                if version_id not in current_version_ids:
                    version_entities.append({"type": "Version", "id": version_id})

            # If no new versions to add, return
            if not version_entities:
                return None

            # Update playlist with new versions
            all_versions = current_versions + version_entities
            result = sg.update("Playlist", playlist_id, {"versions": all_versions})
            if result is None:
                raise ValueError(f"Failed to update playlist with ID {playlist_id}")

            return None
        except Exception as err:
            handle_error(err, operation="add_versions_to_playlist")
            raise  # This is needed to satisfy the type checker

    # Expose playlist tool implementations at module level for tests and internal use
    globals()["find_playlists"] = find_playlists
    globals()["find_project_playlists"] = find_project_playlists
    globals()["find_recent_playlists"] = find_recent_playlists
    globals()["create_playlist"] = create_playlist
    globals()["update_playlist"] = update_playlist
    globals()["add_versions_to_playlist"] = add_versions_to_playlist
