"""Tests for vendor tools."""

import json
import pytest
from fastmcp.exceptions import ToolError
from fastmcp.server import FastMCP
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.vendor_tools import register_vendor_tools


@pytest.fixture
def vendor_server(server: FastMCP, mock_sg: Shotgun):
    """Create a server with vendor tools registered."""
    register_vendor_tools(server, mock_sg)
    return server


class TestVendorTools:
    """Tests for vendor tools."""

    async def test_find_vendor_users(self, vendor_server: FastMCP, mock_sg: Shotgun):
        """Test finding vendor users."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )
        
        # Create a vendor group
        vendor_group = mock_sg.create(
            "Group",
            {
                "code": "Vendors",
            },
        )
        
        # Create a vendor user
        vendor_user = mock_sg.create(
            "HumanUser",
            {
                "login": "vendor_user",
                "name": "Vendor User",
                "email": "vendor@external-company.com",
                "sg_status_list": "act",
                "groups": [{"type": "Group", "id": vendor_group["id"]}],
            },
        )
        
        # Create a regular user
        regular_user = mock_sg.create(
            "HumanUser",
            {
                "login": "regular_user",
                "name": "Regular User",
                "email": "user@internal-company.com",
                "sg_status_list": "act",
            },
        )
        
        # Create versions for both users in the project
        vendor_version = mock_sg.create(
            "Version",
            {
                "project": {"type": "Project", "id": project["id"]},
                "code": "VENDOR_VERSION",
                "created_by": {"type": "HumanUser", "id": vendor_user["id"]},
            },
        )
        
        regular_version = mock_sg.create(
            "Version",
            {
                "project": {"type": "Project", "id": project["id"]},
                "code": "REGULAR_VERSION",
                "created_by": {"type": "HumanUser", "id": regular_user["id"]},
            },
        )
        
        # Test find_vendor_users
        result = await vendor_server.call_tool(
            "find_vendor_users",
            {
                "project_id": project["id"],
            },
        )
        
        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Parse JSON response
        data = json.loads(result[0]["text"])
        
        # Verify vendor user data
        assert "users" in data
        assert len(data["users"]) == 1
        assert data["users"][0]["id"] == vendor_user["id"]
        assert data["users"][0]["login"] == "vendor_user"

    async def test_find_vendor_versions(self, vendor_server: FastMCP, mock_sg: Shotgun):
        """Test finding vendor versions."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )
        
        # Create a vendor group
        vendor_group = mock_sg.create(
            "Group",
            {
                "code": "Vendors",
            },
        )
        
        # Create a vendor user
        vendor_user = mock_sg.create(
            "HumanUser",
            {
                "login": "vendor_user",
                "name": "Vendor User",
                "email": "vendor@external-company.com",
                "sg_status_list": "act",
                "groups": [{"type": "Group", "id": vendor_group["id"]}],
            },
        )
        
        # Create a regular user
        regular_user = mock_sg.create(
            "HumanUser",
            {
                "login": "regular_user",
                "name": "Regular User",
                "email": "user@internal-company.com",
                "sg_status_list": "act",
            },
        )
        
        # Create versions for both users in the project
        vendor_version = mock_sg.create(
            "Version",
            {
                "project": {"type": "Project", "id": project["id"]},
                "code": "VENDOR_VERSION",
                "created_by": {"type": "HumanUser", "id": vendor_user["id"]},
            },
        )
        
        regular_version = mock_sg.create(
            "Version",
            {
                "project": {"type": "Project", "id": project["id"]},
                "code": "REGULAR_VERSION",
                "created_by": {"type": "HumanUser", "id": regular_user["id"]},
            },
        )
        
        # Test find_vendor_versions
        result = await vendor_server.call_tool(
            "find_vendor_versions",
            {
                "project_id": project["id"],
            },
        )
        
        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Parse JSON response
        data = json.loads(result[0]["text"])
        
        # Verify vendor version data
        assert "versions" in data
        assert len(data["versions"]) == 1
        assert data["versions"][0]["id"] == vendor_version["id"]
        assert data["versions"][0]["code"] == "VENDOR_VERSION"

    async def test_create_vendor_playlist(self, vendor_server: FastMCP, mock_sg: Shotgun):
        """Test creating a vendor playlist."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )
        
        # Create a vendor group
        vendor_group = mock_sg.create(
            "Group",
            {
                "code": "Vendors",
            },
        )
        
        # Create a vendor user
        vendor_user = mock_sg.create(
            "HumanUser",
            {
                "login": "vendor_user",
                "name": "Vendor User",
                "email": "vendor@external-company.com",
                "sg_status_list": "act",
                "groups": [{"type": "Group", "id": vendor_group["id"]}],
            },
        )
        
        # Create versions for the vendor user
        for i in range(3):
            mock_sg.create(
                "Version",
                {
                    "project": {"type": "Project", "id": project["id"]},
                    "code": f"VENDOR_VERSION_{i}",
                    "created_by": {"type": "HumanUser", "id": vendor_user["id"]},
                },
            )
        
        # Test create_vendor_playlist
        result = await vendor_server.call_tool(
            "create_vendor_playlist",
            {
                "project_id": project["id"],
                "playlist_name": "Test Vendor Playlist",
                "playlist_description": "Test playlist with vendor versions",
            },
        )
        
        # Verify result
        assert result
        assert isinstance(result, dict)
        assert "id" in result
        assert result["code"] == "Test Vendor Playlist"
        assert result["description"] == "Test playlist with vendor versions"
        assert "sg_url" in result
        assert "versions" in result
        assert len(result["versions"]) == 3
