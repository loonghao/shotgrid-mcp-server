"""Tests for schema validation functionality."""

import pytest
from unittest.mock import MagicMock

from shotgrid_mcp_server.schema_validator import SchemaValidator, get_schema_validator


@pytest.fixture
def mock_sg():
    """Create a mock ShotGrid connection."""
    sg = MagicMock()
    
    # Mock schema for Shot entity
    sg.schema_field_read.return_value = {
        "code": {
            "data_type": {"value": "text"},
            "editable": True,
            "mandatory": {"value": True},
        },
        "sg_status_list": {
            "data_type": {"value": "status_list"},
            "editable": True,
            "mandatory": {"value": False},
        },
        "sg_cut_in": {
            "data_type": {"value": "number"},
            "editable": True,
            "mandatory": {"value": False},
        },
        "created_at": {
            "data_type": {"value": "date_time"},
            "editable": False,  # Not editable
            "mandatory": {"value": False},
        },
    }
    
    return sg


@pytest.fixture
def validator():
    """Create a schema validator instance."""
    from shotgrid_mcp_server.schema_cache import get_schema_cache
    # Clear cache before each test
    cache = get_schema_cache()
    cache.clear()
    return SchemaValidator()


def test_validate_valid_fields(validator, mock_sg):
    """Test validation of valid fields."""
    data = {
        "code": "SH001",
        "sg_status_list": "ip",
        "sg_cut_in": 1001,
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert result["valid"] == ["code", "sg_status_list", "sg_cut_in"]
    assert result["invalid"] == []
    assert len(result["warnings"]) == 0


def test_validate_invalid_fields(validator, mock_sg):
    """Test validation of invalid fields."""
    data = {
        "code": "SH001",
        "invalid_field": "value",
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert "code" in result["valid"]
    assert "invalid_field" in result["invalid"]
    assert any("Unknown field" in w for w in result["warnings"])


def test_validate_non_editable_field(validator, mock_sg):
    """Test validation warns about non-editable fields."""
    data = {
        "code": "SH001",
        "created_at": "2025-01-20",
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert "created_at" in result["valid"]  # Field exists
    assert any("not editable" in w for w in result["warnings"])


def test_validate_field_type_mismatch(validator, mock_sg):
    """Test validation warns about type mismatches."""
    data = {
        "code": "SH001",
        "sg_cut_in": "not_a_number",  # Should be number
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert "sg_cut_in" in result["valid"]  # Field exists
    assert any("expects number" in w for w in result["warnings"])


def test_validate_required_fields(validator, mock_sg):
    """Test validation checks required fields."""
    data = {
        "sg_status_list": "ip",
        # Missing required field "code"
    }
    
    result = validator.validate_fields("Shot", data, mock_sg, check_required=True)
    
    assert any("Missing required fields" in w and "code" in w for w in result["warnings"])


def test_validate_schema_fetch_failure(validator):
    """Test validation handles schema fetch failures gracefully."""
    mock_sg = MagicMock()
    mock_sg.schema_field_read.side_effect = Exception("Connection error")
    
    data = {"code": "SH001"}
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    # Should return all fields as valid when schema is unavailable
    assert result["valid"] == ["code"]
    assert result["invalid"] == []
    assert any("schema unavailable" in w for w in result["warnings"])


def test_global_validator_instance():
    """Test getting the global validator instance."""
    validator1 = get_schema_validator()
    validator2 = get_schema_validator()
    
    # Should return the same instance
    assert validator1 is validator2


def test_validate_entity_reference(validator, mock_sg):
    """Test validation of entity reference fields."""
    # Add entity field to mock schema
    mock_sg.schema_field_read.return_value["project"] = {
        "data_type": {"value": "entity"},
        "editable": True,
        "mandatory": {"value": False},
    }
    
    data = {
        "code": "SH001",
        "project": {"type": "Project", "id": 123},
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert "project" in result["valid"]
    assert len(result["invalid"]) == 0


def test_validate_multi_entity_field(validator, mock_sg):
    """Test validation of multi-entity fields."""
    # Add multi_entity field to mock schema
    mock_sg.schema_field_read.return_value["tasks"] = {
        "data_type": {"value": "multi_entity"},
        "editable": True,
        "mandatory": {"value": False},
    }
    
    data = {
        "code": "SH001",
        "tasks": [
            {"type": "Task", "id": 1},
            {"type": "Task", "id": 2},
        ],
    }
    
    result = validator.validate_fields("Shot", data, mock_sg)
    
    assert "tasks" in result["valid"]
    assert len(result["invalid"]) == 0

