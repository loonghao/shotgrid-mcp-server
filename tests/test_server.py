"""Test module for ShotGrid MCP server.

This module contains unit tests for the ShotGrid MCP server tools.
"""

# Import built-in modules
import json
from pathlib import Path

# Import third-party modules
import pytest
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun


@pytest.mark.asyncio
class TestCreateTools:
    """Test suite for create tools."""

    async def test_create_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test creating a single entity."""
        # Create entity using MCP tool
        entity_type = "Shot"
        data = {"code": "new_shot", "project": mock_sg.find_one("Project", [["code", "is", "test"]])}

        await server.call_tool("create_entity", {"entity_type": entity_type, "data": data})

        # Verify entity was created
        created_shot = mock_sg.find_one(entity_type, [["code", "is", "new_shot"]])
        assert created_shot is not None
        assert created_shot["code"] == data["code"]
        assert created_shot["project"] == data["project"]

    async def test_batch_create_entities(self, server: FastMCP, mock_sg: Shotgun):
        """Test creating multiple entities."""
        # Setup test data
        entity_type = "Shot"
        project = mock_sg.find_one("Project", [["code", "is", "test"]])
        data_list = [{"code": "batch_shot_001", "project": project}, {"code": "batch_shot_002", "project": project}]

        # Create entities using MCP tool
        await server.call_tool("batch_create_entities", {"entity_type": entity_type, "data_list": data_list})

        # Verify entities were created
        entities = mock_sg.find("Shot", [["code", "in", ["batch_shot_001", "batch_shot_002"]]])
        assert len(entities) == 2


@pytest.mark.asyncio
class TestReadTools:
    """Test suite for read tools."""

    async def test_get_schema(self, server: FastMCP, mock_sg: Shotgun):
        """Test getting schema for a specific entity type."""
        entity_type = "Shot"

        # Get schema using MCP tool
        response = await server.call_tool("get_schema", {"entity_type": entity_type})
        response_dict = json.loads(response[0].text)

        # Verify schema
        assert response_dict is not None
        assert "fields" in response_dict
        assert "id" in response_dict["fields"]
        assert "type" in response_dict["fields"]
        assert "code" in response_dict["fields"]


@pytest.mark.asyncio
class TestUpdateTools:
    """Test suite for update tools."""

    async def test_update_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test updating a single entity."""
        # Find test shot
        shot = mock_sg.find_one("Shot", [["code", "is", "test_shot"]])
        assert shot is not None

        # Update entity using MCP tool
        new_code = "updated_shot"
        await server.call_tool(
            "update_entity", {"entity_type": "Shot", "entity_id": shot["id"], "data": {"code": new_code}}
        )

        # Verify update
        updated_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]])
        assert updated_shot is not None
        assert updated_shot["code"] == new_code


@pytest.mark.asyncio
class TestDeleteTools:
    """Test suite for delete tools."""

    async def test_delete_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test deleting a single entity."""
        # Create entity to delete
        project = mock_sg.find_one("Project", [["code", "is", "test"]])
        shot_to_delete = mock_sg.create("Shot", {"code": "shot_to_delete", "project": project})

        # Delete entity using MCP tool
        await server.call_tool("delete_entity", {"entity_type": "Shot", "entity_id": shot_to_delete["id"]})

        # Verify deletion
        deleted_shot = mock_sg.find_one("Shot", [["id", "is", shot_to_delete["id"]]])
        assert deleted_shot is None


@pytest.mark.asyncio
class TestDownloadTools:
    """Test suite for download tools."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for downloads."""
        return tmp_path

    async def test_download_thumbnail(self, server: FastMCP, mock_sg: Shotgun, temp_dir: Path):
        """Test downloading a thumbnail."""
        # Create test shot without attachment
        project = mock_sg.find_one("Project", [["code", "is", "main"]])
        shot = mock_sg.create(
            "Shot",
            {
                "code": "shot_with_thumbnail",
                "project": project,
                "sg_status_list": "ip",
                "description": "Test shot with thumbnail",
            },
        )

        # Add thumbnail directly to the entity
        mock_sg.update(
            "Shot",
            shot["id"],
            {"image": {"url": "https://example.com/thumbnail.jpg", "type": "Attachment"}},
        )

        # Download thumbnail using MCP tool
        file_path = temp_dir / "thumbnail.jpg"
        response = await server.call_tool(
            "download_thumbnail",
            {"entity_type": "Shot", "entity_id": shot["id"], "field_name": "image", "file_path": str(file_path)},
        )
        response_dict = json.loads(response[0].text)

        # Verify download
        assert response_dict == {"file_path": str(file_path)}

    async def test_download_thumbnail_not_found(self, server: FastMCP, mock_sg: Shotgun, temp_dir: Path):
        """Test downloading a non-existent thumbnail."""
        with pytest.raises(
            ToolError, match="Error executing tool download_thumbnail: Entity Shot with ID 999999 not found"
        ):
            await server.call_tool(
                "download_thumbnail",
                {
                    "entity_type": "Shot",
                    "entity_id": 999999,
                    "field_name": "image",
                    "file_path": str(temp_dir / "thumbnail.jpg"),
                },
            )


@pytest.mark.asyncio
class TestSearchTools:
    """Test suite for search tools."""

    async def test_find_entities(self, server: FastMCP, mock_sg: Shotgun):
        """Test finding entities."""
        # Find test project
        project = mock_sg.find_one("Project", [["code", "is", "test"]])

        # Search for shots in project
        response = await server.call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": [["project", "is", project]],
                "fields": ["code", "project"],
            },
        )
        response_dict = json.loads(response[0].text)
        assert isinstance(response_dict, dict)
        assert "entities" in json.loads(response_dict["text"])

        # Verify search results
        result_dict = json.loads(response_dict["text"])
        assert isinstance(result_dict["entities"], list)

    async def test_find_one_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test finding a single entity."""
        # Find test shot
        response = await server.call_tool(
            "find_one_entity",
            {
                "entity_type": "Shot",
                "filters": [["code", "is", "test_shot"]],
                "fields": ["code", "project"],
            },
        )

        # Verify response
        assert response is not None
        assert isinstance(response, list)
        assert len(response) == 1
        response_dict = json.loads(response[0].text)
        assert response_dict is not None
        assert "text" in response_dict
        response_entity = json.loads(response_dict["text"])
        assert "text" in response_entity
        assert "code" in response_entity["text"]
        assert response_entity["text"]["code"] == "test_shot"


@pytest.mark.asyncio
class TestGetThumbnailUrl:
    """Test suite for get_thumbnail_url method."""

    async def test_get_thumbnail_url(self, server: FastMCP, mock_sg: Shotgun):
        """Test get_thumbnail_url method."""
        # Create test shot with thumbnail
        project = mock_sg.find_one("Project", [["code", "is", "main"]])
        shot = mock_sg.create(
            "Shot",
            {
                "code": "shot_with_thumbnail",
                "project": project,
                "sg_status_list": "ip",
                "description": "Test shot with thumbnail",
            },
        )

        # Add thumbnail directly to the entity
        mock_sg.update(
            "Shot",
            shot["id"],
            {"image": {"url": "https://example.com/thumbnail.jpg", "type": "Attachment"}},
        )

        # Get thumbnail URL using MCP tool
        response = await server.call_tool(
            "get_thumbnail_url",
            {"entity_type": "Shot", "entity_id": shot["id"], "field_name": "image"},
        )
        url = response[0].text

        # Verify URL
        assert url == "https://example.com/thumbnail.jpg"

    async def test_get_thumbnail_url_not_found(self, server: FastMCP):
        """Test get_thumbnail_url method when no entity is found."""
        with pytest.raises(
            ToolError, match="Error executing tool get_thumbnail_url: Entity Shot with ID 999999 not found"
        ):
            await server.call_tool(
                "get_thumbnail_url",
                {"entity_type": "Shot", "entity_id": 999999, "field_name": "image"},
            )

    async def test_get_thumbnail_url_no_url(self, server: FastMCP, mock_sg: Shotgun):
        """Test get_thumbnail_url method when entity has no thumbnail URL."""
        # Create test shot without thumbnail
        project = mock_sg.find_one("Project", [["code", "is", "main"]])
        shot = mock_sg.create(
            "Shot",
            {
                "code": "shot_without_thumbnail",
                "project": project,
            },
        )

        with pytest.raises(ToolError, match="Error executing tool get_thumbnail_url: No thumbnail URL found"):
            await server.call_tool(
                "get_thumbnail_url",
                {"entity_type": "Shot", "entity_id": shot["id"], "field_name": "image"},
            )
