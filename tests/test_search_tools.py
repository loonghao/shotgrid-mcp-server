"""Tests for search_tools module."""

import json
import datetime
import pytest
import pytest_asyncio
from fastmcp import FastMCP
from fastmcp.exceptions import ToolError
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.models import (
    EntitiesResponse,
    EntityDict,
    Filter,
    FilterOperator,
    ProjectDict,
    ProjectsResponse,
    TimeUnit,
    UserDict,
    UsersResponse,
)
from shotgrid_mcp_server.tools.search_tools import (
    register_search_tools,
    prepare_fields_with_related,
)


class TestSearchTools:
    """Tests for search tools."""

    @pytest_asyncio.fixture
    async def search_server(self, mock_sg: Shotgun) -> FastMCP:
        """Create a FastMCP server with search tools registered."""
        server = FastMCP("test-server")
        register_search_tools(server, mock_sg)
        return server

    def test_register_search_tools(self, mock_sg: Shotgun):
        """Test register_search_tools function."""
        # Create a server
        server = FastMCP("test-server")

        # Register search tools
        register_search_tools(server, mock_sg)

        # Verify server was created
        assert server is not None

    @pytest.mark.asyncio
    async def test_search_entities(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test search_entities tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Search Test Project",
                "code": "search_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "SEARCH_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create test filters
        filters = [
            {
                "field": "project",
                "operator": "is",
                "value": {"type": "Project", "id": project["id"]},
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "project"],
            }
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None
        # The response format is a list of dictionaries with 'text' key containing JSON
        # We don't need to parse it for this test

    @pytest.mark.asyncio
    async def test_search_entities_no_results(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test search_entities tool with no results."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Empty Project",
                "code": "empty_project",
                "sg_status": "Active",
            },
        )

        # Create test filters with non-matching criteria
        filters = [
            {
                "field": "code",
                "operator": "is",
                "value": "NON_EXISTENT_SHOT",
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": filters,
            }
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="MockgunExt has issues with order parameter as dict")
    async def test_search_entities_with_order(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test search_entities tool with ordering."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Order Test Project",
                "code": "order_test",
                "sg_status": "Active",
            },
        )

        # Create test shots with different creation dates
        shot1 = mock_sg.create(
            "Shot",
            {
                "code": "SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
                "created_at": datetime.datetime(2023, 1, 1),
            },
        )

        shot2 = mock_sg.create(
            "Shot",
            {
                "code": "SHOT_002",
                "project": {"type": "Project", "id": project["id"]},
                "created_at": datetime.datetime(2023, 2, 1),
            },
        )

        # Create test filters
        filters = [
            {
                "field": "project",
                "operator": "is",
                "value": {"type": "Project", "id": project["id"]},
            }
        ]

        # Call the tool with ascending order
        result_asc = await search_server._mcp_call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "created_at"],
                "order": [{"field_name": "created_at", "direction": "asc"}],
            }
        )

        # Verify result structure
        assert result_asc[0].text is not None

        # Call the tool with descending order
        result_desc = await search_server._mcp_call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "created_at"],
                "order": [{"field_name": "created_at", "direction": "desc"}],
            }
        )

        # Verify result structure
        assert result_desc[0].text is not None

    @pytest.mark.asyncio
    async def test_search_entities_with_limit(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test search_entities tool with limit."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Limit Test Project",
                "code": "limit_test",
                "sg_status": "Active",
            },
        )

        # Create multiple test shots
        for i in range(5):
            mock_sg.create(
                "Shot",
                {
                    "code": f"LIMIT_SHOT_{i+1:03d}",
                    "project": {"type": "Project", "id": project["id"]},
                },
            )

        # Create test filters
        filters = [
            {
                "field": "project",
                "operator": "is",
                "value": {"type": "Project", "id": project["id"]},
            }
        ]

        # Call the tool with limit
        result = await search_server._mcp_call_tool(
            "search_entities",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code"],
                "limit": 3,
            }
        )

        # Verify result structure
        assert result[0].text is not None


    @pytest.mark.asyncio
    async def test_sg_search_advanced_basic(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test sg.search.advanced tool with basic filters (internal format)."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Advanced Search Project",
                "code": "advanced_search",
                "sg_status": "Active",
            },
        )

        # Create test shot
        mock_sg.create(
            "Shot",
            {
                "code": "ADV_SEARCH_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create test filters using internal field/operator/value style
        filters = [
            {
                "field": "project",
                "operator": "is",
                "value": {"type": "Project", "id": project["id"]},
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "sg.search.advanced",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "project"],
            },
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    async def test_sg_search_advanced_rest_style_filters(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test sg.search.advanced tool with ShotGrid REST-style filters (path/relation/values)."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Advanced Search REST Project",
                "code": "advanced_search_rest",
                "sg_status": "Active",
            },
        )

        # Create test shot
        mock_sg.create(
            "Shot",
            {
                "code": "ADV_REST_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create test filters using REST-style path/relation/values
        filters = [
            {
                "path": "project",
                "relation": "is",
                "values": [
                    {"type": "Project", "id": project["id"]},
                ],
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "sg.search.advanced",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "project"],
            },
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    async def test_sg_search_advanced_with_time_filters_and_related_fields(
        self, search_server: FastMCP, mock_sg: Shotgun
    ):
        """Test sg.search.advanced with time_filters and related_fields.

        This exercises the time filter conversion path and the related_fields
        handling inside the advanced search implementation.
        """

        # Create project and user
        project = mock_sg.create(
            "Project",
            {
                "name": "Advanced Search Time Project",
                "code": "advanced_search_time",
                "sg_status": "Active",
            },
        )

        user = mock_sg.create(
            "HumanUser",
            {
                "login": "adv_user",
                "name": "Advanced User",
                "email": "adv@example.com",
                "sg_status_list": "act",
            },
        )

        # Create shot with explicit created_at so in_last filter will match
        mock_sg.create(
            "Shot",
            {
                "code": "ADV_TIME_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
                "created_at": datetime.datetime.now(),
            },
        )

        filters = [
            {
                "field": "project",
                "operator": "is",
                "value": {"type": "Project", "id": project["id"]},
            }
        ]

        time_filters = [
            {
                "field": "created_at",
                "operator": "in_last",
                "count": 365,
                "unit": TimeUnit.DAY.value,
            }
        ]

        related_fields = {"created_by": ["name", "email"]}

        result = await search_server._mcp_call_tool(
            "sg.search.advanced",
            {
                "entity_type": "Shot",
                "filters": filters,
                "time_filters": time_filters,
                "fields": ["code"],
                "related_fields": related_fields,
            },
        )

        # Verify result structure and that we got at least one entity back
        assert result
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].text is not None

    @pytest.mark.asyncio
    async def test_find_one_entity(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test find_one_entity tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Find One Test Project",
                "code": "find_one_test",
                "sg_status": "Active",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "FIND_ONE_SHOT",
                "project": {"type": "Project", "id": project["id"]},
            },
        )

        # Create test filters
        filters = [
            {
                "field": "id",
                "operator": "is",
                "value": shot["id"],
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "find_one_entity",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code", "project"],
            }
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    async def test_find_one_entity_not_found(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test find_one_entity tool with no results."""
        # Create test filters with non-matching criteria
        filters = [
            {
                "field": "id",
                "operator": "is",
                "value": 9999,  # Non-existent ID
            }
        ]

        # Call the tool
        result = await search_server._mcp_call_tool(
            "find_one_entity",
            {
                "entity_type": "Shot",
                "filters": filters,
            }
        )

        # Verify result
        assert result
        assert isinstance(result, list)
        assert len(result) == 1

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="MockgunExt has issues with order parameter as dict")
    async def test_find_recently_active_projects(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test find_recently_active_projects tool."""
        # Create test projects with different update dates
        recent_project = mock_sg.create(
            "Project",
            {
                "name": "Recent Project",
                "code": "recent_project",
                "sg_status": "Active",
                "updated_at": datetime.datetime.now(),
            },
        )

        old_project = mock_sg.create(
            "Project",
            {
                "name": "Old Project",
                "code": "old_project",
                "sg_status": "Active",
                "updated_at": datetime.datetime(2020, 1, 1),  # Old date
            },
        )

        # Call the tool with default days (90)
        result = await search_server._mcp_call_tool(
            "find_recently_active_projects",
            {}
        )

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="MockgunExt has issues with order parameter as dict")
    async def test_find_active_users(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test find_active_users tool.

        Note: This test uses 'updated_at' instead of 'last_login' because
        HumanUser entities don't have a 'last_login' field in ShotGrid.
        """
        # Create test users with different update dates
        recent_user = mock_sg.create(
            "HumanUser",
            {
                "name": "Recent User",
                "login": "recent_user",
                "email": "recent@example.com",
                "sg_status_list": "act",
                "updated_at": datetime.datetime.now(),
            },
        )

        old_user = mock_sg.create(
            "HumanUser",
            {
                "name": "Old User",
                "login": "old_user",
                "email": "old@example.com",
                "sg_status_list": "act",
                "updated_at": datetime.datetime(2020, 1, 1),  # Old date
            },
        )

        inactive_user = mock_sg.create(
            "HumanUser",
            {
                "name": "Inactive User",
                "login": "inactive_user",
                "email": "inactive@example.com",
                "sg_status_list": "dis",  # Disabled
                "updated_at": datetime.datetime.now(),
            },
        )

        # Call the tool with default days (30)
        result = await search_server._mcp_call_tool(
            "find_active_users",
            {}
        )

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="MockgunExt has issues with order parameter as dict")
    async def test_find_entities_by_date_range(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test find_entities_by_date_range tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Date Range Test Project",
                "code": "date_range_test",
                "sg_status": "Active",
            },
        )

        # Create test shots with different creation dates
        shot1 = mock_sg.create(
            "Shot",
            {
                "code": "DATE_SHOT_001",
                "project": {"type": "Project", "id": project["id"]},
                "created_at": datetime.datetime(2023, 1, 15),  # Within range
            },
        )

        shot2 = mock_sg.create(
            "Shot",
            {
                "code": "DATE_SHOT_002",
                "project": {"type": "Project", "id": project["id"]},
                "created_at": datetime.datetime(2023, 2, 15),  # Within range
            },
        )

        shot3 = mock_sg.create(
            "Shot",
            {
                "code": "DATE_SHOT_003",
                "project": {"type": "Project", "id": project["id"]},
                "created_at": datetime.datetime(2022, 12, 15),  # Outside range
            },
        )

        # Call the tool with date range
        result = await search_server._mcp_call_tool(
            "find_entities_by_date_range",
            {
                "entity_type": "Shot",
                "date_field": "created_at",
                "start_date": "2023-01-01",
                "end_date": "2023-03-01",
                "fields": ["code", "created_at"],
            }
        )

        # Verify result structure
        assert result[0].text is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="MockgunExt has issues with schema_field_read")
    async def test_search_entities_with_related(self, search_server: FastMCP, mock_sg: Shotgun):
        """Test search_entities_with_related tool."""
        # Create test project
        project = mock_sg.create(
            "Project",
            {
                "name": "Related Test Project",
                "code": "related_test",
                "sg_status": "Active",
            },
        )

        # Create test user
        user = mock_sg.create(
            "HumanUser",
            {
                "name": "Related Test User",
                "login": "related_test_user",
                "email": "related@example.com",
                "sg_status_list": "act",
            },
        )

        # Create test shot
        shot = mock_sg.create(
            "Shot",
            {
                "code": "RELATED_SHOT",
                "project": {"type": "Project", "id": project["id"]},
                "created_by": {"type": "HumanUser", "id": user["id"]},
            },
        )

        # Create test filters
        filters = [
            {
                "field": "id",
                "operator": "is",
                "value": shot["id"],
            }
        ]

        # Call the tool with related fields
        result = await search_server._mcp_call_tool(
            "search_entities_with_related",
            {
                "entity_type": "Shot",
                "filters": filters,
                "fields": ["code"],
                "related_fields": {
                    "project": ["name", "code"],
                    "created_by": ["name", "email"]
                },
            }
        )

        # Verify result structure
        assert result[0].text is not None

    def test_prepare_fields_with_related(self, mock_sg: Shotgun):
        """Test prepare_fields_with_related function."""
        # Mock the schema_field_read method to return field info
        def mock_schema_field_read(entity_type, field_name):
            if field_name == "project":
                return {
                    "properties": {
                        "valid_types": {
                            "value": ["Project"]
                        }
                    }
                }
            elif field_name == "created_by":
                return {
                    "properties": {
                        "valid_types": {
                            "value": ["HumanUser"]
                        }
                    }
                }
            return None

        # Replace the schema_field_read method with our mock
        original_schema_field_read = mock_sg.schema_field_read
        mock_sg.schema_field_read = mock_schema_field_read

        try:
            # Test with basic fields
            basic_fields = ["code", "id", "created_at"]
            result = prepare_fields_with_related(mock_sg, "Shot", basic_fields, None)
            assert set(result) == set(basic_fields)

            # Test with related fields
            related_fields = {
                "project": ["name", "code"],
                "created_by": ["name", "email"]
            }
            result = prepare_fields_with_related(mock_sg, "Shot", basic_fields, related_fields)

            # Verify all fields are included
            assert "code" in result
            assert "id" in result
            assert "created_at" in result

            # Check for dot notation fields
            assert any(f.startswith("project.") and f.endswith(".name") for f in result)
            assert any(f.startswith("project.") and f.endswith(".code") for f in result)
            assert any(f.startswith("created_by.") and f.endswith(".name") for f in result)
            assert any(f.startswith("created_by.") and f.endswith(".email") for f in result)
        finally:
            # Restore the original method
            mock_sg.schema_field_read = original_schema_field_read
