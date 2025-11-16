"""Tests for API request models used by the ShotGrid MCP server."""

import pytest
from pydantic import ValidationError

from shotgrid_mcp_server.api_models import AdvancedSearchRequest


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

    with pytest.raises(ValueError, match="must have either \('field', 'operator', 'value'\)"):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=filters))


def test_advanced_search_filter_operator_validation():
    """filter_operator must be either 'and' or 'or'."""

    # Valid values should pass
    AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="and"))
    AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="or"))

    # Invalid value should raise
    with pytest.raises(ValueError, match="filter_operator must be 'and' or 'or'"):
        AdvancedSearchRequest(**_make_base_advanced_search_kwargs(filters=[], filter_operator="invalid"))


def test_advanced_search_related_fields_valid():
    """Valid related_fields mappings should be accepted as-is."""

    related_fields = {
        "project": ["name", "code"],
        "created_by": ["name", "email"],
    }

    request = AdvancedSearchRequest(
        **_make_base_advanced_search_kwargs(filters=[], related_fields=related_fields)
    )

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
        AdvancedSearchRequest(
            **_make_base_advanced_search_kwargs(filters=[], related_fields=related_fields)
        )

