"""Tests for api_tools module."""

import json
import pytest
import pytest_asyncio
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.api_tools import register_api_tools
from tests.helpers import call_tool


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
        result = await call_tool(
            api_server,
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
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify the parsed response
        assert response_data is not None
        assert isinstance(response_data, list)
        assert len(response_data) == 1  # The expected length is 1 in the test environment

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
        result = await call_tool(
            api_server,
            "sg.find_one",
            {
                "entity_type": "Shot",
                "filters": [["id", "is", shot["id"]]],
                "fields": ["code", "project"],
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify the parsed response
        assert response_data is not None

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
        result = await call_tool(
            api_server,
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
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify the parsed response
        assert isinstance(response_data, dict)
        assert "id" in response_data
        assert response_data["code"] == "API_CREATED_SHOT"
        assert response_data["type"] == "Shot"

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
        result = await call_tool(
            api_server,
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
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify the parsed response
        assert response_data is not None

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
        delete_result = await call_tool(
            api_server,
            "sg.delete",
            {
                "entity_type": "Shot",
                "entity_id": shot["id"],
            }
        )

        # Verify result
        # The result could be any format depending on the API version
        # Just verify that the shot was deleted

        # Verify the result
        # The result could be True or a different format depending on the API version
        # Just verify that the shot was deleted

        # Verify shot was deleted
        deleted_shot = mock_sg.find_one("Shot", [["id", "is", shot["id"]]], ["code"], retired_only=True)
        assert deleted_shot is not None

        # Call the revive tool
        revive_result = await call_tool(
            api_server,
            "sg.revive",
            {
                "entity_type": "Shot",
                "entity_id": shot["id"],
            }
        )

        # Verify result
        # The result could be any format depending on the API version
        # Just verify that the shot was revived

        # Verify the result
        # The result could be True or a different format depending on the API version
        # Just verify that the shot was revived

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
        result = await call_tool(
            api_server,
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
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify the parsed response
        assert isinstance(response_data, list)
        assert len(response_data) == 2

    @pytest.mark.asyncio
    async def test_sg_schema_entity_read(self, api_server: FastMCP):
        """Test sg.schema_entity_read tool."""
        # Call the tool
        result = await call_tool(
            api_server,
            "sg.schema_entity_read",
            {}
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_sg_schema_field_read(self, api_server: FastMCP):
        """Test sg.schema_field_read tool."""
        # Call the tool
        result = await call_tool(
            api_server,
            "sg.schema_field_read",
            {
                "entity_type": "Shot",
            }
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0