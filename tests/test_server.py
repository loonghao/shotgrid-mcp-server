"""Test module for ShotGrid MCP server.

This module contains unit tests for the ShotGrid MCP server tools.
"""

# Import built-in modules
import os
from pathlib import Path
from unittest.mock import patch

# Import third-party modules
import pytest
from fastmcp import FastMCP
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.server import ShotGridTools


@pytest.fixture(scope="session")
def schema_dir():
    """Get schema directory."""
    data_dir = Path(__file__).parent / "data"
    schema_dir = data_dir / "schema"
    entity_schema_dir = data_dir / "entity_schema"

    # Set schema paths
    Shotgun.set_schema_paths(str(schema_dir), str(entity_schema_dir))

    yield schema_dir


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables required by the server."""
    with patch.dict(
        os.environ,
        {
            "SHOTGRID_URL": "https://example.shotgrid.autodesk.com",
            "SCRIPT_NAME": "test_script",
            "SCRIPT_KEY": "test_key",
        },
    ):
        yield


@pytest.fixture
def mock_sg(schema_dir):
    """Create a mock ShotGrid client using Mockgun."""
    with patch("shotgrid_mcp_server.server.ShotGridConnectionContext") as mock_context:
        mockgun_client = Shotgun("https://example.shotgrid.autodesk.com", "test_script", "test_key")

        # Create test project
        project = mockgun_client.create("Project", {"name": "Test Project", "code": "test"})

        # Create test sequence
        sequence = mockgun_client.create("Sequence", {"project": project, "code": "test_seq"})

        # Create test shot
        shot = mockgun_client.create(
            "Shot",
            {
                "project": project,
                "code": "test_shot",
                "sg_sequence": sequence,
            },
        )

        # Create test asset
        asset = mockgun_client.create("Asset", {"project": project, "code": "test_asset"})

        mock_context.return_value.__enter__.return_value = mockgun_client
        yield mockgun_client


@pytest.fixture
def server():
    """Create a FastMCP server instance."""
    server = FastMCP(name="test-server")
    ShotGridTools.create_tool(server)
    ShotGridTools.read_tool(server)
    ShotGridTools.update_tool(server)
    ShotGridTools.delete_tool(server)
    ShotGridTools.download_tool(server)
    ShotGridTools.schema_tool(server)
    return server


class TestCreateTools:
    """Test suite for create tools."""

    def test_create_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test creating a single entity."""
        # Create entity using MCP tool
        entity_type = "Shot"
        data = {"code": "new_shot", "project": mock_sg.find_one("Project", [["code", "is", "test"]])}

        response = server.call_tool("shotgrid.create", {"entity_type": entity_type, "data": data})

        # Verify entity was created
        created_shot = mock_sg.find_one(entity_type, [["code", "is", "new_shot"]])
        assert created_shot is not None
        assert created_shot["code"] == data["code"]
        assert created_shot["project"] == data["project"]

    def test_batch_create_entities(self, server: FastMCP, mock_sg: Shotgun):
        """Test creating multiple entities."""
        # Setup test data
        entity_type = "Shot"
        project = mock_sg.find_one("Project", [["code", "is", "test"]])
        data_list = [{"code": "batch_shot_001", "project": project}, {"code": "batch_shot_002", "project": project}]

        # Create entities using MCP tool
        response = server.call_tool("shotgrid.batch_create", {"entity_type": entity_type, "data_list": data_list})

        # Verify entities were created
        for data in data_list:
            shot = mock_sg.find_one(entity_type, [["code", "is", data["code"]]])
            assert shot is not None
            assert shot["code"] == data["code"]
            assert shot["project"] == data["project"]


class TestReadTools:
    """Test suite for read tools."""

    def test_get_schema(self, server: FastMCP, mock_sg: Shotgun):
        """Test getting schema for a specific entity type."""
        entity_type = "Shot"

        # Get schema using MCP tool
        response = server.call_tool("shotgrid.schema", {"entity_type": entity_type})

        # Verify schema
        assert response is not None
        assert "fields" in response
        assert "id" in response["fields"]
        assert "type" in response["fields"]
        assert "code" in response["fields"]


class TestUpdateTools:
    """Test suite for update tools."""

    def test_update_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test updating a single entity."""
        # Find test shot
        shot = mock_sg.find_one("Shot", [["code", "is", "test_shot"]])
        assert shot is not None

        # Update entity using MCP tool
        new_code = "updated_shot"
        response = server.call_tool(
            "shotgrid.update", {"entity_type": "Shot", "entity_id": shot["id"], "data": {"code": new_code}}
        )

        # Verify update
        updated_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]])
        assert updated_shot is not None
        assert updated_shot["code"] == new_code


class TestDeleteTools:
    """Test suite for delete tools."""

    def test_delete_entity(self, server: FastMCP, mock_sg: Shotgun):
        """Test deleting a single entity."""
        # Create entity to delete
        project = mock_sg.find_one("Project", [["code", "is", "test"]])
        shot_to_delete = mock_sg.create("Shot", {"code": "shot_to_delete", "project": project})

        # Delete entity using MCP tool
        server.call_tool("shotgrid.delete", {"entity_type": "Shot", "entity_id": shot_to_delete["id"]})

        # Verify deletion
        deleted_shot = mock_sg.find_one("Shot", [["id", "is", shot_to_delete["id"]]])
        assert deleted_shot is None


class TestDownloadTools:
    """Test suite for download tools."""

    @pytest.fixture
    def temp_dir(self, tmp_path):
        """Create a temporary directory for downloads."""
        return tmp_path

    def test_download_thumbnail(self, server: FastMCP, mock_sg: Shotgun, temp_dir: Path):
        """Test downloading a thumbnail."""
        # Create test shot with image
        project = mock_sg.find_one("Project", [["code", "is", "test"]])
        shot = mock_sg.create(
            "Shot",
            {"code": "shot_with_thumbnail", "project": project, "image": {"url": "https://example.com/thumbnail.jpg"}},
        )

        # Download thumbnail using MCP tool
        file_path = temp_dir / "thumbnail.jpg"
        response = server.call_tool(
            "shotgrid.download_thumbnail",
            {"entity_type": "Shot", "entity_id": shot["id"], "field_name": "image", "file_path": str(file_path)},
        )

        # Verify download
        assert response == {"file_path": str(file_path)}
        assert file_path.exists()

    def test_download_thumbnail_not_found(self, server: FastMCP, mock_sg: Shotgun, temp_dir: Path):
        """Test downloading a non-existent thumbnail."""
        file_path = temp_dir / "thumbnail.jpg"

        # Try to download non-existent thumbnail
        with pytest.raises(ValueError, match="Entity not found"):
            server.call_tool(
                "shotgrid.download_thumbnail",
                {
                    "entity_type": "Shot",
                    "entity_id": 999999,  # Non-existent ID
                    "field_name": "image",
                    "file_path": str(file_path),
                },
            )

        assert not file_path.exists()


class TestGetThumbnailUrl:
    """Test suite for get_thumbnail_url method."""

    @pytest.fixture
    def mock_shotgun(self, schema_dir):
        """Create a mock Shotgun instance."""
        return Shotgun("https://example.shotgrid.autodesk.com", "test_script", "test_key")

    @pytest.fixture
    def tools(self, mock_shotgun):
        """Create a ShotGridTools instance with a mock Shotgun connection."""
        with patch(
            "shotgrid_mcp_server.connection_pool.ShotGridConnectionPool._create_connection", return_value=mock_shotgun
        ):
            tools = ShotGridTools()
            tools.sg = mock_shotgun
            return tools

    def test_get_thumbnail_url(self, tools, mock_shotgun):
        """Test get_thumbnail_url method."""
        # Create test shot with image
        project = mock_shotgun.create("Project", {"name": "Test Project", "code": "test"})
        shot = mock_shotgun.create(
            "Shot", {"code": "shot_with_url", "project": project, "image": {"url": "https://example.com/thumbnail.jpg"}}
        )

        # Get thumbnail URL
        url = tools.get_thumbnail_url("Shot", shot["id"], "image")
        assert url == shot["image"]["url"]

    def test_get_thumbnail_url_no_result(self, tools):
        """Test get_thumbnail_url method when no entity is found."""
        with pytest.raises(ValueError, match="Entity not found"):
            tools.get_thumbnail_url("Shot", 999999, "image")

    def test_get_thumbnail_url_no_url(self, tools, mock_shotgun):
        """Test get_thumbnail_url method when entity has no thumbnail URL."""
        # Create test shot without image
        project = mock_shotgun.create("Project", {"name": "Test Project", "code": "test"})
        shot = mock_shotgun.create("Shot", {"code": "shot_without_url", "project": project})

        with pytest.raises(ValueError, match="No thumbnail URL found"):
            tools.get_thumbnail_url("Shot", shot["id"], "image")
