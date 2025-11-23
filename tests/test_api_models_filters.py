"""Test API models filter validation."""

import pytest

from shotgrid_mcp_server.api_models import SearchEntitiesRequest


class TestSearchEntitiesRequestFilterValidation:
    """Test SearchEntitiesRequest filter validation."""

    def test_valid_single_filter(self):
        """Test valid single filter."""
        request = SearchEntitiesRequest(
            entity_type="Task", filters=[["sg_status_list", "is", "ip"]], fields=["id", "content"]
        )
        assert request.filters == [["sg_status_list", "is", "ip"]]
        assert isinstance(request.filters[0], list)

    def test_valid_multiple_filters(self):
        """Test valid multiple filters."""
        request = SearchEntitiesRequest(
            entity_type="Shot",
            filters=[["sg_status_list", "in", ["wtg", "rdy", "ip"]], ["project", "is", {"type": "Project", "id": 123}]],
            fields=["code"],
        )
        assert len(request.filters) == 2
        assert request.filters[0] == ["sg_status_list", "in", ["wtg", "rdy", "ip"]]
        assert request.filters[1] == ["project", "is", {"type": "Project", "id": 123}]

    def test_valid_time_filter(self):
        """Test valid time-based filter."""
        request = SearchEntitiesRequest(
            entity_type="Version", filters=[["created_at", "in_last", 7, "DAY"]], fields=["code"]
        )
        assert request.filters == [["created_at", "in_last", 7, "DAY"]]

    def test_empty_filters(self):
        """Test empty filters list."""
        request = SearchEntitiesRequest(entity_type="Asset", filters=[], fields=["code"])
        assert request.filters == []

    def test_none_filters(self):
        """Test None filters (should default to empty list)."""
        request = SearchEntitiesRequest(entity_type="Asset", fields=["code"])
        assert request.filters == []

    def test_invalid_filter_not_list(self):
        """Test invalid filter that is not a list/tuple."""
        with pytest.raises(ValueError, match="Filter 0 must be a list/tuple"):
            SearchEntitiesRequest(entity_type="Task", filters=["invalid"], fields=["id"])

    def test_invalid_filter_too_short(self):
        """Test invalid filter with less than 3 elements."""
        with pytest.raises(ValueError, match="Filter 0 must have at least 3 elements"):
            SearchEntitiesRequest(entity_type="Task", filters=[["field", "operator"]], fields=["id"])

    def test_invalid_filter_dict_format(self):
        """Test that dict format is no longer accepted."""
        with pytest.raises(ValueError, match="Filter 0 must be a list/tuple"):
            SearchEntitiesRequest(
                entity_type="Task",
                filters=[{"field": "sg_status_list", "operator": "is", "value": "ip"}],
                fields=["id"],
            )

    def test_tuple_format_accepted(self):
        """Test that tuple format is accepted and converted to list."""
        request = SearchEntitiesRequest(entity_type="Task", filters=[("sg_status_list", "is", "ip")], fields=["id"])
        # Tuples are converted to lists during validation
        assert request.filters == [["sg_status_list", "is", "ip"]]

    def test_filter_with_entity_reference(self):
        """Test filter with entity reference."""
        request = SearchEntitiesRequest(
            entity_type="Task", filters=[["task_assignees", "is", {"type": "HumanUser", "id": 42}]], fields=["content"]
        )
        assert request.filters[0][2] == {"type": "HumanUser", "id": 42}

    def test_filter_with_list_value(self):
        """Test filter with list value (in operator)."""
        request = SearchEntitiesRequest(
            entity_type="Shot", filters=[["sg_status_list", "in", ["wtg", "rdy", "ip", "rev"]]], fields=["code"]
        )
        assert request.filters[0][2] == ["wtg", "rdy", "ip", "rev"]

    def test_complex_filters(self):
        """Test complex filters with multiple types."""
        request = SearchEntitiesRequest(
            entity_type="Task",
            filters=[
                ["sg_status_list", "in", ["wtg", "rdy", "ip"]],
                ["project", "is", {"type": "Project", "id": 123}],
                ["created_at", "in_last", 30, "DAY"],
                ["content", "contains", "animation"],
            ],
            fields=["id", "content", "sg_status_list"],
        )
        assert len(request.filters) == 4
        # Verify filters are preserved as-is
        assert all(isinstance(f, list) for f in request.filters)
