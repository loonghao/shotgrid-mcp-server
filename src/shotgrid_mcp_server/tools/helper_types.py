"""Type definitions for ShotGrid MCP server helper functions.

This module provides type definitions for helper functions in the ShotGrid MCP server.
"""

from typing import Dict, List, Literal, Optional, TypedDict, Union

from shotgrid_mcp_server.custom_types import Filter


class ProjectDict(TypedDict, total=False):
    """ShotGrid project dictionary."""

    id: int
    type: str
    name: str
    sg_status: Optional[str]
    updated_at: Optional[str]
    updated_by: Optional[Dict[str, Union[int, str]]]


class UserDict(TypedDict, total=False):
    """ShotGrid user dictionary."""

    id: int
    type: str
    name: str
    login: str
    email: Optional[str]
    last_login: Optional[str]
    sg_status_list: str


class EntityDict(TypedDict, total=False):
    """ShotGrid entity dictionary."""

    id: int
    type: str
    name: Optional[str]
    code: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]
    sg_status_list: Optional[str]


# Define TimeUnit as a type alias instead of a class
TimeUnit = Literal["DAY", "WEEK", "MONTH", "YEAR"]
"""ShotGrid time unit."""


class TimeFilter(TypedDict):
    """ShotGrid time filter."""

    field: str
    operator: Literal["in_last", "not_in_last", "in_next", "not_in_next"]
    count: int
    unit: TimeUnit


class DateRangeFilter(TypedDict):
    """ShotGrid date range filter."""

    field: str
    start_date: str
    end_date: str
    additional_filters: Optional[List[Filter]]


class ProjectsResponse(TypedDict):
    """Response for find_recently_active_projects."""

    projects: List[ProjectDict]


class UsersResponse(TypedDict):
    """Response for find_active_users."""

    users: List[UserDict]


class EntitiesResponse(TypedDict):
    """Response for find_entities_by_date_range."""

    entities: List[EntityDict]
