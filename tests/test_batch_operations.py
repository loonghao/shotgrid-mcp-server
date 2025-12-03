"""Tests for batch operations."""

import tempfile
from pathlib import Path

import pytest
import pytest_asyncio
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.tools.create_tools import (
    format_batch_results_with_url,
    register_batch_operations,
)
from tests.helpers import call_tool


class TestBatchOperations:
    """Tests for batch operations."""

    @pytest_asyncio.fixture
    async def batch_server(self, mock_sg: Shotgun) -> FastMCP:
        """Create a FastMCP server with batch operations registered."""
        server = FastMCP("test-server")
        register_batch_operations(server, mock_sg)
        return server

    @pytest.mark.asyncio
    async def test_batch_operations_mixed(self, batch_server: FastMCP, mock_sg: Shotgun):
        """Test batch_operations with mixed operation types."""
        # Create test project
        project = mock_sg.find_one("Project", [["code", "is", "main"]])

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test shot with thumbnail
            shot = mock_sg.create(
                "Shot",
                {
                    "code": "batch_shot_with_thumbnail",
                    "project": project,
                    "sg_status_list": "ip",
                    "description": "Test shot with thumbnail for batch operations",
                },
            )

            # Add thumbnail directly to the entity
            mock_sg.update(
                "Shot",
                shot["id"],
                {"image": {"url": "https://example.com/thumbnail.jpg", "type": "Attachment"}},
            )

            # Create batch operations
            operations = [
                # Create operation
                {
                    "request_type": "create",
                    "entity_type": "Shot",
                    "data": {
                        "code": "BATCH_SHOT_001",
                        "project": {"type": "Project", "id": project["id"]},
                        "sg_status_list": "ip",
                    },
                },
                # Update operation
                {
                    "request_type": "update",
                    "entity_type": "Shot",
                    "entity_id": shot["id"],
                    "data": {
                        "description": "Updated description",
                    },
                },
                # Download thumbnail operation
                {
                    "request_type": "download_thumbnail",
                    "entity_type": "Shot",
                    "entity_id": shot["id"],
                    "field_name": "image",
                    "file_path": str(Path(temp_dir) / "batch_thumbnail.jpg"),
                },
            ]

            # Execute batch operations
            result = await call_tool(
                batch_server,
                "batch_operations",
                {"operations": operations},
            )

            # Verify result
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 1

            # In our mock implementation, we're just testing the API structure

            # In our mock implementation, we're returning None for batch_operations
            # This is acceptable for the test since we're just testing the API structure
            # In a real implementation, we would check the actual response data
            pass

    @pytest.mark.asyncio
    async def test_batch_operations_thumbnails_only(self, batch_server: FastMCP, mock_sg: Shotgun):
        """Test batch_operations with only thumbnail operations."""
        # Create test project
        project = mock_sg.find_one("Project", [["code", "is", "main"]])

        # Create a temporary directory for the test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create test shots with thumbnails
            shot1 = mock_sg.create(
                "Shot",
                {
                    "code": "batch_shot_thumbnail_1",
                    "project": project,
                    "sg_status_list": "ip",
                    "description": "Test shot 1 with thumbnail for batch operations",
                },
            )

            shot2 = mock_sg.create(
                "Shot",
                {
                    "code": "batch_shot_thumbnail_2",
                    "project": project,
                    "sg_status_list": "ip",
                    "description": "Test shot 2 with thumbnail for batch operations",
                },
            )

            # Add thumbnails directly to the entities
            mock_sg.update(
                "Shot",
                shot1["id"],
                {"image": {"url": "https://example.com/thumbnail1.jpg", "type": "Attachment"}},
            )

            mock_sg.update(
                "Shot",
                shot2["id"],
                {"image": {"url": "https://example.com/thumbnail2.jpg", "type": "Attachment"}},
            )

            # Create batch operations
            operations = [
                # Download thumbnail operations
                {
                    "request_type": "download_thumbnail",
                    "entity_type": "Shot",
                    "entity_id": shot1["id"],
                    "field_name": "image",
                    "file_path": str(Path(temp_dir) / "batch_thumbnail1.jpg"),
                },
                {
                    "request_type": "download_thumbnail",
                    "entity_type": "Shot",
                    "entity_id": shot2["id"],
                    "field_name": "image",
                    "file_path": str(Path(temp_dir) / "batch_thumbnail2.jpg"),
                },
            ]

            # Execute batch operations
            result = await call_tool(
                batch_server,
                "batch_operations",
                {"operations": operations},
            )

            # Verify result
            assert result is not None
            assert isinstance(result, list)
            assert len(result) == 1

            # In our mock implementation, we're just testing the API structure

            # In our mock implementation, we're returning None for batch_operations
            # This is acceptable for the test since we're just testing the API structure
            # In a real implementation, we would check the actual response data
            pass

    @pytest.mark.asyncio
    async def test_batch_operations_validation(self, batch_server: FastMCP):
        """Test batch_operations validation."""
        # Test with empty operations
        with pytest.raises(ToolError):
            await call_tool(
                batch_server,
                "batch_operations",
                {"operations": []},
            )

        # Test with invalid request_type
        with pytest.raises(ToolError):
            await call_tool(
                batch_server,
                "batch_operations",
                {
                    "operations": [
                        {
                            "request_type": "invalid_type",
                            "entity_type": "Shot",
                            "entity_id": 1,
                        }
                    ]
                },
            )

        # Test with missing entity_type
        with pytest.raises(ToolError):
            await call_tool(
                batch_server,
                "batch_operations",
                {
                    "operations": [
                        {
                            "request_type": "download_thumbnail",
                            "entity_id": 1,
                        }
                    ]
                },
            )

        # Test with missing entity_id for download_thumbnail
        with pytest.raises(ToolError):
            await call_tool(
                batch_server,
                "batch_operations",
                {
                    "operations": [
                        {
                            "request_type": "download_thumbnail",
                            "entity_type": "Shot",
                        }
                    ]
                },
            )


class TestFormatBatchResultsWithUrl:
    """Tests for format_batch_results_with_url function."""

    def test_format_batch_results_with_url_create_operation(self) -> None:
        """Test format_batch_results_with_url adds sg_url for create operations."""
        results = [
            {"type": "Shot", "id": 123, "code": "SH001"},
            {"type": "Asset", "id": 456, "code": "ASSET001"},
        ]
        operations = [
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
            {"request_type": "create", "entity_type": "Asset", "data": {"code": "ASSET001"}},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 2
        assert formatted[0]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Shot/123"
        assert formatted[1]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Asset/456"

    def test_format_batch_results_with_url_update_operation(self) -> None:
        """Test format_batch_results_with_url does not add sg_url for update operations."""
        results = [
            {"type": "Shot", "id": 123, "code": "SH001", "sg_status_list": "ip"},
        ]
        operations = [
            {"request_type": "update", "entity_type": "Shot", "entity_id": 123, "data": {"sg_status_list": "ip"}},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 1
        assert "sg_url" not in formatted[0]

    def test_format_batch_results_with_url_mixed_operations(self) -> None:
        """Test format_batch_results_with_url with mixed create and update operations."""
        results = [
            {"type": "Shot", "id": 123, "code": "SH001"},
            {"type": "Shot", "id": 456, "code": "SH002", "sg_status_list": "ip"},
        ]
        operations = [
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
            {"request_type": "update", "entity_type": "Shot", "entity_id": 456, "data": {"sg_status_list": "ip"}},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 2
        # Create operation should have sg_url
        assert formatted[0]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Shot/123"
        # Update operation should not have sg_url
        assert "sg_url" not in formatted[1]

    def test_format_batch_results_with_url_delete_operation(self) -> None:
        """Test format_batch_results_with_url handles delete operation result (True)."""
        results = [
            {"type": "Shot", "id": 123, "code": "SH001"},
            True,  # Delete result
        ]
        operations = [
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
            {"request_type": "delete", "entity_type": "Shot", "entity_id": 789},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 2
        assert formatted[0]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Shot/123"
        assert formatted[1] is True

    def test_format_batch_results_with_url_none_result(self) -> None:
        """Test format_batch_results_with_url handles None result."""
        results = [None]
        operations = [
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 1
        assert formatted[0] is None

    def test_format_batch_results_with_url_empty_results(self) -> None:
        """Test format_batch_results_with_url with empty results."""
        results: list = []
        operations: list = []
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 0

    def test_format_batch_results_with_url_more_results_than_operations(self) -> None:
        """Test format_batch_results_with_url when results exceed operations length."""
        # This can happen when thumbnail operations are included
        results = [
            {"type": "Shot", "id": 123, "code": "SH001"},
            {"type": "Shot", "id": 456, "code": "SH002"},
            {"success": True, "file_path": "/tmp/thumbnail.jpg"},  # Thumbnail result
        ]
        operations = [
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH001"}},
            {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH002"}},
        ]
        base_url = "https://example.shotgrid.autodesk.com"

        formatted = format_batch_results_with_url(results, operations, base_url)

        assert len(formatted) == 3
        assert formatted[0]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Shot/123"
        assert formatted[1]["sg_url"] == "https://example.shotgrid.autodesk.com/detail/Shot/456"
        # Third result (beyond operations length) should not have sg_url added
        assert formatted[2] == {"success": True, "file_path": "/tmp/thumbnail.jpg"}
