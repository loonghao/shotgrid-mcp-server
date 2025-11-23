"""Tests for API request models used by the ShotGrid MCP server."""

import pytest
from pydantic import ValidationError

from shotgrid_mcp_server.api_models import (
    AdvancedSearchRequest,
    BatchRequest,
    FindOneEntityRequest,
    SearchEntitiesRequest,
    _normalize_datetime_value,
)


def _make_base_advanced_search_kwargs(**overrides):
    """Helper to build minimal valid AdvancedSearchRequest kwargs."""

    data: dict = {"entity_type": "Shot"}
    data.update(overrides)
    return data


def test_advanced_search_filters_internal_style_preserved():
    """Internal style filters should pass through unchanged."""

    filters = [
        {"field": "code", "operator": "is", "value": "SHOT_001"},
    ]

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))

    assert request.filters == filters


def test_advanced_search_filters_rest_style_single_value_normalized():
    """REST-style filters with single value should be normalized to internal style."""

    filters = [
        {
            "path": "project",
            "relation": "is",
            "values": [{"type": "Project", "id": 1}],
        }
    ]

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))

    assert request.filters == [
        {
            "field": "project",
            "operator": "is",
            "value": {"type": "Project", "id": 1},
        }
    ]


def test_advanced_search_filters_rest_style_multi_value_preserved():
    """REST-style filters with multiple values should keep the list as value."""

    filters = [
        {
            "path": "sg_status_list",
            "relation": "in",
            "values": ["ip", "fin"],
        }
    ]

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))

    assert request.filters == [
        {
            "field": "sg_status_list",
            "operator": "in",
            "value": ["ip", "fin"],
        }
    ]


def test_advanced_search_filters_empty_allowed():
    """Empty filters list should be allowed and preserved."""

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[]))
    assert request.filters == []


def test_advanced_search_filters_invalid_type_raises():
    """Non-dict filter entries should surface as Pydantic validation errors.

    The ``filters`` field is typed as ``List[Dict[str, Any]]`` so Pydantic's
    core validation layer will reject non-dict values before the custom
    field validator runs.
    """

    with pytest.raises(ValidationError):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=["not-a-dict"]))


def test_advanced_search_filters_missing_required_keys_raises():
    """Filters missing required key combinations should raise a validation error."""

    # Missing both internal and REST-style key sets
    filters = [{"field": "code"}]

    with pytest.raises(ValueError, match=r"must have either \('field', 'operator', 'value'\)"):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))


def test_advanced_search_filter_operator_validation():
    """filter_operator must be either 'all' or 'any'."""

    # Valid values should pass
    AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="all"))
    AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="any"))

    # Invalid value should raise
    with pytest.raises(ValueError, match="filter_operator must be 'all' or 'any'"):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="invalid"))


def test_search_entities_list_format_filters():
    """Filters can be provided in list format: ["field", "operator", value]."""
    from shotgrid_mcp_server.api_models import SearchEntitiesRequest

    # Single filter in list format
    request = SearchEntitiesRequest(entity_type="Shot", filters=[["sg_status_list", "is", "ip"]])
    assert len(request.filters) == 1
    # Filters are now kept as-is (list format)
    assert request.filters[0][0] == "sg_status_list"
    assert request.filters[0][1] == "is"
    assert request.filters[0][2] == "ip"

    # Multiple filters in list format
    request = SearchEntitiesRequest(
        entity_type="Shot", filters=[["sg_status_list", "is", "ip"], ["project", "is", {"type": "Project", "id": 123}]]
    )
    assert len(request.filters) == 2
    # Filters are kept as-is (list format)
    assert request.filters[0][0] == "sg_status_list"
    assert request.filters[1][0] == "project"


def test_find_one_entity_list_format_filters():
    """FindOneEntityRequest accepts list format filters and converts to dict."""
    from shotgrid_mcp_server.api_models import FindOneEntityRequest

    request = FindOneEntityRequest(entity_type="Shot", filters=[["code", "is", "SH001"]])
    assert len(request.filters) == 1
    # FindOneEntityRequest converts list format to dict format
    assert request.filters[0]["field"] == "code"
    assert request.filters[0]["operator"] == "is"
    assert request.filters[0]["value"] == "SH001"


def test_advanced_search_list_format_filters():
    """AdvancedSearchRequest accepts list format filters."""

    request = AdvancedSearchRequest(entity_type="Shot", filters=[["sg_status_list", "is", "ip"]])
    assert len(request.filters) == 1
    # Advanced search filters are kept in dict format (different validator)
    assert request.filters[0]["field"] == "sg_status_list"
    assert request.filters[0]["operator"] == "is"
    assert request.filters[0]["value"] == "ip"


def test_advanced_search_related_fields_valid():
    """Valid related_fields mappings should be accepted as-is."""

    related_fields = {
        "project": ["name", "code"],
        "created_by": ["name", "email"],
    }

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], related_fields=related_fields))

    assert request.related_fields == related_fields


@pytest.mark.parametrize(
    "related_fields",
    [
        {123: ["name"]},
        {"project": "name"},
        {"project": [123]},
    ],
)
def test_advanced_search_related_fields_invalid_type_errors(related_fields):
    """Invalid related_fields types should raise Pydantic validation errors.

    Because ``related_fields`` is typed as ``Dict[str, List[str]]`` the core
    Pydantic validators will reject mismatched key/value types before the
    custom field validator runs.
    """

    with pytest.raises(ValidationError):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], related_fields=related_fields))


# Tests for field_name auto-correction


def test_search_entities_field_name_auto_corrected():
    """SearchEntitiesRequest now only accepts list/tuple format filters."""
    # Dict format is no longer supported - should raise validation error
    filters = [
        {"field_name": "archived", "operator": "is", "value": True},
    ]

    with pytest.raises(ValidationError, match="must be a list/tuple"):
        SearchEntitiesRequest(entity_type="Project", filters=filters)


def test_find_one_entity_field_name_auto_corrected():
    """FindOneEntityRequest should auto-correct 'field_name' to 'field'."""
    filters = [
        {"field_name": "code", "operator": "is", "value": "SHOT_001"},
    ]

    request = FindOneEntityRequest(entity_type="Shot", filters=filters)

    # Should be auto-corrected to use 'field'
    assert request.filters == [
        {"field": "code", "operator": "is", "value": "SHOT_001"},
    ]


def test_advanced_search_field_name_auto_corrected():
    """AdvancedSearchRequest should auto-correct 'field_name' to 'field'."""
    filters = [
        {"field_name": "sg_status_list", "operator": "in", "value": ["ip", "fin"]},
    ]

    request = AdvancedSearchRequest(entity_type="Shot", filters=filters)

    # Should be auto-corrected to use 'field'
    assert request.filters == [
        {"field": "sg_status_list", "operator": "in", "value": ["ip", "fin"]},
    ]


def test_search_entities_missing_field_helpful_error():
    """SearchEntitiesRequest should provide helpful error for dict format (no longer supported)."""
    filters = [
        {"operator": "is", "value": True},  # Dict format not supported
    ]

    with pytest.raises(ValidationError, match="must be a list/tuple"):
        SearchEntitiesRequest(entity_type="Project", filters=filters)


def test_find_one_entity_missing_field_helpful_error():
    """FindOneEntityRequest should provide helpful error when 'field' is missing."""
    filters = [
        {"operator": "is", "value": "SHOT_001"},  # Missing 'field' key
    ]

    with pytest.raises(ValueError, match="must have a 'field' key"):
        FindOneEntityRequest(entity_type="Shot", filters=filters)


def test_advanced_search_missing_field_helpful_error():
    """AdvancedSearchRequest should provide helpful error when required keys are missing."""
    filters = [
        {"operator": "is", "value": "SHOT_001"},  # Missing 'field' key
    ]

    with pytest.raises(ValueError, match="must have either"):
        AdvancedSearchRequest(entity_type="Shot", filters=filters)


# Additional validation tests for better coverage


def test_search_entities_order_validation_non_dict():
    """Test that order validation rejects non-dict items."""
    with pytest.raises(ValidationError) as exc_info:
        SearchEntitiesRequest(
            entity_type="Shot",
            filters=[],
            fields=["id"],
            order=["invalid_order"],  # Should be dict
        )

    error_message = str(exc_info.value)
    # Pydantic validates type before custom validator runs
    assert "Input should be a valid dictionary" in error_message or "Order item 0 must be a dictionary" in error_message


# Note: Order validation tests are skipped because Pydantic's type validation
# happens before custom validators, so these specific error messages won't be triggered
# The validation logic is still tested indirectly through successful requests


def test_batch_request_missing_request_type():
    """Test that batch validation requires request_type."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "entity_type": "Shot",
                    "data": {"code": "SH001"},
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "must have a 'request_type'" in error_message


def test_batch_request_invalid_request_type():
    """Test that batch validation rejects invalid request_type."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "request_type": "invalid",
                    "entity_type": "Shot",
                    "data": {"code": "SH001"},
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "invalid request_type" in error_message
    assert "Must be one of: create, update, delete" in error_message


def test_batch_request_missing_entity_type():
    """Test that batch validation requires entity_type."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "request_type": "create",
                    "data": {"code": "SH001"},
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "must have an 'entity_type'" in error_message


def test_batch_request_update_missing_entity_id():
    """Test that batch validation requires entity_id for update."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "request_type": "update",
                    "entity_type": "Shot",
                    "data": {"code": "SH001"},
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "must have an 'entity_id'" in error_message


def test_batch_request_delete_missing_entity_id():
    """Test that batch validation requires entity_id for delete."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "request_type": "delete",
                    "entity_type": "Shot",
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "must have an 'entity_id'" in error_message


def test_batch_request_create_missing_data():
    """Test that batch validation requires data for create."""
    with pytest.raises(ValidationError) as exc_info:
        BatchRequest(
            requests=[
                {
                    "request_type": "create",
                    "entity_type": "Shot",
                }
            ]
        )

    error_message = str(exc_info.value)
    assert "must have 'data'" in error_message


def test_advanced_search_filter_operator_validation():
    """Test that filter_operator validation rejects invalid values."""
    with pytest.raises(ValidationError) as exc_info:
        AdvancedSearchRequest(
            entity_type="Shot",
            filters=[],
            fields=["id"],
            filter_operator="invalid",
        )

    error_message = str(exc_info.value)
    assert "filter_operator must be 'all' or 'any'" in error_message


def test_find_one_entity_filter_operator_validation():
    """Test that FindOneEntityRequest validates filter_operator."""
    with pytest.raises(ValidationError) as exc_info:
        FindOneEntityRequest(
            entity_type="Shot",
            filters=[["id", "is", 1]],
            fields=["id"],
            filter_operator="invalid",
        )

    error_message = str(exc_info.value)
    assert "filter_operator must be 'all' or 'any'" in error_message


def test_advanced_search_related_fields_non_string_key():
    """Test that related_fields validation rejects non-string keys."""
    with pytest.raises(ValidationError) as exc_info:
        AdvancedSearchRequest(
            entity_type="Shot",
            filters=[],
            fields=["id"],
            related_fields={123: ["id"]},  # Non-string key
        )

    error_message = str(exc_info.value)
    # Pydantic validates type before custom validator runs
    assert "Input should be a valid string" in error_message or "Related field key must be a string" in error_message


def test_advanced_search_related_fields_non_list_value():
    """Test that related_fields validation requires list values."""
    with pytest.raises(ValidationError) as exc_info:
        AdvancedSearchRequest(
            entity_type="Shot",
            filters=[],
            fields=["id"],
            related_fields={"project": "id"},  # Should be list
        )

    error_message = str(exc_info.value)
    # Pydantic validates type before custom validator runs
    assert "Input should be a valid list" in error_message or "Related field value for 'project' must be a list" in error_message


def test_advanced_search_related_fields_non_string_item():
    """Test that related_fields validation requires string items in list."""
    with pytest.raises(ValidationError) as exc_info:
        AdvancedSearchRequest(
            entity_type="Shot",
            filters=[],
            fields=["id"],
            related_fields={"project": [123]},  # Non-string item
        )

    error_message = str(exc_info.value)
    # Pydantic validates type before custom validator runs
    assert "Input should be a valid string" in error_message or "Related field item for 'project' must be a string" in error_message


def test_find_one_entity_filter_missing_operator():
    """Test that FindOneEntityRequest filter validation requires operator."""
    with pytest.raises(ValidationError) as exc_info:
        FindOneEntityRequest(
            entity_type="Shot",
            filters=[{"field": "id", "value": 1}],  # Missing operator
            fields=["id"],
        )

    error_message = str(exc_info.value)
    assert "must have an 'operator' key" in error_message


def test_find_one_entity_filter_missing_value():
    """Test that FindOneEntityRequest filter validation requires value."""
    with pytest.raises(ValidationError) as exc_info:
        FindOneEntityRequest(
            entity_type="Shot",
            filters=[{"field": "id", "operator": "is"}],  # Missing value
            fields=["id"],
        )

    error_message = str(exc_info.value)
    assert "must have a 'value' key" in error_message


def test_find_one_entity_filter_short_list():
    """Test that FindOneEntityRequest filter validation rejects short lists."""
    with pytest.raises(ValidationError) as exc_info:
        FindOneEntityRequest(
            entity_type="Shot",
            filters=[["id", "is"]],  # Missing value
            fields=["id"],
        )

    error_message = str(exc_info.value)
    assert "must have at least 3 elements" in error_message


def test_find_one_entity_filter_invalid_type():
    """Test that FindOneEntityRequest filter validation rejects invalid types."""
    with pytest.raises(ValidationError) as exc_info:
        FindOneEntityRequest(
            entity_type="Shot",
            filters=["invalid"],  # Should be list or dict
            fields=["id"],
        )

    error_message = str(exc_info.value)
    assert "must be a list" in error_message or "must be a dict" in error_message


# Datetime normalization tests


def test_normalize_datetime_value_with_space_separator():
    """Test that datetime with space separator is converted to ISO 8601."""
    result = _normalize_datetime_value("2025-11-23 00:00:00")
    assert result == "2025-11-23T00:00:00Z"


def test_normalize_datetime_value_with_date_only():
    """Test that date-only string is converted to ISO 8601 with time."""
    result = _normalize_datetime_value("2025-11-23")
    assert result == "2025-11-23T00:00:00Z"


def test_normalize_datetime_value_already_iso8601():
    """Test that ISO 8601 datetime is not modified."""
    # With Z suffix
    result = _normalize_datetime_value("2025-11-23T00:00:00Z")
    assert result == "2025-11-23T00:00:00Z"

    # With timezone offset
    result = _normalize_datetime_value("2025-11-23T00:00:00+08:00")
    assert result == "2025-11-23T00:00:00+08:00"


def test_normalize_datetime_value_non_string():
    """Test that non-string values are returned unchanged."""
    assert _normalize_datetime_value(123) == 123
    assert _normalize_datetime_value(None) is None
    assert _normalize_datetime_value({"type": "Project", "id": 1}) == {"type": "Project", "id": 1}


def test_normalize_datetime_value_invalid_format():
    """Test that invalid datetime formats are returned unchanged."""
    result = _normalize_datetime_value("not a date")
    assert result == "not a date"


def test_advanced_search_filters_datetime_normalization():
    """Test that datetime values in filters are automatically normalized."""
    # List format with datetime
    filters = [
        ["updated_at", "greater_than", "2025-11-23 00:00:00"],
    ]

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))

    assert request.filters == [
        {
            "field": "updated_at",
            "operator": "greater_than",
            "value": "2025-11-23T00:00:00Z",
        }
    ]


def test_advanced_search_filters_dict_datetime_normalization():
    """Test that datetime values in dict-format filters are normalized."""
    # Dict format with datetime
    filters = [
        {"field": "updated_at", "operator": "greater_than", "value": "2025-11-23 00:00:00"},
    ]

    request = AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))

    assert request.filters == [
        {
            "field": "updated_at",
            "operator": "greater_than",
            "value": "2025-11-23T00:00:00Z",
        }
    ]


def test_search_entities_filters_datetime_normalization():
    """Test that SearchEntitiesRequest also normalizes datetime values."""
    filters = [
        ["created_at", "is", "2025-11-23"],
    ]

    request = SearchEntitiesRequest(entity_type="Task", filters=filters, fields=["id"])

    # SearchEntitiesRequest keeps list format but normalizes datetime values
    assert request.filters == [
        ["created_at", "is", "2025-11-23T00:00:00Z"],
    ]
