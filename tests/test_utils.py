"""Tests for utils module."""

import os
import tempfile
from pathlib import Path
from unittest import mock

from shotgrid_mcp_server.utils import (
    generate_default_file_path,
    simplify_json_schema,
    simplify_tool_schemas,
)


class TestGenerateDefaultFilePath:
    """Tests for generate_default_file_path function."""

    def test_generate_default_file_path_default_params(self):
        """Test generate_default_file_path with default parameters."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Call the function
                result = generate_default_file_path("Shot", 123)

                # Check the result
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                expected_file = expected_dir / "Shot_123_image.jpg"
                assert result == str(expected_file)

                # Verify the directory was created
                assert expected_dir.exists()

    def test_generate_default_file_path_custom_params(self):
        """Test generate_default_file_path with custom parameters."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Call the function with custom parameters
                result = generate_default_file_path(
                    entity_type="Asset",
                    entity_id=456,
                    field_name="custom_image",
                    image_format="png",
                )

                # Check the result
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                expected_file = expected_dir / "Asset_456_custom_image.png"
                assert result == str(expected_file)

                # Verify the directory was created
                assert expected_dir.exists()

    def test_generate_default_file_path_directory_creation(self):
        """Test that generate_default_file_path creates the directory if it doesn't exist."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Ensure the directory doesn't exist
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                if expected_dir.exists():
                    os.rmdir(expected_dir)

                # Call the function
                generate_default_file_path("Version", 789)

                # Verify the directory was created
                assert expected_dir.exists()


class TestSimplifyJsonSchema:
    """Tests for simplify_json_schema function."""

    def test_simplify_ref_references(self):
        """Test that $ref references are inlined."""
        schema = {
            "$defs": {
                "Project": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                    },
                }
            },
            "type": "object",
            "properties": {
                "project": {"$ref": "#/$defs/Project"},
            },
        }

        result = simplify_json_schema(schema)

        # $defs should be removed
        assert "$defs" not in result
        # $ref should be resolved
        assert "$ref" not in result.get("properties", {}).get("project", {})
        # The referenced definition should be inlined
        assert result["properties"]["project"]["type"] == "object"
        assert "id" in result["properties"]["project"]["properties"]
        assert "name" in result["properties"]["project"]["properties"]

    def test_simplify_anyof_null_pattern(self):
        """Test that anyOf with null type is simplified."""
        schema = {
            "type": "object",
            "properties": {
                "name": {
                    "anyOf": [{"type": "string"}, {"type": "null"}]
                },
            },
        }

        result = simplify_json_schema(schema)

        # anyOf should be simplified to just the non-null type
        assert "anyOf" not in result["properties"]["name"]
        assert result["properties"]["name"]["type"] == "string"

    def test_simplify_oneof_null_pattern(self):
        """Test that oneOf with null type is simplified."""
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "oneOf": [{"type": "integer"}, {"type": "null"}]
                },
            },
        }

        result = simplify_json_schema(schema)

        # oneOf should be simplified to just the non-null type
        assert "oneOf" not in result["properties"]["value"]
        assert result["properties"]["value"]["type"] == "integer"

    def test_preserve_anyof_multiple_types(self):
        """Test that anyOf with multiple non-null types is preserved."""
        schema = {
            "type": "object",
            "properties": {
                "value": {
                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                },
            },
        }

        result = simplify_json_schema(schema)

        # anyOf should be preserved with multiple types
        assert "anyOf" in result["properties"]["value"]
        assert len(result["properties"]["value"]["anyOf"]) == 2

    def test_nested_ref_resolution(self):
        """Test that nested $ref references are resolved."""
        schema = {
            "$defs": {
                "Address": {
                    "type": "object",
                    "properties": {
                        "street": {"type": "string"},
                    },
                },
                "Person": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {"$ref": "#/$defs/Address"},
                    },
                },
            },
            "type": "object",
            "properties": {
                "person": {"$ref": "#/$defs/Person"},
            },
        }

        result = simplify_json_schema(schema)

        # All $refs should be resolved
        assert "$defs" not in result
        assert "$ref" not in str(result)
        # Nested structure should be preserved
        person = result["properties"]["person"]
        assert person["type"] == "object"
        assert "address" in person["properties"]
        assert person["properties"]["address"]["type"] == "object"

    def test_complex_pydantic_schema(self):
        """Test simplification of a complex Pydantic-generated schema."""
        schema = {
            "$defs": {
                "EntityType": {
                    "enum": ["Shot", "Asset", "Task"],
                    "type": "string",
                },
                "FilterItem": {
                    "type": "object",
                    "properties": {
                        "field": {"type": "string"},
                        "operator": {"type": "string"},
                        "value": {
                            "anyOf": [
                                {"type": "string"},
                                {"type": "integer"},
                                {"type": "null"},
                            ]
                        },
                    },
                },
            },
            "type": "object",
            "properties": {
                "entity_type": {"$ref": "#/$defs/EntityType"},
                "filters": {
                    "type": "array",
                    "items": {"$ref": "#/$defs/FilterItem"},
                },
                "limit": {
                    "anyOf": [{"type": "integer"}, {"type": "null"}],
                    "default": None,
                },
            },
            "required": ["entity_type", "filters"],
        }

        result = simplify_json_schema(schema)

        # $defs should be removed
        assert "$defs" not in result
        # entity_type should be inlined
        assert result["properties"]["entity_type"]["type"] == "string"
        assert "enum" in result["properties"]["entity_type"]
        # filters items should be inlined
        assert result["properties"]["filters"]["items"]["type"] == "object"
        # limit should be simplified
        assert result["properties"]["limit"]["type"] == "integer"
        # required should be preserved
        assert result["required"] == ["entity_type", "filters"]

    def test_empty_schema(self):
        """Test that empty schema is handled gracefully."""
        result = simplify_json_schema({})
        assert result == {}

    def test_non_dict_input(self):
        """Test that non-dict input is returned as-is."""
        assert simplify_json_schema("not a dict") == "not a dict"
        assert simplify_json_schema(123) == 123
        assert simplify_json_schema(None) is None

    def test_schema_without_defs(self):
        """Test that schema without $defs works correctly."""
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
            },
        }

        result = simplify_json_schema(schema)

        assert result == schema


class TestSimplifyToolSchemas:
    """Tests for simplify_tool_schemas function."""

    def test_simplify_tool_schemas_basic(self):
        """Test basic tool schema simplification."""
        tools = [
            {
                "name": "my_tool",
                "description": "A test tool",
                "inputSchema": {
                    "$defs": {
                        "MyModel": {"type": "object", "properties": {"id": {"type": "integer"}}}
                    },
                    "type": "object",
                    "properties": {
                        "data": {"$ref": "#/$defs/MyModel"},
                    },
                },
            }
        ]

        result = simplify_tool_schemas(tools)

        assert len(result) == 1
        assert result[0]["name"] == "my_tool"
        assert "$defs" not in result[0]["inputSchema"]
        assert result[0]["inputSchema"]["properties"]["data"]["type"] == "object"

    def test_simplify_tool_schemas_multiple_tools(self):
        """Test simplification of multiple tools."""
        tools = [
            {
                "name": "tool1",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "value": {"anyOf": [{"type": "string"}, {"type": "null"}]}
                    },
                },
            },
            {
                "name": "tool2",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "count": {"type": "integer"}
                    },
                },
            },
        ]

        result = simplify_tool_schemas(tools)

        assert len(result) == 2
        # First tool should have simplified anyOf
        assert result[0]["inputSchema"]["properties"]["value"]["type"] == "string"
        # Second tool should be unchanged
        assert result[1]["inputSchema"]["properties"]["count"]["type"] == "integer"

    def test_simplify_tool_schemas_preserves_other_fields(self):
        """Test that other tool fields are preserved."""
        tools = [
            {
                "name": "my_tool",
                "description": "A test tool",
                "custom_field": "custom_value",
                "inputSchema": {"type": "object"},
            }
        ]

        result = simplify_tool_schemas(tools)

        assert result[0]["name"] == "my_tool"
        assert result[0]["description"] == "A test tool"
        assert result[0]["custom_field"] == "custom_value"

    def test_simplify_tool_schemas_no_input_schema(self):
        """Test handling of tools without inputSchema."""
        tools = [
            {
                "name": "simple_tool",
                "description": "No schema",
            }
        ]

        result = simplify_tool_schemas(tools)

        assert len(result) == 1
        assert result[0]["name"] == "simple_tool"
        assert "inputSchema" not in result[0]

    def test_simplify_tool_schemas_empty_list(self):
        """Test handling of empty tool list."""
        result = simplify_tool_schemas([])
        assert result == []
