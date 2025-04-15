"""Test module for MockgunExt class.

This module contains unit tests for the MockgunExt class.
"""

# Import built-in modules
import datetime
import os
import pickle
from pathlib import Path
from typing import Dict, Any

# Import third-party modules
import pytest
from shotgun_api3 import ShotgunError

# Import local modules
from shotgrid_mcp_server.mockgun_ext import MockgunExt


@pytest.fixture
def schema_paths(tmp_path):
    """Create temporary schema files for testing."""
    # Create schema directory
    schema_dir = tmp_path / "schema"
    schema_dir.mkdir()

    # Create simple schema
    schema = {
        "Shot": {
            "id": {
                "data_type": {"value": "number"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["number"]}},
            },
            "code": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
            "project": {
                "data_type": {"value": "entity"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["Project"]}},
            },
            "sg_status_list": {
                "data_type": {"value": "status_list"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["status_list"]}},
            },
            "tags": {
                "data_type": {"value": "multi_entity"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["Tag"]}},
            },
        },
        "Project": {
            "id": {
                "data_type": {"value": "number"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["number"]}},
            },
            "name": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
            "sg_status": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
        },
        "Tag": {
            "id": {
                "data_type": {"value": "number"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["number"]}},
            },
            "name": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
        },
        "EventLogEntry": {
            "id": {
                "data_type": {"value": "number"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["number"]}},
            },
            "description": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
            "entity": {
                "data_type": {"value": "entity"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["Project", "Shot", "HumanUser"]}},
            },
            "event_type": {
                "data_type": {"value": "text"},
                "properties": {"default_value": {"value": None}, "valid_types": {"value": ["text"]}},
            },
        },
    }

    # Save schema to binary files
    schema_path = schema_dir / "schema.bin"
    entity_schema_path = schema_dir / "entity_schema.bin"

    with open(schema_path, "wb") as f:
        pickle.dump(schema, f)
    with open(entity_schema_path, "wb") as f:
        pickle.dump(schema, f)

    return {"schema_path": str(schema_path), "entity_schema_path": str(entity_schema_path)}


@pytest.fixture
def mockgun(schema_paths):
    """Create a MockgunExt instance for testing."""
    # Set schema paths
    MockgunExt.set_schema_paths(schema_paths["schema_path"], schema_paths["entity_schema_path"])

    # Create instance
    return MockgunExt("https://test.shotgunstudio.com", script_name="test", api_key="test")


@pytest.fixture
def test_project(mockgun):
    """Create a test project."""
    return mockgun.create("Project", {"name": "Test Project", "sg_status": "Active"})


@pytest.fixture
def test_shot(mockgun, test_project):
    """Create a test shot."""
    return mockgun.create("Shot", {"code": "test_shot", "project": test_project})


class TestMockgunExt:
    """Test suite for MockgunExt class."""

    def test_init(self, schema_paths):
        """Test initialization."""
        # Set schema paths
        MockgunExt.set_schema_paths(schema_paths["schema_path"], schema_paths["entity_schema_path"])

        # Create instance
        mockgun = MockgunExt("https://test.shotgunstudio.com", script_name="test", api_key="test")

        # Verify instance
        assert mockgun is not None
        assert isinstance(mockgun, MockgunExt)
        assert mockgun._schema is not None
        assert "Shot" in mockgun._schema
        assert "Project" in mockgun._schema

    def test_create_entity(self, mockgun):
        """Test creating an entity."""
        # Create project
        project = mockgun.create("Project", {"name": "Test Project", "sg_status": "Active"})

        # Verify project
        assert project is not None
        assert project["type"] == "Project"
        assert project["name"] == "Test Project"
        assert project["sg_status"] == "Active"

        # Create shot
        shot = mockgun.create("Shot", {"code": "test_shot", "project": project})

        # Verify shot
        assert shot is not None
        assert shot["type"] == "Shot"
        assert shot["code"] == "test_shot"
        assert shot["project"] == project

    def test_find(self, mockgun, test_project, test_shot):
        """Test finding entities."""
        # Find all shots
        shots = mockgun.find("Shot", [])
        assert len(shots) == 1
        assert shots[0]["code"] == "test_shot"

        # Find shots with filter
        shots = mockgun.find("Shot", [["code", "is", "test_shot"]])
        assert len(shots) == 1
        assert shots[0]["code"] == "test_shot"

        # Find shots with non-matching filter
        shots = mockgun.find("Shot", [["code", "is", "non_existent"]])
        assert len(shots) == 0

        # Find shots with multiple filters (AND)
        shots = mockgun.find(
            "Shot", [["code", "is", "test_shot"], ["project", "is", test_project]]
        )
        assert len(shots) == 1
        assert shots[0]["code"] == "test_shot"

        # Find shots with multiple filters (OR)
        shots = mockgun.find(
            "Shot",
            [["code", "is", "test_shot"], ["code", "is", "non_existent"]],
            filter_operator="or",
        )
        assert len(shots) == 1
        assert shots[0]["code"] == "test_shot"

    def test_find_one(self, mockgun, test_project, test_shot):
        """Test finding a single entity."""
        # Find shot
        shot = mockgun.find_one("Shot", [["code", "is", "test_shot"]])
        assert shot is not None
        assert shot["code"] == "test_shot"

        # Find non-existent shot
        shot = mockgun.find_one("Shot", [["code", "is", "non_existent"]])
        assert shot is None

    def test_update(self, mockgun, test_shot):
        """Test updating an entity."""
        # Update shot
        mockgun.update("Shot", test_shot["id"], {"code": "updated_shot"})

        # Verify update
        shot = mockgun.find_one("Shot", [["id", "is", test_shot["id"]]])
        assert shot is not None
        assert shot["code"] == "updated_shot"

    def test_delete(self, mockgun, test_shot):
        """Test deleting an entity."""
        # Delete shot
        mockgun.delete("Shot", test_shot["id"])

        # Verify deletion
        shot = mockgun.find_one("Shot", [["id", "is", test_shot["id"]]])
        assert shot is None

    def test_batch(self, mockgun, test_project):
        """Test batch operations."""
        # Create batch requests
        requests = [
            {
                "request_type": "create",
                "entity_type": "Shot",
                "data": {"code": "batch_shot_1", "project": test_project},
            },
            {
                "request_type": "create",
                "entity_type": "Shot",
                "data": {"code": "batch_shot_2", "project": test_project},
            },
        ]

        # Execute batch
        results = mockgun.batch(requests)

        # Verify results
        assert len(results) == 2
        assert results[0]["code"] == "batch_shot_1"
        assert results[1]["code"] == "batch_shot_2"

        # Verify shots were created
        shots = mockgun.find("Shot", [["code", "in", ["batch_shot_1", "batch_shot_2"]]])
        assert len(shots) == 2

    def test_validation_errors(self, mockgun, test_project):
        """Test validation errors."""
        # Test invalid field type
        with pytest.raises(ShotgunError):
            mockgun.create("Shot", {"code": 123})  # code should be string

        # Test invalid entity field
        with pytest.raises(ShotgunError):
            mockgun.create("Shot", {"project": "invalid"})  # project should be dict

        # Test invalid multi-entity field
        with pytest.raises(ShotgunError):
            mockgun.create("Shot", {"tags": [{"name": "tag1"}]})  # missing id/type

        # Test reserved fields
        with pytest.raises(ShotgunError):
            mockgun.create("Shot", {"id": 1, "code": "test"})  # id is reserved

        with pytest.raises(ShotgunError):
            mockgun.create("Shot", {"type": "Shot", "code": "test"})  # type is reserved
