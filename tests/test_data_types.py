"""Tests for ShotGrid data type utilities."""

import datetime
import unittest

from shotgrid_mcp_server.data_types import (
    ShotGridTypes,
    convert_from_shotgrid_type,
    convert_to_shotgrid_type,
    format_entity_value,
    format_multi_entity_value,
    get_entity_field_types,
    get_field_type,
    is_entity_field,
    is_multi_entity_field,
)


class TestDataTypeConversion(unittest.TestCase):
    """Test data type conversion functions."""

    def test_convert_to_shotgrid_type_date(self):
        """Test conversion to ShotGrid date type."""
        # Test with datetime
        date = datetime.datetime(2023, 1, 1)
        result = convert_to_shotgrid_type(date, ShotGridTypes.DATE)
        self.assertEqual(result, "2023-01-01")

        # Test with string
        result = convert_to_shotgrid_type("2023-01-01", ShotGridTypes.DATE)
        self.assertEqual(result, "2023-01-01")

        # Test with None
        result = convert_to_shotgrid_type(None, ShotGridTypes.DATE)
        self.assertIsNone(result)

    def test_convert_to_shotgrid_type_checkbox(self):
        """Test conversion to ShotGrid checkbox type."""
        # Test with True
        result = convert_to_shotgrid_type(True, ShotGridTypes.CHECKBOX)
        self.assertTrue(result)

        # Test with False
        result = convert_to_shotgrid_type(False, ShotGridTypes.CHECKBOX)
        self.assertFalse(result)

        # Test with 1
        result = convert_to_shotgrid_type(1, ShotGridTypes.CHECKBOX)
        self.assertTrue(result)

        # Test with 0
        result = convert_to_shotgrid_type(0, ShotGridTypes.CHECKBOX)
        self.assertFalse(result)

        # Test with None
        result = convert_to_shotgrid_type(None, ShotGridTypes.CHECKBOX)
        self.assertIsNone(result)

    def test_convert_to_shotgrid_type_number(self):
        """Test conversion to ShotGrid number type."""
        # Test with int
        result = convert_to_shotgrid_type(123, ShotGridTypes.NUMBER)
        self.assertEqual(result, 123)

        # Test with string
        result = convert_to_shotgrid_type("123", ShotGridTypes.NUMBER)
        self.assertEqual(result, 123)

        # Test with invalid string
        result = convert_to_shotgrid_type("abc", ShotGridTypes.NUMBER)
        self.assertEqual(result, "abc")

        # Test with None
        result = convert_to_shotgrid_type(None, ShotGridTypes.NUMBER)
        self.assertIsNone(result)

    def test_convert_to_shotgrid_type_entity(self):
        """Test conversion to ShotGrid entity type."""
        # Test with entity dict
        entity = {"type": "Shot", "id": 123}
        result = convert_to_shotgrid_type(entity, ShotGridTypes.ENTITY)
        self.assertEqual(result, entity)

        # Test with None
        result = convert_to_shotgrid_type(None, ShotGridTypes.ENTITY)
        self.assertIsNone(result)

    def test_convert_from_shotgrid_type_date(self):
        """Test conversion from ShotGrid date type."""
        # Test with string
        result = convert_from_shotgrid_type("2023-01-01", ShotGridTypes.DATE)
        self.assertEqual(result, datetime.date(2023, 1, 1))

        # Test with invalid string
        result = convert_from_shotgrid_type("invalid", ShotGridTypes.DATE)
        self.assertEqual(result, "invalid")

        # Test with None
        result = convert_from_shotgrid_type(None, ShotGridTypes.DATE)
        self.assertIsNone(result)

    def test_convert_from_shotgrid_type_datetime(self):
        """Test conversion from ShotGrid datetime type."""
        # Test with ISO format string
        result = convert_from_shotgrid_type("2023-01-01T12:00:00", ShotGridTypes.DATE_TIME)
        self.assertEqual(result, datetime.datetime(2023, 1, 1, 12, 0, 0))

        # Test with other format string
        result = convert_from_shotgrid_type("2023-01-01 12:00:00", ShotGridTypes.DATE_TIME)
        self.assertEqual(result, datetime.datetime(2023, 1, 1, 12, 0, 0))

        # Test with invalid string
        result = convert_from_shotgrid_type("invalid", ShotGridTypes.DATE_TIME)
        self.assertEqual(result, "invalid")

        # Test with None
        result = convert_from_shotgrid_type(None, ShotGridTypes.DATE_TIME)
        self.assertIsNone(result)


class TestSchemaFunctions(unittest.TestCase):
    """Test schema-related functions."""

    def setUp(self):
        """Set up test data."""
        self.schema = {
            "Shot": {
                "fields": {
                    "code": {
                        "data_type": {"value": "text"},
                    },
                    "sg_sequence": {
                        "data_type": {"value": "entity"},
                        "properties": {
                            "valid_types": {"value": ["Sequence"]},
                        },
                    },
                    "assets": {
                        "data_type": {"value": "multi_entity"},
                        "properties": {
                            "valid_types": {"value": ["Asset"]},
                        },
                    },
                }
            }
        }

    def test_get_field_type(self):
        """Test get_field_type function."""
        # Test with valid field
        result = get_field_type(self.schema, "Shot", "code")
        self.assertEqual(result, "text")

        # Test with entity field
        result = get_field_type(self.schema, "Shot", "sg_sequence")
        self.assertEqual(result, "entity")

        # Test with multi-entity field
        result = get_field_type(self.schema, "Shot", "assets")
        self.assertEqual(result, "multi_entity")

        # Test with invalid field
        result = get_field_type(self.schema, "Shot", "invalid")
        self.assertIsNone(result)

        # Test with invalid entity type
        result = get_field_type(self.schema, "Invalid", "code")
        self.assertIsNone(result)

    def test_is_entity_field(self):
        """Test is_entity_field function."""
        # Test with entity field
        result = is_entity_field(self.schema, "Shot", "sg_sequence")
        self.assertTrue(result)

        # Test with non-entity field
        result = is_entity_field(self.schema, "Shot", "code")
        self.assertFalse(result)

        # Test with invalid field
        result = is_entity_field(self.schema, "Shot", "invalid")
        self.assertFalse(result)

    def test_is_multi_entity_field(self):
        """Test is_multi_entity_field function."""
        # Test with multi-entity field
        result = is_multi_entity_field(self.schema, "Shot", "assets")
        self.assertTrue(result)

        # Test with non-multi-entity field
        result = is_multi_entity_field(self.schema, "Shot", "code")
        self.assertFalse(result)

        # Test with invalid field
        result = is_multi_entity_field(self.schema, "Shot", "invalid")
        self.assertFalse(result)

    def test_get_entity_field_types(self):
        """Test get_entity_field_types function."""
        # Test with entity field
        result = get_entity_field_types(self.schema, "Shot", "sg_sequence")
        self.assertEqual(result, ["Sequence"])

        # Test with multi-entity field
        result = get_entity_field_types(self.schema, "Shot", "assets")
        self.assertEqual(result, ["Asset"])

        # Test with non-entity field
        result = get_entity_field_types(self.schema, "Shot", "code")
        self.assertEqual(result, [])

        # Test with invalid field
        result = get_entity_field_types(self.schema, "Shot", "invalid")
        self.assertEqual(result, [])


class TestEntityFormatting(unittest.TestCase):
    """Test entity formatting functions."""

    def test_format_entity_value(self):
        """Test format_entity_value function."""
        result = format_entity_value("Shot", 123)
        self.assertEqual(result, {"type": "Shot", "id": 123})

    def test_format_multi_entity_value(self):
        """Test format_multi_entity_value function."""
        entities = [
            {"type": "Shot", "id": 123, "name": "Shot 1"},
            {"type": "Shot", "id": 456, "name": "Shot 2"},
            {"invalid": "entity"},  # Should be filtered out
        ]
        result = format_multi_entity_value(entities)
        self.assertEqual(
            result,
            [
                {"type": "Shot", "id": 123},
                {"type": "Shot", "id": 456},
            ],
        )

        # Test with empty list
        result = format_multi_entity_value([])
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
