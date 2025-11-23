"""Vendor tools for ShotGrid MCP server.

This module contains tools for working with vendor (external) users and their versions in ShotGrid.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

# Import MCP-specific models
from shotgrid_mcp_server.models import (
    create_in_last_filter,
)
from shotgrid_mcp_server.response_models import (
    PlaylistsResult,
    VendorUsersResult,
    VendorVersionsResult,
    generate_playlist_url,
)
from shotgrid_mcp_server.tools.base import handle_error, serialize_entity
from shotgrid_mcp_server.tools.types import EntityDict, FastMCPType

# Configure logging
logger = logging.getLogger(__name__)


def _get_default_user_fields() -> List[str]:
    """Get default fields for user queries.

    Returns:
        List[str]: Default fields to retrieve for users.
    """
    return ["id", "name", "login", "email", "groups", "sg_status_list", "sg_vendor"]


def _get_default_version_fields() -> List[str]:
    """Get default fields for version queries.

    Returns:
        List[str]: Default fields to retrieve for versions.
    """
    return [
        "id",
        "code",
        "description",
        "created_at",
        "updated_at",
        "user",
        "created_by",
        "entity",
        "project",
        "sg_status_list",
        "sg_path_to_movie",
        "sg_path_to_frames",
    ]


def _serialize_users_response(users: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Serialize users to JSON response using Pydantic model.

    Args:
        users: List of users to serialize.

    Returns:
        Dict[str, Any]: Serialized users response with schema resources.
    """
    from typing import cast

    # Serialize each user
    serialized_users = [cast(EntityDict, serialize_entity(user)) for user in users]

    # Return structured result
    return VendorUsersResult(
        users=serialized_users,
        total_count=len(serialized_users),
        message=f"Found {len(serialized_users)} vendor users",
    ).model_dump()


def _serialize_versions_response(versions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Serialize versions to JSON response using Pydantic model.

    Args:
        versions: List of versions to serialize.

    Returns:
        Dict[str, Any]: Serialized versions response with schema resources.
    """
    from typing import cast

    # Serialize each version
    serialized_versions = [cast(EntityDict, serialize_entity(version)) for version in versions]

    # Return structured result
    return VendorVersionsResult(
        versions=serialized_versions,
        total_count=len(serialized_versions),
        message=f"Found {len(serialized_versions)} vendor versions",
    ).model_dump()


def _is_vendor_user(user: Dict[str, Any]) -> bool:
    """Check if a user is a vendor (external) user.

    Args:
        user: User data.

    Returns:
        bool: True if the user is a vendor, False otherwise.
    """
    # Check for sg_vendor field if it exists
    if "sg_vendor" in user and user["sg_vendor"]:
        return True

    # Check for group membership if groups field exists
    if "groups" in user and user["groups"]:
        for group in user["groups"]:
            if isinstance(group, dict) and "name" in group:
                group_name = group["name"].lower()
                if "vendor" in group_name or "external" in group_name:
                    return True

    # Check for email domain if email field exists
    if "email" in user and user["email"]:
        email = user["email"].lower()
        # List of common vendor domains (customize as needed)
        vendor_domains = ["@vendor.", "@external.", "@freelance.", "@contractor."]
        for domain in vendor_domains:
            if domain in email:
                return True

    return False


def register_vendor_tools(server: FastMCPType, sg: Shotgun) -> None:  # noqa: C901
    """Register vendor tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    @server.tool("find_vendor_users")
    def find_vendor_users(
        project_id: Optional[int] = None,
        fields: Optional[List[str]] = None,
        active_only: bool = True,
    ) -> Dict[str, Any]:
        """Find vendor (external) users in ShotGrid.

        **When to use this tool:**
        - You need to find external/vendor users in the system
        - You want to see which vendors are working on a project
        - You need to get contact information for vendor users
        - You want to filter vendor users by active status

        **When NOT to use this tool:**
        - To find internal users - Use `search_entities` with entity_type="HumanUser" instead
        - To find all users (internal + vendor) - Use `search_entities` instead
        - To find vendor versions - Use `find_vendor_versions` instead

        **Common use cases:**
        - Get all active vendor users
        - Get vendor users working on project 123
        - Get vendor user contact information (email, login)

        Args:
            project_id: Optional project ID to filter vendor users by.
                       If provided, only returns vendors associated with this project.

                       Example: 123

            fields: Optional list of fields to return.
                   If not provided, returns default fields:
                   ["id", "name", "login", "email", "groups", "sg_status_list", "sg_vendor"]

                   Example: ["name", "email", "login"]

            active_only: Whether to return only active users (default: True).
                        If False, returns all vendor users including inactive ones.

                        Example: True

        Returns:
            Dictionary containing:
            - users: List of vendor users found
            - total_count: Number of vendor users found
            - message: Summary message

        Raises:
            ToolError: If the find operation fails.

        Examples:
            Get all active vendor users:
            {
                "active_only": true
            }

            Get vendor users in project 123:
            {
                "project_id": 123,
                "active_only": true
            }

        Note:
            - Vendor users are identified by sg_vendor field, group membership, or email domain
            - Default fields include vendor-specific information
            - Results are sorted by name
        """
        """Find vendor (external) users in ShotGrid.

        Args:
            project_id: Optional project ID to filter users by.
            fields: Optional list of fields to return.
            active_only: Whether to only return active users (default: True).

        Returns:
            List[Dict[str, str]]: List of vendor users found.

        Raises:
            ToolError: If the find operation fails.
        """
        try:
            # Default fields if none provided
            if fields is None:
                fields = _get_default_user_fields()

            # Build filters
            filters = []

            # Add project filter if provided
            if project_id:
                # For users, we need to find users who have worked on the project
                # This is a complex query that might need customization based on your ShotGrid setup
                # Here's a simplified version that looks for users who have created versions in the project
                version_filters = [["project", "is", {"type": "Project", "id": project_id}]]
                versions = sg.find("Version", version_filters, ["created_by"])
                user_ids = list({v["created_by"]["id"] for v in versions if "created_by" in v})

                if user_ids:
                    filters.append(["id", "in", user_ids])
                else:
                    # No users found for this project
                    return _serialize_users_response([])

            # Add active filter if requested
            if active_only:
                filters.append(["sg_status_list", "is", "act"])

            # Execute query
            all_users = sg.find("HumanUser", filters, fields)

            # Filter vendor users
            vendor_users = [user for user in all_users if _is_vendor_user(user)]

            # Serialize and return results
            return _serialize_users_response(vendor_users)
        except Exception as err:
            handle_error(err, operation="find_vendor_users")
            raise  # This is needed to satisfy the type checker

    @server.tool("find_vendor_versions")
    def find_vendor_versions(  # noqa: C901
        project_id: int,
        vendor_user_ids: Optional[List[int]] = None,
        days: Optional[int] = None,
        status: Optional[str] = None,
        entity_type: Optional[str] = None,
        entity_id: Optional[int] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Find versions created by vendor users in ShotGrid.

        **When to use this tool:**
        - You need to find versions submitted by external/vendor users
        - You want to review vendor deliverables in a project
        - You need to track vendor work progress
        - You want to filter vendor versions by status or date range

        **When NOT to use this tool:**
        - To find all versions (internal + vendor) - Use `search_entities` with entity_type="Version" instead
        - To find vendor users - Use `find_vendor_users` instead
        - To find versions by specific criteria (not vendor-related) - Use `search_entities` instead

        **Common use cases:**
        - Get all vendor versions in project 123
        - Get vendor versions from last 7 days
        - Get vendor versions with status "rev" (in review)
        - Get vendor versions for a specific shot or asset

        Args:
            project_id: Project ID to filter versions by.
                       Required - all versions must belong to a project.

                       Example: 123

            vendor_user_ids: Optional list of vendor user IDs.
                            If not provided, finds versions from all vendor users in the project.
                            If provided, only finds versions from these specific vendor users.

                            Example: [42, 43, 44]

            days: Optional number of days to look back.
                 If provided, only returns versions created in the last N days.

                 Example: 7 (last 7 days)

            status: Optional status to filter versions by.
                   Common statuses: "rev" (review), "apr" (approved), "ip" (in progress)

                   Example: "rev"

            entity_type: Optional entity type to filter versions by.
                        Use with entity_id to find versions for a specific entity.

                        Example: "Shot"

            entity_id: Optional entity ID to filter versions by.
                      Use with entity_type to find versions for a specific entity.

                      Example: 1234

            fields: Optional list of fields to return.
                   If not provided, returns default fields:
                   ["id", "code", "description", "created_at", "updated_at", "user",
                    "created_by", "entity", "project", "sg_status_list",
                    "sg_path_to_movie", "sg_path_to_frames"]

                   Example: ["code", "sg_status_list", "created_at"]

            limit: Optional limit on number of versions to return.
                  Useful for getting just the most recent vendor versions.

                  Example: 50

        Returns:
            Dictionary containing:
            - versions: List of vendor versions found (sorted newest first)
            - total_count: Number of vendor versions found
            - message: Summary message

        Raises:
            ToolError: If the find operation fails or project_id is invalid.

        Examples:
            Get all vendor versions in project 123:
            {
                "project_id": 123
            }

            Get vendor versions from last 7 days with status "rev":
            {
                "project_id": 123,
                "days": 7,
                "status": "rev",
                "limit": 50
            }

            Get vendor versions for a specific shot:
            {
                "project_id": 123,
                "entity_type": "Shot",
                "entity_id": 1234
            }

            Get versions from specific vendor users:
            {
                "project_id": 123,
                "vendor_user_ids": [42, 43],
                "days": 30
            }

        Note:
            - If vendor_user_ids is not provided, automatically finds all vendor users in the project
            - Results are sorted by creation date (newest first)
            - Vendor users are identified by sg_vendor field, group membership, or email domain
        """
        try:
            # Default fields if none provided
            if fields is None:
                fields = _get_default_version_fields()

            # Build filters
            filters = [["project", "is", {"type": "Project", "id": project_id}]]

            # Add user filter if provided
            if vendor_user_ids:
                user_filter = []
                for user_id in vendor_user_ids:
                    user_filter.append(["created_by.id", "is", user_id])

                if len(user_filter) == 1:
                    filters.append(user_filter[0])
                else:
                    filters.append(["or"] + user_filter)
            else:
                # If no specific vendor users provided, find all vendor users first
                vendor_users_result = find_vendor_users(project_id)
                # Parse the response if it's a string, otherwise use it directly
                if isinstance(vendor_users_result, str):
                    vendor_users_result = json.loads(vendor_users_result)

                # Get vendor users from the response
                vendor_users = vendor_users_result.get("data", [])

                if vendor_users:
                    vendor_user_ids = [user["id"] for user in vendor_users]
                    user_filter = []
                    for user_id in vendor_user_ids:
                        user_filter.append(["created_by.id", "is", user_id])

                    if len(user_filter) == 1:
                        filters.append(user_filter[0])
                    else:
                        filters.append(["or"] + user_filter)
                else:
                    # No vendor users found
                    return _serialize_versions_response([])

            # Add date filter if days provided
            if days:
                date_filter = create_in_last_filter("created_at", days, "DAY")
                filters.append(date_filter.to_tuple())

            # Add status filter if provided
            if status:
                filters.append(["sg_status_list", "is", status])

            # Add entity filter if provided
            if entity_type and entity_id:
                filters.append(["entity", "is", {"type": entity_type, "id": entity_id}])

            # Order by creation date, newest first
            order = [{"field_name": "created_at", "direction": "desc"}]

            # Execute query
            result = sg.find(
                "Version",
                filters,
                fields=fields,
                order=order,
                limit=limit,
            )

            # Serialize and return results
            return _serialize_versions_response(result)
        except Exception as err:
            handle_error(err, operation="find_vendor_versions")
            raise  # This is needed to satisfy the type checker

    @server.tool("create_vendor_playlist")
    def create_vendor_playlist(
        project_id: int,
        vendor_user_ids: Optional[List[int]] = None,
        days: Optional[int] = 7,
        status: Optional[str] = None,
        playlist_name: Optional[str] = None,
        playlist_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a playlist with versions from vendor users.

        Args:
            project_id: Project ID to filter versions by.
            vendor_user_ids: Optional list of vendor user IDs. If not provided, all vendor users will be considered.
            days: Optional number of days to look back (default: 7).
            status: Optional status to filter versions by.
            playlist_name: Optional name for the playlist. If not provided, a default name will be generated.
            playlist_description: Optional description for the playlist.

        Returns:
            List[Dict[str, str]]: Serialized response containing the created playlist with URL.

        Raises:
            ToolError: If the create operation fails.
        """
        try:
            # Find vendor versions
            versions_result = find_vendor_versions(
                project_id=project_id, vendor_user_ids=vendor_user_ids, days=days, status=status, fields=["id"]
            )

            # Parse the response if it's a string, otherwise use it directly
            if isinstance(versions_result, str):
                versions_result = json.loads(versions_result)

            # Get versions from the response
            versions = versions_result.get("data", [])

            if not versions:
                raise ValueError("No vendor versions found for the specified criteria")

            # Generate playlist name if not provided
            if not playlist_name:
                import datetime

                today = datetime.datetime.now().strftime("%Y-%m-%d")
                playlist_name = f"Vendor Versions - {today}"

            # Generate playlist description if not provided
            if not playlist_description:
                vendor_count = len({v["created_by"]["id"] for v in versions if "created_by" in v})
                version_count = len(versions)
                playlist_description = f"Automatically generated playlist containing {version_count} versions from {vendor_count} vendor users."

            # Prepare version entities for playlist
            version_entities = [{"type": "Version", "id": v["id"]} for v in versions]

            # Create playlist
            data = {
                "code": playlist_name,
                "description": playlist_description,
                "project": {"type": "Project", "id": project_id},
                "versions": version_entities,
            }

            result = sg.create("Playlist", data)
            if result is None:
                raise ValueError("Failed to create playlist")

            from typing import cast

            # Generate playlist URL
            playlist_url = generate_playlist_url(sg.base_url, result["id"])
            result["sg_url"] = playlist_url

            # Serialize the entity
            serialized_entity = cast(EntityDict, serialize_entity(result))

            # Return structured result
            return PlaylistsResult(
                playlists=[serialized_entity],
                total_count=1,
                message="Vendor playlist created successfully",
            ).model_dump()
        except Exception as err:
            handle_error(err, operation="create_vendor_playlist")
            raise  # This is needed to satisfy the type checker
