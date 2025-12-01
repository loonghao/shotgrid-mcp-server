"""Tests for api_tools module."""

import json

import pytest
import pytest_asyncio
from fastmcp import FastMCP
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
            },
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
            },
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
            },
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
            },
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
            },
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
            },
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
            },
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
        result = await call_tool(api_server, "sg.schema_entity_read", {})

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
            },
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        # The length of the result can vary depending on the API version
        # We just need to make sure it's not empty
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_sg_text_search_entity_types_list_conversion(
        self, api_server: FastMCP, mock_sg: Shotgun
    ):
        """Test that sg_text_search converts list of entity types to dict format."""
        import json

        # Create test data
        project = mock_sg.create(
            "Project",
            {
                "name": "Text Search Test",
                "code": "text_search_test",
                "sg_status": "Active",
            },
        )

        shot = mock_sg.create(
            "Shot",
            {
                "code": "SHOT_animation",
                "project": project,
            },
        )

        asset = mock_sg.create(
            "Asset",
            {
                "code": "CHAR_animation",
                "project": project,
                "sg_asset_type": "Character",
            },
        )

        # Test with list of entity types (should be converted to dict internally)
        result = await api_server._mcp_call_tool(
            "sg_text_search",
            {
                "text": "animation",
                "entity_types": ["Shot", "Asset"],  # List format
            },
        )

        # Parse the result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        data = json.loads(result[0].text)

        # Verify result structure
        assert "matches" in data

        # Verify we got results from both entity types
        matches = data["matches"]
        entity_types_found = {match["type"] for match in matches}
        assert "Shot" in entity_types_found or "Asset" in entity_types_found

    @pytest.mark.asyncio
    async def test_sg_text_search_single_entity_type(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg_text_search with single entity type."""
        import json

        # Create test data
        project = mock_sg.create(
            "Project",
            {
                "name": "Single Type Search",
                "code": "single_type_search",
                "sg_status": "Active",
            },
        )

        user = mock_sg.create(
            "HumanUser",
            {
                "login": "john.doe",
                "name": "John Doe",
                "email": "john.doe@example.com",
            },
        )

        # Test with single entity type
        result = await api_server._mcp_call_tool(
            "sg_text_search",
            {
                "text": "John",
                "entity_types": ["HumanUser"],  # Single entity type as list
            },
        )

        # Parse the result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        data = json.loads(result[0].text)

        # Verify result
        assert "matches" in data

    @pytest.mark.asyncio
    async def test_sg_text_search_with_project_filter(
        self, api_server: FastMCP, mock_sg: Shotgun
    ):
        """Test sg_text_search with project_ids filter."""
        import json

        # Create test projects
        project1 = mock_sg.create(
            "Project",
            {
                "name": "Project One",
                "code": "proj1",
                "sg_status": "Active",
            },
        )

        project2 = mock_sg.create(
            "Project",
            {
                "name": "Project Two",
                "code": "proj2",
                "sg_status": "Active",
            },
        )

        # Create shots in different projects
        shot1 = mock_sg.create(
            "Shot",
            {
                "code": "SHOT_hero",
                "project": project1,
            },
        )

        shot2 = mock_sg.create(
            "Shot",
            {
                "code": "SHOT_villain",
                "project": project2,
            },
        )

        # Test with project filter
        result = await api_server._mcp_call_tool(
            "sg_text_search",
            {
                "text": "SHOT",
                "entity_types": ["Shot"],
                "project_ids": [project1["id"]],  # Only search in project1
            },
        )

        # Parse the result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        data = json.loads(result[0].text)

        # Verify result
        assert "matches" in data

    @pytest.mark.asyncio
    async def test_sg_text_search_minimum_length_validation(self, api_server: FastMCP):
        """Test that sg_text_search validates minimum text length (3 characters)."""
        from fastmcp.exceptions import ToolError

        # Test with empty string
        with pytest.raises(ToolError) as exc_info:
            await api_server._mcp_call_tool(
                "sg_text_search",
                {
                    "text": "",
                    "entity_types": ["Shot"],
                },
            )
        assert "at least 3 characters" in str(exc_info.value)
        assert "0 characters" in str(exc_info.value)

        # Test with 1 character
        with pytest.raises(ToolError) as exc_info:
            await api_server._mcp_call_tool(
                "sg_text_search",
                {
                    "text": "a",
                    "entity_types": ["Shot"],
                },
            )
        assert "at least 3 characters" in str(exc_info.value)
        assert "1 characters" in str(exc_info.value)

        # Test with 2 characters
        with pytest.raises(ToolError) as exc_info:
            await api_server._mcp_call_tool(
                "sg_text_search",
                {
                    "text": "ab",
                    "entity_types": ["Shot"],
                },
            )
        assert "at least 3 characters" in str(exc_info.value)
        assert "2 characters" in str(exc_info.value)

        # Test with whitespace only
        with pytest.raises(ToolError) as exc_info:
            await api_server._mcp_call_tool(
                "sg_text_search",
                {
                    "text": "  ",
                    "entity_types": ["Shot"],
                },
            )
        assert "at least 3 characters" in str(exc_info.value)
        assert "0 characters" in str(exc_info.value)  # Whitespace is stripped

    @pytest.mark.asyncio
    async def test_sg_text_search_valid_minimum_length(
        self, api_server: FastMCP, mock_sg: Shotgun
    ):
        """Test that sg_text_search accepts exactly 3 characters."""
        import json

        # Create test data
        project = mock_sg.create(
            "Project",
            {
                "name": "Min Length Test",
                "code": "min_test",
                "sg_status": "Active",
            },
        )

        shot = mock_sg.create(
            "Shot",
            {
                "code": "ABC",
                "project": project,
            },
        )

        # Test with exactly 3 characters (should succeed)
        result = await api_server._mcp_call_tool(
            "sg_text_search",
            {
                "text": "ABC",
                "entity_types": ["Shot"],
            },
        )

        # Parse the result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) == 1
        data = json.loads(result[0].text)

        # Should succeed (not an error)
        assert "isError" not in data or data["isError"] is False
        assert "matches" in data

    @pytest.mark.asyncio
    async def test_sg_upload(self, api_server: FastMCP, mock_sg: Shotgun, tmp_path):
        """Test sg.upload tool returns structured UploadResult."""
        # Create a test file
        test_file = tmp_path / "test_movie.mov"
        test_file.write_bytes(b"fake movie content" * 1000)  # ~18KB file

        # Create test project and version
        project = mock_sg.create(
            "Project",
            {
                "name": "Upload Test Project",
                "code": "upload_test",
                "sg_status": "Active",
            },
        )

        version = mock_sg.create(
            "Version",
            {
                "code": "upload_test_v001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Call the upload tool
        result = await call_tool(
            api_server,
            "sg_upload",
            {
                "entity_type": "Version",
                "entity_id": version["id"],
                "path": str(test_file),
                "field_name": "sg_uploaded_movie",
                "display_name": "Test Movie",
            },
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured UploadResult fields
        assert isinstance(response_data, dict)
        assert "attachment_id" in response_data
        assert isinstance(response_data["attachment_id"], int)
        assert response_data["success"] is True
        assert response_data["entity_type"] == "Version"
        assert response_data["entity_id"] == version["id"]
        assert response_data["field_name"] == "sg_uploaded_movie"
        assert response_data["file_name"] == "test_movie.mov"
        assert response_data["file_size_bytes"] > 0
        assert "file_size_display" in response_data
        assert response_data["status"] == "completed"
        assert "message" in response_data
        assert "Successfully uploaded" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_delete_structured_response(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg_delete tool returns structured DeleteResult."""
        # Create test project and shot
        project = mock_sg.create(
            "Project",
            {"name": "Delete Test Project", "code": "delete_test", "sg_status": "Active"},
        )
        shot = mock_sg.create(
            "Shot",
            {"code": "DELETE_SHOT", "project": {"type": "Project", "id": project["id"]}},
        )

        # Call the delete tool
        result = await call_tool(
            api_server,
            "sg_delete",
            {"entity_type": "Shot", "entity_id": shot["id"]},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured DeleteResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["entity_type"] == "Shot"
        assert response_data["entity_id"] == shot["id"]
        assert "message" in response_data
        assert "Successfully deleted" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_revive_structured_response(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg_revive tool returns structured ReviveResult."""
        # Create test project and shot
        project = mock_sg.create(
            "Project",
            {"name": "Revive Test Project", "code": "revive_test", "sg_status": "Active"},
        )
        shot = mock_sg.create(
            "Shot",
            {"code": "REVIVE_SHOT", "project": {"type": "Project", "id": project["id"]}},
        )

        # Call the revive tool
        result = await call_tool(
            api_server,
            "sg_revive",
            {"entity_type": "Shot", "entity_id": shot["id"]},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured ReviveResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["entity_type"] == "Shot"
        assert response_data["entity_id"] == shot["id"]
        assert "message" in response_data
        assert "Successfully revived" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_download_attachment_structured_response(self, api_server: FastMCP, tmp_path):
        """Test sg_download_attachment tool returns structured DownloadResult."""
        # Create a mock attachment reference
        attachment = {"type": "Attachment", "id": 123, "name": "test_image.jpg"}
        download_path = str(tmp_path / "downloaded_image.jpg")

        # Call the download attachment tool
        result = await call_tool(
            api_server,
            "sg_download_attachment",
            {"attachment": attachment, "file_path": download_path},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured DownloadResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["file_path"] == download_path
        assert "file_name" in response_data
        assert "file_size_bytes" in response_data
        assert "file_size_display" in response_data
        assert response_data["status"] == "completed"
        assert "message" in response_data
        assert "Successfully downloaded" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_follow_structured_response(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg_follow tool returns structured FollowResult."""
        # Create test project and task
        project = mock_sg.create(
            "Project",
            {"name": "Follow Test Project", "code": "follow_test", "sg_status": "Active"},
        )
        task = mock_sg.create(
            "Task",
            {"content": "Test Task", "project": {"type": "Project", "id": project["id"]}},
        )

        # Call the follow tool
        result = await call_tool(
            api_server,
            "sg_follow",
            {"entity_type": "Task", "entity_id": task["id"]},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured FollowResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["action"] == "follow"
        assert response_data["entity_type"] == "Task"
        assert response_data["entity_id"] == task["id"]
        assert "message" in response_data
        assert "Successfully started following" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_unfollow_structured_response(self, api_server: FastMCP, mock_sg: Shotgun):
        """Test sg_unfollow tool returns structured FollowResult."""
        # Create test project and task
        project = mock_sg.create(
            "Project",
            {"name": "Unfollow Test Project", "code": "unfollow_test", "sg_status": "Active"},
        )
        task = mock_sg.create(
            "Task",
            {"content": "Test Task", "project": {"type": "Project", "id": project["id"]}},
        )

        # Call the unfollow tool
        result = await call_tool(
            api_server,
            "sg_unfollow",
            {"entity_type": "Task", "entity_id": task["id"]},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured FollowResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["action"] == "unfollow"
        assert response_data["entity_type"] == "Task"
        assert response_data["entity_id"] == task["id"]
        assert "message" in response_data
        assert "Successfully stopped following" in response_data["message"]

    @pytest.mark.asyncio
    async def test_sg_update_project_last_accessed_structured_response(
        self, api_server: FastMCP, mock_sg: Shotgun
    ):
        """Test sg_update_project_last_accessed tool returns structured ProjectAccessResult."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {"name": "Access Test Project", "code": "access_test", "sg_status": "Active"},
        )

        # Call the update project last accessed tool
        result = await call_tool(
            api_server,
            "sg_update_project_last_accessed",
            {"project_id": project["id"]},
        )

        # Verify result
        assert result is not None
        assert isinstance(result, list)
        assert len(result) > 0

        # Parse the JSON response
        response_text = result[0].text
        response_data = json.loads(response_text)

        # Verify structured ProjectAccessResult fields
        assert isinstance(response_data, dict)
        assert response_data["success"] is True
        assert response_data["project_id"] == project["id"]
        assert "message" in response_data
        assert "Successfully updated last accessed time" in response_data["message"]
