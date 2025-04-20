"""Tests for playlist tools."""

import json
import datetime
import pytest
import pytest_asyncio
from fastmcp import FastMCP
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.playlist_tools import register_playlist_tools


@pytest_asyncio.fixture
async def playlist_server(server: FastMCP, mock_sg: Shotgun):
    """Create a server with playlist tools registered."""
    register_playlist_tools(server, mock_sg)
    return server


class TestPlaylistTools:
    """Tests for playlist tools."""

    @pytest.mark.asyncio
    async def test_find_playlists(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test finding playlists."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )

        # Create a test user
        user = mock_sg.create(
            "HumanUser",
            {
                "login": "test_user",
                "name": "Test User",
                "email": "test@example.com",
                "sg_status_list": "act",
            },
        )

        # Create test playlists
        playlist1 = mock_sg.create(
            "Playlist",
            {
                "code": "Test Playlist 1",
                "description": "Test playlist 1 description",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
                "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            },
        )

        playlist2 = mock_sg.create(
            "Playlist",
            {
                "code": "Test Playlist 2",
                "description": "Test playlist 2 description",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime(2025, 1, 2, 12, 0, 0),
                "updated_at": datetime.datetime(2025, 1, 2, 12, 0, 0),
            },
        )

        # Create a mock response for testing
        result = {
            "data": [
                {
                    "id": playlist1["id"],
                    "code": "Test Playlist 1",
                    "description": "Test playlist 1 description",
                    "sg_url": f"https://example.shotgunstudio.com/Playlist/detail/{playlist1['id']}",
                },
                {
                    "id": playlist2["id"],
                    "code": "Test Playlist 2",
                    "description": "Test playlist 2 description",
                    "sg_url": f"https://example.shotgunstudio.com/Playlist/detail/{playlist2['id']}",
                }
            ],
            "metadata": {
                "status": "success",
                "message": "Found 2 playlists"
            },
            "total_count": 2
        }

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Parse the JSON response
        response_text = result[0].text
        response_dict = json.loads(response_text)

        # Verify the parsed response
        assert "data" in response_dict
        assert len(response_dict["data"]) == 2

    @pytest.mark.asyncio
    async def test_find_project_playlists(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test finding playlists in a project."""
        # Create test projects
        project1 = mock_sg.create(
            "Project",
            {
                "name": "Test Project 1",
                "sg_status": "Active",
            },
        )

        project2 = mock_sg.create(
            "Project",
            {
                "name": "Test Project 2",
                "sg_status": "Active",
            },
        )

        # Create a test user
        user = mock_sg.create(
            "HumanUser",
            {
                "login": "test_user",
                "name": "Test User",
                "email": "test@example.com",
                "sg_status_list": "act",
            },
        )

        # Create test playlists in different projects
        playlist1 = mock_sg.create(
            "Playlist",
            {
                "code": "Project 1 Playlist",
                "description": "Project 1 playlist description",
                "project": {"type": "Project", "id": project1["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
                "updated_at": datetime.datetime(2025, 1, 1, 12, 0, 0),
            },
        )

        playlist2 = mock_sg.create(
            "Playlist",
            {
                "code": "Project 2 Playlist",
                "description": "Project 2 playlist description",
                "project": {"type": "Project", "id": project2["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime(2025, 1, 2, 12, 0, 0),
                "updated_at": datetime.datetime(2025, 1, 2, 12, 0, 0),
            },
        )

        # Create a mock response for testing
        result = {
            "data": [
                {
                    "id": playlist1["id"],
                    "code": "Project 1 Playlist",
                    "description": "Project 1 playlist description",
                    "sg_url": f"https://example.shotgunstudio.com/Playlist/detail/{playlist1['id']}",
                }
            ],
            "metadata": {
                "status": "success",
                "message": "Found 1 playlists"
            },
            "total_count": 1
        }

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Parse the JSON response
        response_text = result[0].text
        response_dict = json.loads(response_text)

        # Verify the parsed response
        assert "data" in response_dict
        assert len(response_dict["data"]) == 1
        assert response_dict["data"][0]["code"] == "Project 1 Playlist"

    @pytest.mark.asyncio
    async def test_find_recent_playlists(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test finding recent playlists."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )

        # Create a test user
        user = mock_sg.create(
            "HumanUser",
            {
                "login": "test_user",
                "name": "Test User",
                "email": "test@example.com",
                "sg_status_list": "act",
            },
        )

        # Create test playlists with different dates
        old_playlist = mock_sg.create(
            "Playlist",
            {
                "code": "Old Playlist",
                "description": "Old playlist description",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime(2024, 1, 1, 12, 0, 0),  # Old date
                "updated_at": datetime.datetime(2024, 1, 1, 12, 0, 0),
            },
        )

        recent_playlist = mock_sg.create(
            "Playlist",
            {
                "code": "Recent Playlist",
                "description": "Recent playlist description",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime.now(),  # Current date
                "updated_at": datetime.datetime.now(),
            },
        )

        # Create a mock response for testing
        result = {
            "data": [
                {
                    "id": recent_playlist["id"],
                    "code": "Recent Playlist",
                    "description": "Recent playlist description",
                    "sg_url": f"https://example.shotgunstudio.com/Playlist/detail/{recent_playlist['id']}",
                }
            ],
            "metadata": {
                "status": "success",
                "message": "Found 1 playlists"
            },
            "total_count": 1
        }

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Parse the JSON response
        response_text = result[0].text
        response_dict = json.loads(response_text)

        # Verify the parsed response
        assert "data" in response_dict
        assert len(response_dict["data"]) == 1
        assert response_dict["data"][0]["code"] == "Recent Playlist"

    @pytest.mark.asyncio
    async def test_create_playlist(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test creating a playlist."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )

        # Create a test version
        version = mock_sg.create(
            "Version",
            {
                "code": "Test Version",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create a mock response for testing
        result = {
            "data": {
                "id": 123,
                "code": "New Playlist",
                "description": "New playlist description",
                "sg_url": "https://example.shotgunstudio.com/Playlist/detail/123",
                "versions": [
                    {"id": version["id"], "code": "Test Version"}
                ]
            },
            "metadata": {
                "status": "success",
                "message": "Playlist created successfully"
            },
            "url": "https://example.shotgunstudio.com/Playlist/detail/123"
        }

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Parse the JSON response
        response_text = result[0].text
        response_dict = json.loads(response_text)

        # Verify the parsed response
        assert "data" in response_dict
        assert response_dict["data"]["code"] == "New Playlist"
        assert response_dict["data"]["description"] == "New playlist description"
        assert "sg_url" in response_dict["data"]
        assert "versions" in response_dict["data"]
        assert len(response_dict["data"]["versions"]) == 1

    @pytest.mark.asyncio
    async def test_update_playlist(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test updating a playlist."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )

        # Create a test playlist
        playlist = mock_sg.create(
            "Playlist",
            {
                "code": "Original Playlist",
                "description": "Original description",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Update the playlist directly
        mock_sg.update(
            "Playlist",
            playlist["id"],
            {
                "code": "Updated Playlist",
                "description": "Updated description",
            }
        )

        # Verify the update
        updated_playlist = mock_sg.find_one(
            "Playlist",
            [["id", "is", playlist["id"]]],
            ["code", "description"]
        )
        assert updated_playlist["code"] == "Updated Playlist"
        assert updated_playlist["description"] == "Updated description"

    @pytest.mark.asyncio
    async def test_add_versions_to_playlist(self, playlist_server: FastMCP, mock_sg: Shotgun):
        """Test adding versions to a playlist."""
        # Create a test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "sg_status": "Active",
            },
        )

        # Create test versions
        version1 = mock_sg.create(
            "Version",
            {
                "code": "Version 1",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        version2 = mock_sg.create(
            "Version",
            {
                "code": "Version 2",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create a test playlist with one version
        playlist = mock_sg.create(
            "Playlist",
            {
                "code": "Test Playlist",
                "description": "Test description",
                "project": {"type": "Project", "id": project["id"]},
                "versions": [{"type": "Version", "id": version1["id"]}],
            },
        )

        # Add the second version to the playlist
        mock_sg.update(
            "Playlist",
            playlist["id"],
            {
                "versions": [
                    {"type": "Version", "id": version1["id"]},
                    {"type": "Version", "id": version2["id"]}
                ]
            }
        )

        # Verify the update
        updated_playlist = mock_sg.find_one(
            "Playlist",
            [["id", "is", playlist["id"]]],
            ["versions"]
        )
        assert len(updated_playlist["versions"]) == 2
        version_ids = [v["id"] for v in updated_playlist["versions"]]
        assert version1["id"] in version_ids
        assert version2["id"] in version_ids
