"""Playlist tools for ShotGrid MCP server.

This module contains tools for working with Playlists in ShotGrid.
"""

import logging
from typing import Any, Dict, List, Optional

# Import from shotgrid-query
from shotgrid_query import TimeUnitEnum as TimeUnit
from shotgrid_query import process_filters
from shotgun_api3.lib.mockgun import Shotgun

# Import MCP-specific models
from shotgrid_mcp_server.models import (
    create_in_last_filter,
    create_in_project_filter,
)
from shotgrid_mcp_server.response_models import (
    PlaylistsResult,
    generate_playlist_url_variants,
)
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import EntityDict, FastMCPType

# Configure logging
logger = logging.getLogger(__name__)


def _get_default_playlist_fields() -> List[str]:
    """Get default fields for playlist queries.

    Returns:
        List[str]: Default fields to retrieve for playlists.
    """
    return ["id", "code", "description", "created_at", "updated_at", "created_by", "versions", "project"]


def _serialize_playlists_response(playlists: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Serialize playlists to JSON response using Pydantic model.

    Args:
        playlists: List of playlists to serialize.

    Returns:
        Dict[str, Any]: Serialized playlists response with schema resources.
    """
    from typing import cast

    # Serialize each playlist
    serialized_playlists = [cast(EntityDict, serialize_entity(playlist)) for playlist in playlists]

    # Return structured result
    return PlaylistsResult(
        playlists=serialized_playlists,
        total_count=len(serialized_playlists),
        message=f"Found {len(serialized_playlists)} playlists",
    ).model_dump()


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
        """Find playlists in ShotGrid using filters and field selection.

        **When to use this tool:**
        - Search for playlists with specific criteria (project, creator, date range)
        - Find playlists containing specific versions
        - Search for playlists by name pattern
        - Get playlists with custom field selection
        - Apply complex filtering logic (AND/OR operators)

        **When NOT to use this tool:**
        - To find recent playlists only - Use `find_recent_playlists` instead (simpler)
        - To find playlists in a specific project only - Use `find_project_playlists` instead
        - To create new playlists - Use `create_playlist` instead
        - To update playlists - Use `update_entity` with entity_type="Playlist" instead
        - To delete playlists - Use `delete_entity` with entity_type="Playlist" instead

        **Common use cases:**
        - Find dailies playlists: Filter by code containing "dailies"
        - Find playlists for review: Filter by project and date range
        - Find user's playlists: Filter by created_by user ID
        - Find playlists with specific versions: Filter by versions field

        Args:
            filters: Optional list of filter conditions.
                    If not provided, returns all playlists (subject to limit).

                    Filter format (same as search_entities):
                    [
                        ["field_name", "operator", value],
                        ...
                    ]

                    Common filters:

                    By project:
                    [["project", "is", {"type": "Project", "id": 123}]]

                    By creator:
                    [["created_by", "is", {"type": "HumanUser", "id": 42}]]

                    By date range:
                    [["created_at", "in_last", 7, "DAY"]]

                    By name pattern:
                    [["code", "contains", "dailies"]]

                    Multiple filters (AND logic):
                    [
                        ["project", "is", {"type": "Project", "id": 123}],
                        ["created_at", "in_last", 30, "DAY"]
                    ]

            fields: Optional list of fields to return.
                   If not provided, returns default fields:
                   ["id", "code", "description", "created_at", "updated_at",
                    "created_by", "versions", "project"]

                   Additional useful fields:
                   - "sg_status": Playlist status
                   - "sg_date_and_time": Scheduled review date/time
                   - "sg_client_approved": Client approval status

                   Example:
                   ["code", "description", "versions", "created_at"]

            order: Optional sort order.
                  Format: [{"field_name": "field", "direction": "asc|desc"}]

                  Examples:

                  Newest first:
                  [{"field_name": "created_at", "direction": "desc"}]

                  Alphabetical:
                  [{"field_name": "code", "direction": "asc"}]

                  Multiple sort fields:
                  [
                      {"field_name": "project", "direction": "asc"},
                      {"field_name": "created_at", "direction": "desc"}
                  ]

            filter_operator: Logical operator for combining filters.
                           Values: "all" (AND, default) or "any" (OR)

                           Example with OR logic:
                           filter_operator="any" combines filters with OR

            limit: Maximum number of playlists to return.
                  Useful for limiting large result sets.

                  Example: 50

            page: Page number for pagination (1-based).
                 Used with page_size for paginated results.

                 Example: 1 (first page)

            page_size: Number of playlists per page.
                      Used with page for pagination.

                      Example: 20

        Returns:
            Dictionary containing:
            - playlists: List of matching playlists
            - total_count: Number of playlists found
            - message: Summary message
            - schema_resources: Links to schema information

            Each playlist includes:
            - All requested fields
            - sg_url: Primary URL (screening room)
            - sg_urls: All URL variants

            Example:
            {
                "playlists": [
                    {
                        "type": "Playlist",
                        "id": 456,
                        "code": "Dailies_2025-01-15",
                        "description": "Daily review",
                        "project": {"type": "Project", "id": 123, "name": "Demo"},
                        "created_at": "2025-01-15T10:00:00Z",
                        "versions": [
                            {"type": "Version", "id": 1001},
                            {"type": "Version", "id": 1002}
                        ],
                        "sg_url": "https://studio.shotgrid.autodesk.com/page/screening_room?playlist_id=456",
                        "sg_urls": {...}
                    },
                    ...
                ],
                "total_count": 5,
                "message": "Found 5 playlists",
                "schema_resources": {...}
            }

        Raises:
            ToolError: If filters are malformed or the find operation fails.

        Examples:
            Find all playlists in a project:
            {
                "filters": [["project", "is", {"type": "Project", "id": 123}]],
                "order": [{"field_name": "created_at", "direction": "desc"}],
                "limit": 20
            }

            Find playlists created last week:
            {
                "filters": [["created_at", "in_last", 7, "DAY"]],
                "fields": ["code", "description", "created_at", "versions"],
                "order": [{"field_name": "created_at", "direction": "desc"}]
            }

            Find playlists by name pattern:
            {
                "filters": [["code", "contains", "client_review"]],
                "fields": ["code", "description", "project"]
            }

            Find playlists with pagination:
            {
                "filters": [["project", "is", {"type": "Project", "id": 123}]],
                "page": 1,
                "page_size": 20,
                "order": [{"field_name": "created_at", "direction": "desc"}]
            }

        Common Filter Operators:
            - is, is_not: Exact match
            - contains, not_contains: Substring match
            - in_last, not_in_last: Time-based (e.g., last 7 days)
            - greater_than, less_than: Date/numeric comparison

        Note:
            - All playlists include screening room URLs for easy access
            - Default fields include versions and project information
            - Pagination is 1-based (page 1 is the first page)
            - Empty filters return all playlists (subject to limit)
            - Results are automatically enriched with ShotGrid URLs
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

        **When to use this tool:**
        - You know the project ID and want all playlists in that project
        - You want to find recent playlists in a specific project
        - You need a simple way to get project playlists without complex filters

        **When NOT to use this tool:**
        - To search across multiple projects - Use `find_playlists` instead
        - To find recent playlists across all projects - Use `find_recent_playlists` instead
        - To apply complex filtering - Use `find_playlists` instead

        **Common use cases:**
        - Get all playlists in project 123
        - Get playlists created in last 7 days in project 123
        - Get latest 10 playlists in a project

        Args:
            project_id: ID of project to find playlists for.
                       Must be a valid project ID.

                       Example: 123

            fields: Optional list of fields to return.
                   If not provided, returns default fields.

                   Example: ["code", "description", "versions"]

            days: Optional number of days to look back.
                 If provided, only returns playlists created in the last N days.

                 Example: 7 (last 7 days)

            limit: Optional limit on number of playlists to return.
                  Useful for getting just the most recent playlists.

                  Example: 10

        Returns:
            Dictionary containing:
            - playlists: List of playlists found
            - total_count: Number of playlists found
            - message: Summary message

        Raises:
            ToolError: If the find operation fails or project_id is invalid.

        Examples:
            Get all playlists in project 123:
            {
                "project_id": 123
            }

            Get playlists from last 7 days in project 123:
            {
                "project_id": 123,
                "days": 7,
                "limit": 20
            }
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

        **When to use this tool:**
        - You want to find playlists created recently (last N days)
        - You need a quick way to get recent playlists without complex filters
        - You want to see what playlists were created this week
        - You want to find recent playlists across all projects or in a specific project

        **When NOT to use this tool:**
        - To find playlists with complex criteria - Use `find_playlists` instead
        - To find all playlists in a project (not just recent) - Use `find_project_playlists` instead
        - To search by playlist name or other fields - Use `find_playlists` instead

        **Common use cases:**
        - Get playlists from last 7 days (default)
        - Get playlists from last 30 days in project 123
        - Get latest 10 playlists across all projects

        Args:
            days: Number of days to look back (default: 7).
                 Playlists created within this time period will be returned.

                 Examples:
                 - 7 (last week, default)
                 - 30 (last month)
                 - 1 (today)

            project_id: Optional project ID to filter playlists by.
                       If not provided, searches across all projects.

                       Example: 123

            limit: Optional limit on number of playlists to return (default: 20).
                  Useful for getting just the most recent playlists.

                  Example: 10

            fields: Optional list of fields to return.
                   If not provided, returns default fields.

                   Example: ["code", "description", "versions"]

        Returns:
            Dictionary containing:
            - playlists: List of recent playlists found (sorted newest first)
            - total_count: Number of playlists found
            - message: Summary message

        Raises:
            ToolError: If the find operation fails.

        Examples:
            Get playlists from last 7 days:
            {
                "days": 7
            }

            Get playlists from last 30 days in project 123:
            {
                "days": 30,
                "project_id": 123,
                "limit": 50
            }

            Get latest 10 playlists across all projects:
            {
                "days": 90,
                "limit": 10
            }
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
        """Create a playlist in ShotGrid for version review and approval.

        Use this tool to create a new playlist for organizing and reviewing versions.
        Playlists are used for dailies, client reviews, and approval sessions.

        Common use cases:
        - Create dailies playlist for daily review sessions
        - Organize versions for client review
        - Group versions for approval workflows
        - Create screening room sessions
        - Collect versions for specific milestones

        For finding existing playlists, use `find_playlists` or `find_recent_playlists`.
        For adding versions to existing playlists, use `add_versions_to_playlist`.

        Args:
            code: Name/code of the playlist.
                 This is the display name shown in ShotGrid.
                 Should be descriptive and unique within the project.

                 Examples:
                 - "Dailies_2025-01-15"
                 - "Client_Review_v1"
                 - "Final_Approval_Shots"
                 - "Animation_Review_Week_3"

            project_id: ID of the project to create the playlist in.
                       The playlist will be associated with this project.

                       Example: 123

            description: Optional description of the playlist.
                        Provides context about the playlist's purpose.

                        Examples:
                        - "Daily review for animation department"
                        - "Client review for Episode 1"
                        - "Final approval for all hero shots"

            versions: Optional list of versions to add to the playlist.
                     Each version should be a dictionary with type and id.
                     Versions can also be added later using `add_versions_to_playlist`.

                     Format:
                     [
                         {"type": "Version", "id": 1234},
                         {"type": "Version", "id": 1235},
                         ...
                     ]

                     Example:
                     [
                         {"type": "Version", "id": 1001},
                         {"type": "Version", "id": 1002},
                         {"type": "Version", "id": 1003}
                     ]

        Returns:
            Dictionary containing:
            - entity: The created playlist with all fields
            - entity_type: "Playlist"
            - sg_url: Primary URL to view the playlist (screening room)
            - sg_urls: All URL variants for accessing the playlist
            - schema_resources: Links to schema information

            Example:
            {
                "entity": {
                    "type": "Playlist",
                    "id": 456,
                    "code": "Dailies_2025-01-15",
                    "description": "Daily review for animation",
                    "project": {"type": "Project", "id": 123, "name": "Demo"},
                    "versions": [
                        {"type": "Version", "id": 1001},
                        {"type": "Version", "id": 1002}
                    ],
                    "sg_url": "https://studio.shotgrid.autodesk.com/page/screening_room?playlist_id=456",
                    "sg_urls": {
                        "screening_room": "https://...",
                        "detail": "https://...",
                        "versions_tab": "https://..."
                    }
                },
                "entity_type": "Playlist",
                "schema_resources": {...}
            }

        Raises:
            ToolError: If project_id is invalid or the create operation fails.

        Examples:
            Create empty playlist:
            {
                "code": "Dailies_2025-01-15",
                "project_id": 123,
                "description": "Daily review for animation department"
            }

            Create playlist with versions:
            {
                "code": "Client_Review_v1",
                "project_id": 123,
                "description": "First client review for Episode 1",
                "versions": [
                    {"type": "Version", "id": 1001},
                    {"type": "Version", "id": 1002},
                    {"type": "Version", "id": 1003}
                ]
            }

            Create approval playlist:
            {
                "code": "Final_Approval_Hero_Shots",
                "project_id": 123,
                "description": "Final approval for all hero character shots",
                "versions": [
                    {"type": "Version", "id": 2001},
                    {"type": "Version", "id": 2002}
                ]
            }

        Playlist URLs:
            The created playlist includes multiple URL variants:
            - screening_room: View in ShotGrid's screening room (recommended)
            - detail: View playlist detail page
            - versions_tab: View versions tab

            Use the screening_room URL for review sessions.

        Note:
            - Playlists are project-specific
            - Versions must belong to the same project as the playlist
            - Empty playlists can be created and populated later
            - Playlist code should be unique within the project
            - Created playlists are immediately available in ShotGrid
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

            from typing import cast

            # Serialize the entity
            serialized_entity = cast(EntityDict, serialize_entity(result))

            # Return structured result
            return PlaylistsResult(
                playlists=[serialized_entity],
                total_count=1,
                message="Playlist created successfully",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="create_playlist")
            raise  # This is needed to satisfy the type checker

    @server.tool("update_playlist")
    def update_playlist(
        playlist_id: int,
        code: Optional[str] = None,
        description: Optional[str] = None,
        versions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Update a playlist in ShotGrid.

        Args:
            playlist_id: ID of the playlist to update.
            code: Optional new code/name for the playlist.
            description: Optional new description for the playlist.
            versions: Optional new list of versions for the playlist.

        Returns:
            Dict[str, Any]: Updated playlist with schema resources.

        Raises:
            ToolError: If the update operation fails.
        """
        try:
            from typing import cast

            from shotgrid_mcp_server.response_models import EntityUpdateResult

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

            # Return structured result
            return EntityUpdateResult(
                entity=cast(EntityDict, serialize_entity(result)),
                entity_type="Playlist",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="update_playlist")
            raise  # This is needed to satisfy the type checker

    @server.tool("add_versions_to_playlist")
    def add_versions_to_playlist(
        playlist_id: int,
        version_ids: List[int],
    ) -> Dict[str, Any]:
        """Add versions to a playlist in ShotGrid.

        Args:
            playlist_id: ID of the playlist to update.
            version_ids: List of version IDs to add to the playlist.

        Returns:
            Dict[str, Any]: Updated playlist with schema resources.

        Raises:
            ToolError: If the update operation fails.
        """
        try:
            from typing import cast

            from shotgrid_mcp_server.response_models import EntityUpdateResult

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

            # If no new versions to add, return current playlist
            if not version_entities:
                return EntityUpdateResult(
                    entity=cast(EntityDict, serialize_entity(playlist)),
                    entity_type="Playlist",
                ).model_dump()

            # Update playlist with new versions
            all_versions = current_versions + version_entities
            result = sg.update("Playlist", playlist_id, {"versions": all_versions})
            if result is None:
                raise ValueError(f"Failed to update playlist with ID {playlist_id}")

            # Return structured result
            return EntityUpdateResult(
                entity=cast(EntityDict, serialize_entity(result)),
                entity_type="Playlist",
            ).model_dump()
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
