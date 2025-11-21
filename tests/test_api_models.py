"""Tests for API request models used by the ShotGrid MCP server."""

import pytest
from pydantic import ValidationError

from shotgrid_mcp_server.api_models import (
    AdvancedSearchRequest,
    FindOneEntityRequest,
    SearchEntitiesRequest,
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
