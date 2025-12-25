"""Tests for entity reference normalization utilities."""

import pytest

from shotgrid_mcp_server.utils import (
    FIELD_TO_ENTITY_TYPE,
    infer_entity_type_from_field_name,
    normalize_batch_request,
    normalize_data_dict,
    normalize_entity_reference,
    normalize_filter_value,
    normalize_filters,
    normalize_grouping,
)


class TestInferEntityTypeFromFieldName:
    """Tests for infer_entity_type_from_field_name function."""

    def test_known_field_names(self):
        """Test inference for known field names."""
        assert infer_entity_type_from_field_name("project") == "Project"
        assert infer_entity_type_from_field_name("shot") == "Shot"
        assert infer_entity_type_from_field_name("asset") == "Asset"
        assert infer_entity_type_from_field_name("task") == "Task"
        assert infer_entity_type_from_field_name("sequence") == "Sequence"
        assert infer_entity_type_from_field_name("version") == "Version"
        assert infer_entity_type_from_field_name("user") == "HumanUser"
        assert infer_entity_type_from_field_name("created_by") == "HumanUser"
        assert infer_entity_type_from_field_name("assigned_to") == "HumanUser"

    def test_sg_prefixed_field_names(self):
        """Test inference for sg_ prefixed field names."""
        assert infer_entity_type_from_field_name("sg_project") == "Project"
        assert infer_entity_type_from_field_name("sg_shot") == "Shot"
        assert infer_entity_type_from_field_name("sg_asset") == "Asset"
        assert infer_entity_type_from_field_name("sg_task") == "Task"
        assert infer_entity_type_from_field_name("sg_sequence") == "Sequence"
        assert infer_entity_type_from_field_name("sg_version") == "Version"
        assert infer_entity_type_from_field_name("sg_user") == "HumanUser"
        assert infer_entity_type_from_field_name("sg_assigned_to") == "HumanUser"

    def test_case_insensitive(self):
        """Test that inference is case insensitive."""
        assert infer_entity_type_from_field_name("Project") == "Project"
        assert infer_entity_type_from_field_name("PROJECT") == "Project"
        assert infer_entity_type_from_field_name("SHOT") == "Shot"

    def test_dot_notation(self):
        """Test inference for dot notation field names."""
        assert infer_entity_type_from_field_name("project.Project.id") == "Project"
        assert infer_entity_type_from_field_name("shot.Shot.code") == "Shot"

    def test_unknown_field_names(self):
        """Test inference for unknown field names (uses title case)."""
        assert infer_entity_type_from_field_name("custom_field") == "CustomField"
        assert infer_entity_type_from_field_name("my_entity") == "MyEntity"


class TestNormalizeEntityReference:
    """Tests for normalize_entity_reference function."""

    def test_integer_to_dict(self):
        """Test converting integer ID to dict format."""
        result = normalize_entity_reference(70, "project")
        assert result == {"type": "Project", "id": 70}

    def test_integer_to_dict_various_fields(self):
        """Test converting integer ID for various field types."""
        assert normalize_entity_reference(123, "shot") == {"type": "Shot", "id": 123}
        assert normalize_entity_reference(456, "task") == {"type": "Task", "id": 456}
        assert normalize_entity_reference(789, "user") == {"type": "HumanUser", "id": 789}

    def test_dict_passthrough(self):
        """Test that dict values pass through unchanged."""
        entity_dict = {"type": "Project", "id": 70}
        result = normalize_entity_reference(entity_dict, "project")
        assert result == entity_dict

    def test_string_passthrough(self):
        """Test that string values pass through unchanged."""
        result = normalize_entity_reference("active", "status")
        assert result == "active"

    def test_none_passthrough(self):
        """Test that None values pass through unchanged."""
        result = normalize_entity_reference(None, "project")
        assert result is None

    def test_list_passthrough(self):
        """Test that list values pass through unchanged."""
        result = normalize_entity_reference([1, 2, 3], "some_field")
        assert result == [1, 2, 3]


class TestNormalizeFilterValue:
    """Tests for normalize_filter_value function."""

    def test_standard_filter_with_integer(self):
        """Test normalizing standard filter with integer entity ID."""
        filter_item = ["project", "is", 70]
        result = normalize_filter_value(filter_item)
        assert result == ["project", "is", {"type": "Project", "id": 70}]

    def test_standard_filter_with_dict(self):
        """Test that standard filter with dict passes through."""
        filter_item = ["project", "is", {"type": "Project", "id": 70}]
        result = normalize_filter_value(filter_item)
        assert result == filter_item

    def test_standard_filter_with_string(self):
        """Test that standard filter with string passes through."""
        filter_item = ["sg_status_list", "is", "ip"]
        result = normalize_filter_value(filter_item)
        assert result == filter_item

    def test_filter_with_in_operator(self):
        """Test normalizing filter with 'in' operator and list of integers."""
        filter_item = ["project", "in", [70, 71, 72]]
        result = normalize_filter_value(filter_item)
        assert result == [
            "project",
            "in",
            [
                {"type": "Project", "id": 70},
                {"type": "Project", "id": 71},
                {"type": "Project", "id": 72},
            ],
        ]

    def test_dict_format_filter(self):
        """Test normalizing dict format filter."""
        filter_item = {"project": 70}
        result = normalize_filter_value(filter_item)
        assert result == {"project": {"type": "Project", "id": 70}}

    def test_nested_filter_structure(self):
        """Test normalizing nested filter structure."""
        filter_item = {
            "filter_operator": "any",
            "filters": [["project", "is", 70], ["shot", "is", 123]],
        }
        result = normalize_filter_value(filter_item)
        assert result == {
            "filter_operator": "any",
            "filters": [
                ["project", "is", {"type": "Project", "id": 70}],
                ["shot", "is", {"type": "Shot", "id": 123}],
            ],
        }

    def test_dot_notation_field(self):
        """Test normalizing filter with dot notation field name."""
        filter_item = ["project.Project.id", "is", 70]
        result = normalize_filter_value(filter_item)
        assert result == ["project.Project.id", "is", {"type": "Project", "id": 70}]


class TestNormalizeFilters:
    """Tests for normalize_filters function."""

    def test_single_filter(self):
        """Test normalizing a single filter."""
        filters = [["project", "is", 70]]
        result = normalize_filters(filters)
        assert result == [["project", "is", {"type": "Project", "id": 70}]]

    def test_multiple_filters(self):
        """Test normalizing multiple filters."""
        filters = [["project", "is", 70], ["shot", "is", 123], ["sg_status_list", "is", "ip"]]
        result = normalize_filters(filters)
        assert result == [
            ["project", "is", {"type": "Project", "id": 70}],
            ["shot", "is", {"type": "Shot", "id": 123}],
            ["sg_status_list", "is", "ip"],
        ]

    def test_empty_filters(self):
        """Test normalizing empty filters list."""
        result = normalize_filters([])
        assert result == []

    def test_non_list_passthrough(self):
        """Test that non-list values pass through unchanged."""
        result = normalize_filters(None)
        assert result is None


class TestNormalizeGrouping:
    """Tests for normalize_grouping function."""

    def test_none_grouping(self):
        """Test that None grouping passes through."""
        result = normalize_grouping(None)
        assert result is None

    def test_empty_grouping(self):
        """Test that empty grouping passes through."""
        result = normalize_grouping([])
        assert result == []

    def test_standard_grouping(self):
        """Test normalizing standard grouping."""
        grouping = [{"field": "sg_status_list", "type": "exact", "direction": "asc"}]
        result = normalize_grouping(grouping)
        assert result == grouping

    def test_grouping_with_entity_value(self):
        """Test normalizing grouping with entity value."""
        grouping = [{"field": "project", "type": "exact", "project": 70}]
        result = normalize_grouping(grouping)
        assert result == [{"field": "project", "type": "exact", "project": {"type": "Project", "id": 70}}]


class TestNormalizeDataDict:
    """Tests for normalize_data_dict function."""

    def test_integer_entity_field(self):
        """Test normalizing integer entity field."""
        data = {"project": 70, "code": "SH001"}
        result = normalize_data_dict(data)
        assert result == {"project": {"type": "Project", "id": 70}, "code": "SH001"}

    def test_multiple_entity_fields(self):
        """Test normalizing multiple entity fields."""
        data = {"project": 70, "shot": 123, "code": "SH001"}
        result = normalize_data_dict(data)
        assert result == {
            "project": {"type": "Project", "id": 70},
            "shot": {"type": "Shot", "id": 123},
            "code": "SH001",
        }

    def test_dict_entity_passthrough(self):
        """Test that dict entity values pass through unchanged."""
        data = {"project": {"type": "Project", "id": 70}, "code": "SH001"}
        result = normalize_data_dict(data)
        assert result == data

    def test_non_entity_integer_passthrough(self):
        """Test that non-entity integer fields pass through unchanged."""
        data = {"frame_count": 100, "code": "SH001"}
        result = normalize_data_dict(data)
        assert result == data

    def test_multi_entity_field_with_integers(self):
        """Test normalizing multi-entity field with integer IDs."""
        data = {"project": [70, 71]}
        result = normalize_data_dict(data)
        assert result == {
            "project": [{"type": "Project", "id": 70}, {"type": "Project", "id": 71}]
        }

    def test_non_dict_passthrough(self):
        """Test that non-dict values pass through unchanged."""
        result = normalize_data_dict("not a dict")
        assert result == "not a dict"


class TestNormalizeBatchRequest:
    """Tests for normalize_batch_request function."""

    def test_create_request(self):
        """Test normalizing create batch request."""
        request = {
            "request_type": "create",
            "entity_type": "Shot",
            "data": {"project": 70, "code": "SH001"},
        }
        result = normalize_batch_request(request)
        assert result == {
            "request_type": "create",
            "entity_type": "Shot",
            "data": {"project": {"type": "Project", "id": 70}, "code": "SH001"},
        }

    def test_update_request(self):
        """Test normalizing update batch request."""
        request = {
            "request_type": "update",
            "entity_type": "Shot",
            "entity_id": 1234,
            "data": {"project": 70},
        }
        result = normalize_batch_request(request)
        assert result == {
            "request_type": "update",
            "entity_type": "Shot",
            "entity_id": 1234,
            "data": {"project": {"type": "Project", "id": 70}},
        }

    def test_delete_request_passthrough(self):
        """Test that delete request passes through unchanged."""
        request = {
            "request_type": "delete",
            "entity_type": "Shot",
            "entity_id": 1234,
        }
        result = normalize_batch_request(request)
        assert result == request

    def test_non_dict_passthrough(self):
        """Test that non-dict values pass through unchanged."""
        result = normalize_batch_request("not a dict")
        assert result == "not a dict"


class TestFieldToEntityTypeMapping:
    """Tests for FIELD_TO_ENTITY_TYPE mapping completeness."""

    def test_common_fields_mapped(self):
        """Test that common entity fields are mapped."""
        common_fields = [
            "project",
            "shot",
            "asset",
            "task",
            "sequence",
            "version",
            "user",
            "created_by",
            "updated_by",
            "assigned_to",
            "department",
            "step",
            "note",
            "playlist",
            "published_file",
            "group",
        ]
        for field in common_fields:
            assert field in FIELD_TO_ENTITY_TYPE, f"Field '{field}' should be in FIELD_TO_ENTITY_TYPE"

    def test_sg_prefixed_fields_mapped(self):
        """Test that sg_ prefixed fields are mapped."""
        sg_fields = [
            "sg_task",
            "sg_shot",
            "sg_asset",
            "sg_sequence",
            "sg_version",
            "sg_project",
            "sg_user",
            "sg_assigned_to",
            "sg_step",
            "sg_department",
            "sg_note",
            "sg_playlist",
            "sg_published_file",
            "sg_group",
        ]
        for field in sg_fields:
            assert field in FIELD_TO_ENTITY_TYPE, f"Field '{field}' should be in FIELD_TO_ENTITY_TYPE"
