"""Schema validation for ShotGrid entities.

This module provides validation functionality for ShotGrid entity fields
using cached schema data.
"""

import logging
from typing import Any, Dict, List, Optional, Set

from shotgrid_mcp_server.schema_cache import SchemaCache, get_schema_cache

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validator for ShotGrid entity fields using schema data."""

    def __init__(self, cache: Optional[SchemaCache] = None):
        """Initialize the schema validator.

        Args:
            cache: Optional SchemaCache instance. If None, uses global cache.
        """
        self.cache = cache if cache is not None else get_schema_cache()

    def validate_fields(
        self,
        entity_type: str,
        data: Dict[str, Any],
        sg_connection: Any,
        check_required: bool = False,
    ) -> Dict[str, List[str]]:
        """Validate entity fields against schema.

        Args:
            entity_type: ShotGrid entity type (e.g., "Shot", "Asset")
            data: Dictionary of field names and values to validate
            sg_connection: ShotGrid connection to fetch schema if not cached
            check_required: Whether to check for required fields

        Returns:
            Dictionary with validation results:
            {
                "valid": List of valid field names,
                "invalid": List of invalid field names,
                "warnings": List of warning messages
            }
        """
        # Get schema from cache or fetch from ShotGrid
        schema = self.cache.get_entity_schema(entity_type)
        if schema is None:
            try:
                schema = sg_connection.schema_field_read(entity_type)
                self.cache.set_entity_schema(entity_type, schema)
                logger.debug(f"Fetched and cached schema for {entity_type}")
            except Exception as e:
                logger.warning(f"Failed to fetch schema for {entity_type}: {e}")
                # Return all fields as valid if schema fetch fails
                return {
                    "valid": list(data.keys()),
                    "invalid": [],
                    "warnings": [f"Could not validate fields: schema unavailable for {entity_type}"],
                }

        valid_fields: List[str] = []
        invalid_fields: List[str] = []
        warnings: List[str] = []

        # Validate each field
        for field_name, field_value in data.items():
            if field_name not in schema:
                invalid_fields.append(field_name)
                warnings.append(f"Unknown field '{field_name}' for {entity_type}")
            else:
                valid_fields.append(field_name)
                field_schema = schema[field_name]

                # Check if field is editable
                if not field_schema.get("editable", True):
                    warnings.append(f"Field '{field_name}' is not editable")

                # Validate data type
                data_type = (
                    field_schema.get("data_type", {}).get("value")
                    if isinstance(field_schema.get("data_type"), dict)
                    else field_schema.get("data_type")
                )

                if data_type and field_value is not None:
                    type_warning = self._validate_field_type(field_name, field_value, data_type)
                    if type_warning:
                        warnings.append(type_warning)

        # Check required fields if requested
        if check_required:
            required_fields = self._get_required_fields(schema)
            missing_required = set(required_fields) - set(data.keys())
            if missing_required:
                warnings.append(f"Missing required fields: {', '.join(missing_required)}")

        return {
            "valid": valid_fields,
            "invalid": invalid_fields,
            "warnings": warnings,
        }

    def _validate_field_type(self, field_name: str, value: Any, data_type: str) -> Optional[str]:
        """Validate field value type.

        Args:
            field_name: Field name
            value: Field value
            data_type: Expected data type from schema

        Returns:
            Warning message if validation fails, None otherwise
        """
        # Basic type validation
        type_checks = {
            "text": (str, "string"),
            "number": ((int, float), "number"),
            "float": ((int, float), "number"),
            "checkbox": (bool, "boolean"),
            "date": (str, "date string"),
            "date_time": (str, "datetime string"),
            "entity": (dict, "entity reference dict"),
            "multi_entity": (list, "list of entity references"),
            "list": (list, "list"),
            "status_list": (str, "status string"),
            "tag_list": (list, "list of tags"),
        }

        if data_type in type_checks:
            expected_type, type_name = type_checks[data_type]
            if not isinstance(value, expected_type):
                return f"Field '{field_name}' expects {type_name}, " f"got {type(value).__name__}"

        return None

    def _get_required_fields(self, schema: Dict[str, Any]) -> Set[str]:
        """Get list of required fields from schema.

        Args:
            schema: Entity schema dictionary

        Returns:
            Set of required field names
        """
        required = set()
        for field_name, field_schema in schema.items():
            # Check if field is mandatory
            if field_schema.get("mandatory", {}).get("value", False):
                required.add(field_name)
        return required


# Global validator instance
_global_validator: Optional[SchemaValidator] = None


def get_schema_validator() -> SchemaValidator:
    """Get the global schema validator instance.

    Returns:
        Global SchemaValidator instance
    """
    global _global_validator
    if _global_validator is None:
        _global_validator = SchemaValidator()
    return _global_validator
