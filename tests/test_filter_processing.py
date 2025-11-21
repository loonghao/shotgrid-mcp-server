"""Test end-to-end filter processing with shotgrid-query integration."""

from shotgrid_query import process_filters

from shotgrid_mcp_server.api_models import SearchEntitiesRequest


class TestFilterProcessingIntegration:
    """Test integration between SearchEntitiesRequest and shotgrid-query."""

    def test_simple_filter_processing(self):
        """Test simple filter goes through validation and processing."""
        # Step 1: Validate with SearchEntitiesRequest
        request = SearchEntitiesRequest(entity_type="Task", filters=[["sg_status_list", "is", "ip"]], fields=["id"])

        # Step 2: Process with shotgrid-query
        processed = process_filters(request.filters)

        # Verify: Should be converted to tuple
        assert len(processed) == 1
        assert processed[0] == ("sg_status_list", "is", "ip")
        assert isinstance(processed[0], tuple)

    def test_multiple_filters_processing(self):
        """Test multiple filters processing."""
        request = SearchEntitiesRequest(
            entity_type="Shot",
            filters=[["sg_status_list", "in", ["wtg", "rdy"]], ["project", "is", {"type": "Project", "id": 123}]],
            fields=["code"],
        )

        processed = process_filters(request.filters)

        assert len(processed) == 2
        assert processed[0] == ("sg_status_list", "in", ["wtg", "rdy"])
        assert processed[1] == ("project", "is", {"type": "Project", "id": 123})

    def test_time_filter_processing(self):
        """Test time-based filter processing."""
        request = SearchEntitiesRequest(
            entity_type="Version", filters=[["created_at", "in_last", [7, "DAY"]]], fields=["code"]
        )

        processed = process_filters(request.filters)

        assert len(processed) == 1
        assert processed[0] == ("created_at", "in_last", [7, "DAY"])

    def test_empty_filters_processing(self):
        """Test empty filters processing."""
        request = SearchEntitiesRequest(entity_type="Asset", filters=[], fields=["code"])

        processed = process_filters(request.filters)

        assert processed == []

    def test_complex_filters_processing(self):
        """Test complex filters with various operators."""
        request = SearchEntitiesRequest(
            entity_type="Task",
            filters=[
                ["sg_status_list", "in", ["wtg", "rdy", "ip", "rev"]],
                ["task_assignees", "is", {"type": "HumanUser", "id": 42}],
                ["due_date", "greater_than", "2025-01-01"],
                ["content", "contains", "animation"],
            ],
            fields=["id", "content"],
        )

        processed = process_filters(request.filters)

        assert len(processed) == 4
        # All should be tuples
        assert all(isinstance(f, tuple) for f in processed)
        # Verify values are preserved
        assert processed[0][2] == ["wtg", "rdy", "ip", "rev"]
        assert processed[1][2] == {"type": "HumanUser", "id": 42}
        assert processed[2][2] == "2025-01-01"
        assert processed[3][2] == "animation"

    def test_tuple_input_processing(self):
        """Test that tuple input is also accepted."""
        request = SearchEntitiesRequest(entity_type="Task", filters=[("sg_status_list", "is", "ip")], fields=["id"])

        processed = process_filters(request.filters)

        assert len(processed) == 1
        assert processed[0] == ("sg_status_list", "is", "ip")

    def test_filter_with_none_value(self):
        """Test filter with None value."""
        request = SearchEntitiesRequest(
            entity_type="Task", filters=[["task_assignees", "is", None]], fields=["content"]
        )

        processed = process_filters(request.filters)

        assert len(processed) == 1
        assert processed[0] == ("task_assignees", "is", None)

    def test_filter_with_boolean_value(self):
        """Test filter with boolean value."""
        request = SearchEntitiesRequest(entity_type="Asset", filters=[["sg_is_published", "is", True]], fields=["code"])

        processed = process_filters(request.filters)

        assert len(processed) == 1
        assert processed[0] == ("sg_is_published", "is", True)

    def test_filter_with_numeric_value(self):
        """Test filter with numeric value."""
        request = SearchEntitiesRequest(entity_type="Shot", filters=[["id", "greater_than", 1000]], fields=["code"])

        processed = process_filters(request.filters)

        assert len(processed) == 1
        assert processed[0] == ("id", "greater_than", 1000)
