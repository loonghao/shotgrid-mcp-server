"""Tests for helper types Pydantic models."""

import pytest
from pydantic import ValidationError

from shotgrid_mcp_server.tools.helper_types import (
    DateRangeFilter,
    EntitiesResponse,
    EntityDict,
    ProjectDict,
    ProjectsResponse,
    TimeFilter,
    UserDict,
    UsersResponse,
)


def test_project_dict_valid():
    """Test ProjectDict with valid data."""
    project = ProjectDict(
        id=123,
        type="Project",
        name="Test Project",
        sg_status="Active",
    )

    assert project.id == 123
    assert project.type == "Project"
    assert project.name == "Test Project"
    assert project.sg_status == "Active"


def test_project_dict_extra_fields():
    """Test ProjectDict allows extra fields."""
    project = ProjectDict(
        id=123,
        type="Project",
        name="Test Project",
        custom_field="custom_value",  # Extra field
    )

    assert project.id == 123
    # Extra field should be allowed due to Config.extra = "allow"


def test_user_dict_valid():
    """Test UserDict with valid data."""
    user = UserDict(
        id=456,
        type="HumanUser",
        name="John Doe",
        login="jdoe",
        sg_status_list="act",
    )

    assert user.id == 456
    assert user.name == "John Doe"
    assert user.login == "jdoe"


def test_user_dict_optional_fields():
    """Test UserDict with optional fields."""
    user = UserDict(
        id=456,
        type="HumanUser",
        name="John Doe",
        login="jdoe",
        email="john@example.com",
        sg_status_list="act",
    )

    assert user.email == "john@example.com"


def test_entity_dict_valid():
    """Test EntityDict with valid data."""
    entity = EntityDict(
        id=789,
        type="Shot",
        code="SH001",
    )

    assert entity.id == 789
    assert entity.type == "Shot"
    assert entity.code == "SH001"


def test_time_filter_valid():
    """Test TimeFilter with valid data."""
    filter = TimeFilter(
        field="created_at",
        operator="in_last",
        count=7,
        unit="DAY",
    )

    assert filter.field == "created_at"
    assert filter.operator == "in_last"
    assert filter.count == 7
    assert filter.unit == "DAY"


def test_time_filter_invalid_operator():
    """Test TimeFilter rejects invalid operator."""
    with pytest.raises(ValidationError) as exc_info:
        TimeFilter(
            field="created_at",
            operator="invalid_operator",  # Invalid
            count=7,
            unit="DAY",
        )

    assert "operator" in str(exc_info.value)


def test_time_filter_invalid_count():
    """Test TimeFilter rejects invalid count."""
    with pytest.raises(ValidationError) as exc_info:
        TimeFilter(
            field="created_at",
            operator="in_last",
            count=0,  # Must be > 0
            unit="DAY",
        )

    assert "count" in str(exc_info.value)


def test_date_range_filter_valid():
    """Test DateRangeFilter with valid data."""
    filter = DateRangeFilter(
        field="created_at",
        start_date="2025-01-01",
        end_date="2025-01-31",
    )

    assert filter.field == "created_at"
    assert filter.start_date == "2025-01-01"
    assert filter.end_date == "2025-01-31"


def test_date_range_filter_with_additional_filters():
    """Test DateRangeFilter with additional filters."""
    filter = DateRangeFilter(
        field="created_at",
        start_date="2025-01-01",
        end_date="2025-01-31",
        additional_filters=[
            ["sg_status_list", "is", "ip"],
        ],
    )

    assert filter.additional_filters is not None
    assert len(filter.additional_filters) == 1


def test_projects_response_valid():
    """Test ProjectsResponse with valid data."""
    response = ProjectsResponse(
        projects=[
            ProjectDict(id=1, type="Project", name="Project 1"),
            ProjectDict(id=2, type="Project", name="Project 2"),
        ]
    )

    assert len(response.projects) == 2
    assert response.projects[0].name == "Project 1"


def test_users_response_valid():
    """Test UsersResponse with valid data."""
    response = UsersResponse(
        users=[
            UserDict(id=1, type="HumanUser", name="User 1", login="user1", sg_status_list="act"),
            UserDict(id=2, type="HumanUser", name="User 2", login="user2", sg_status_list="act"),
        ]
    )

    assert len(response.users) == 2
    assert response.users[0].login == "user1"


def test_entities_response_valid():
    """Test EntitiesResponse with valid data."""
    response = EntitiesResponse(
        entities=[
            EntityDict(id=1, type="Shot", code="SH001"),
            EntityDict(id=2, type="Shot", code="SH002"),
        ]
    )

    assert len(response.entities) == 2
    assert response.entities[0].code == "SH001"


def test_model_dump():
    """Test that models can be dumped to dict."""
    project = ProjectDict(
        id=123,
        type="Project",
        name="Test Project",
    )

    data = project.model_dump()

    assert isinstance(data, dict)
    assert data["id"] == 123
    assert data["name"] == "Test Project"


def test_model_json():
    """Test that models can be serialized to JSON."""
    project = ProjectDict(
        id=123,
        type="Project",
        name="Test Project",
    )

    json_str = project.model_dump_json()

    assert isinstance(json_str, str)
    assert "123" in json_str
    assert "Test Project" in json_str
