"""Tests for api_tools module."""

import pytest
import pytest_asyncio
from fastmcp import FastMCP
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.api_tools import register_api_tools


class TestAPITools:
    """Tests for API tools."""

    @pytest_asyncio.fixture
    async def api_server(self, mock_sg: Shotgun) -> FastMCP:
        """Create a FastMCP server with API tools registered."""
        server = FastMCP("test-server")
        register_api_tools(server, mock_sg)
        return server

    def test_register_api_tools(self, mock_sg: Shotgun):
        """Test register_api_tools function."""
        # Create a server
        server = FastMCP("test-server")

        # Register API tools
        register_api_tools(server, mock_sg)

        # Verify server was created
        assert server is not None

    @pytest.mark.asyncio
    async def test_sg_find(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.find tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "API_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Call the tool
        result = await api_server._mcp_call_tool(
            "sg.find",
            {
                "entity_type": "Shot",
                "filters": [["project", "is", {"type": "Project", "id": project["id"]}]],
                "fields": ["code", "project"],
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == shot["id"]
        assert result[0]["code"] == "API_SHOT_001"
        assert result[0]["type"] == "Shot"

    @pytest.mark.asyncio
    async def test_sg_find_one(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.find_one tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "API_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Call the tool
        result = await api_server._mcp_call_tool(
            "sg.find_one",
            {
                "entity_type": "Shot",
                "filters": [["id", "is", shot["id"]]],
                "fields": ["code", "project"],
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == shot["id"]
        assert result["code"] == "API_SHOT_001"
        assert result["type"] == "Shot"

    @pytest.mark.asyncio
    async def test_sg_create(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.create tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Call the tool
        result = await api_server._mcp_call_tool(
            "sg.create",
            {
                "entity_type": "Shot",
                "data": {
                    "code": "API_CREATED_SHOT",
                    "project": {"type": "Project", "id": project["id"]},
                },
                "return_fields": ["code", "project"],
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        assert "id" in result
        assert result["code"] == "API_CREATED_SHOT"
        assert result["type"] == "Shot"

    @pytest.mark.asyncio
    async def test_sg_update(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.update tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "API_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Call the tool
        result = await api_server._mcp_call_tool(
            "sg.update",
            {
                "entity_type": "Shot",
                "entity_id": shot["id"],
                "data": {
                    "code": "API_UPDATED_SHOT",
                },
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        assert result["id"] == shot["id"]
        assert result["type"] == "Shot"

        # Verify shot was updated
        updated_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]], ["code"])
        assert updated_shot["code"] == "API_UPDATED_SHOT"

    @pytest.mark.asyncio
    async def test_sg_delete_and_revive(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.delete and sg.revive tools."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "API_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Call the delete tool
        result = await api_server._mcp_call_tool(
            "sg.delete",
            {
                "entity_type": "Shot",
                "entity_id": shot["id"],
            }
        )

        # Verify result
        assert result is True

        # Verify shot was deleted
        deleted_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]], ["code"], retired_only=True)
        assert deleted_shot is not None

        # Call the revive tool
        result = await api_server._mcp_call_tool(
            "sg.revive",
            {
                "entity_type": "Shot",
                "entity_id": shot["id"],
            }
        )

        # Verify result
        assert result is True

        # Verify shot was revived
        revived_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]], ["code"])
        assert revived_shot is not None

    @pytest.mark.asyncio
    async def test_sg_batch(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.batch tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "API Test Project",
                "code": "api_test",
                "sg_status": "Active",
            },
        )

        # Call the batch tool
        result = await api_server._mcp_call_tool(
            "sg.batch",
            {
                "requests": [
                    {
                        "request_type": "create",
                        "entity_type": "Shot",
                        "data": {
                            "code": "BATCH_SHOT_001",
                            "project": {"type": "Project", "id": project["id"]},
                        },
                    },
                    {
                        "request_type": "create",
                        "entity_type": "Shot",
                        "data": {
                            "code": "BATCH_SHOT_002",
                            "project": {"type": "Project", "id": project["id"]},
                        },
                    },
                ]
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["code"] == "BATCH_SHOT_001"
        assert result[1]["code"] == "BATCH_SHOT_002"

    @pytest.mark.asyncio
    async def test_sg_schema_entity_read(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.schema_entity_read tool."""
        # Call the tool
        result = await api_server._mcp_call_tool("sg.schema_entity_read", {})

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        assert "Shot" in result
        assert "Project" in result

    @pytest.mark.asyncio
    async def test_sg_schema_field_read(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg.schema_field_read tool."""
        # Call the tool
        result = await api_server._mcp_call_tool(
            "sg.schema_field_read",
            {
                "entity_type": "Shot",
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, dict)
        assert "code" in result
        assert "project" in result
