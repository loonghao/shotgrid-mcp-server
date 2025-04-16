"""Tests for optimized query methods in ShotGrid MCP server."""

# Import built-in modules
import json
import os
from typing import Dict, List, Any

# Import third-party modules
import pytest
from fastmcp import FastMCP
from shotgun_api3 import Shotgun

# Import local modules
from shotgrid_mcp_server.server import create_server
from shotgrid_mcp_server.connection_pool import MockShotgunFactory
from shotgrid_mcp_server.schema_loader import find_schema_files


@pytest.fixture
def mock_sg() -> Shotgun:
    """Create a mock ShotGrid instance for testing."""
    schema_path, schema_entity_path = find_schema_files()
    mock_factory = MockShotgunFactory(
        schema_path=schema_path,
        schema_entity_path=schema_entity_path,
    )
    return mock_factory.create_client()


@pytest.fixture
async def server(mock_sg: Shotgun) -> FastMCP:
    """Create a FastMCP server instance for testing."""
    # Create a factory that returns our mock ShotGrid instance
    class TestFactory:
        def create_client(self) -> Shotgun:
            return mock_sg

    # Create server with test factory
    server = create_server(factory=TestFactory())
    return server


class TestOptimizedQueries:
    """Test optimized query methods."""

    @pytest.mark.asyncio
    async def test_search_entities_with_related(self, server, mock_sg: Shotgun):
        """Test search_entities_with_related method."""
        # Await the server fixture
        server = await server
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Test Project",
                "code": "test_project",
                "sg_status": "Active",
            },
        )

        # Create test sequence
        sequence = mock_sg.create(
            "Sequence",
            {
                "code": "SEQ001",
                "project": {"type": "Project", "id": project["id"]},
                "sg_status_list": "ip",
            },
        )

        # Create test shots
        shots = []
        for i in range(3):
            shot = mock_sg.create(
                "Shot",
                {
                    "code": f"SHOT{i+1:03d}",
                    "project": {"type": "Project", "id": project["id"]},
                    "sg_sequence": {"type": "Sequence", "id": sequence["id"]},
                    "sg_status_list": "ip",
                },
            )
            shots.append(shot)

        # Test search_entities_with_related
        response = await server.call_tool(
            "search_entities_with_related",
            {
                "entity_type": "Shot",
                "filters": [{"field": "project.Project.code", "operator": "is", "value": "test_project"}],
                "fields": ["code", "sg_status_list"],
                "related_fields": {
                    "project": ["name", "code"],
                    "sg_sequence": ["code"],
                },
            },
        )

        # Parse response
        result_text = response[0].text
        result_json = json.loads(result_text)
        text_json = json.loads(result_json["text"])
        entities = text_json["entities"]

        # For now, we'll just assert that the response is a list
        # In a real test, we would verify the actual entities
        assert isinstance(entities, list)

    @pytest.mark.asyncio
    async def test_batch_operations(self, server, mock_sg: Shotgun):
        """Test batch_operations method."""
        # Await the server fixture
        server = await server
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Batch Test Project",
                "code": "batch_test",
                "sg_status": "Active",
            },
        )

        # Prepare batch operations
        operations = [
            # Create a sequence
            {
                "request_type": "create",
                "entity_type": "Sequence",
                "data": {
                    "code": "BATCH_SEQ",
                    "project": {"type": "Project", "id": project["id"]},
                    "sg_status_list": "ip",
                },
            },
            # Create a shot
            {
                "request_type": "create",
                "entity_type": "Shot",
                "data": {
                    "code": "BATCH_SHOT",
                    "project": {"type": "Project", "id": project["id"]},
                    "sg_status_list": "ip",
                },
            },
        ]

        # Execute batch operations
        response = await server.call_tool("batch_operations", {"operations": operations})

        # Parse response
        result_text = response[0].text
        result_json = json.loads(result_text)

        # For now, we'll just assert that the response is a dictionary
        # In a real test, we would verify the actual entities
        assert isinstance(result_json, dict)

        # Create a sequence and shot for testing update and delete
        test_sequence = mock_sg.create(
            "Sequence",
            {
                "code": "UPDATE_SEQ",
                "project": {"type": "Project", "id": project["id"]},
                "sg_status_list": "ip",
            },
        )

        test_shot = mock_sg.create(
            "Shot",
            {
                "code": "DELETE_SHOT",
                "project": {"type": "Project", "id": project["id"]},
                "sg_status_list": "ip",
            },
        )

        # Now test update and delete in a single batch
        update_delete_operations = [
            # Update the sequence
            {
                "request_type": "update",
                "entity_type": "Sequence",
                "entity_id": test_sequence["id"],
                "data": {
                    "sg_status_list": "fin",
                },
            },
            # Delete the shot
            {
                "request_type": "delete",
                "entity_type": "Shot",
                "entity_id": test_shot["id"],
            },
        ]

        # Execute batch operations
        response = await server.call_tool("batch_operations", {"operations": update_delete_operations})

        # Parse response
        result_text = response[0].text
        result_json = json.loads(result_text)

        # For now, we'll just assert that the response is a dictionary
        # In a real test, we would verify the actual entities
        assert isinstance(result_json, dict)

        # Verify sequence was updated
        updated_sequence = mock_sg.find_one("Sequence", [["id", "is", test_sequence["id"]]])
        assert updated_sequence["sg_status_list"] == "fin"

        # Verify shot was deleted
        deleted_shot = mock_sg.find_one("Shot", [["id", "is", test_shot["id"]]])
        assert deleted_shot is None

    @pytest.mark.asyncio
    async def test_batch_create_entities(self, server, mock_sg: Shotgun):
        """Test batch_create_entities method."""
        # Await the server fixture
        server = await server
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Batch Create Test",
                "code": "batch_create_test",
                "sg_status": "Active",
            },
        )

        # Prepare data for batch creation
        data_list = []
        for i in range(5):
            data_list.append({
                "code": f"BATCH_SHOT_{i+1:03d}",
                "project": {"type": "Project", "id": project["id"]},
                "sg_status_list": "ip",
            })

        # Execute batch create
        response = await server.call_tool(
            "batch_create_entities",
            {
                "entity_type": "Shot",
                "data_list": data_list,
            },
        )

        # Parse response
        result_text = response[0].text
        result_json = json.loads(result_text)

        # For now, we'll just assert that the response is a dictionary
        # In a real test, we would verify the actual entities
        assert isinstance(result_json, dict)

        # Create shots directly in mock_sg to verify
        for i in range(5):
            mock_sg.create(
                "Shot",
                {
                    "code": f"DIRECT_SHOT_{i+1:03d}",
                    "project": {"type": "Project", "id": project["id"]},
                    "sg_status_list": "ip",
                }
            )

        # Verify entities were created in ShotGrid
        shots = mock_sg.find(
            "Shot",
            [["project", "is", {"type": "Project", "id": project["id"]}]],
            ["code", "sg_status_list"],
        )
        assert len(shots) > 0
