"""Type definitions for ShotGrid MCP server helper functions.

This module provides type definitions for helper functions in the ShotGrid MCP server.
All types are now Pydantic models for better validation and type safety.
"""

from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from shotgrid_mcp_server.custom_types import Filter


class ProjectDict(BaseModel):
    """ShotGrid project dictionary.

    Represents a ShotGrid project entity with common fields.
    """

    id: int = Field(..., description="Project ID")
    type: str = Field(..., description="Entity type (always 'Project')")
    name: str = Field(..., description="Project name")
    sg_status: Optional[str] = Field(None, description="Project status")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    updated_by: Optional[Dict[str, Union[int, str]]] = Field(None, description="User who last updated the project")

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields from ShotGrid


class UserDict(BaseModel):
    """ShotGrid user dictionary.

    Represents a ShotGrid user entity with common fields.
    """

    id: int = Field(..., description="User ID")
    type: str = Field(..., description="Entity type (always 'HumanUser')")
    name: str = Field(..., description="User's full name")
    login: str = Field(..., description="User's login name")
    email: Optional[str] = Field(None, description="User's email address")
    last_login: Optional[str] = Field(None, description="Last login timestamp")
    sg_status_list: str = Field(..., description="User status (act, dis, etc.)")

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields from ShotGrid


class EntityDict(BaseModel):
    """ShotGrid entity dictionary.

    Represents a generic ShotGrid entity with common fields.
    """

    id: int = Field(..., description="Entity ID")
    type: str = Field(..., description="Entity type")
    name: Optional[str] = Field(None, description="Entity name")
    code: Optional[str] = Field(None, description="Entity code")
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    updated_at: Optional[str] = Field(None, description="Last update timestamp")
    sg_status_list: Optional[str] = Field(None, description="Entity status")

    class Config:
        """Pydantic configuration."""

        extra = "allow"  # Allow additional fields from ShotGrid


# Define TimeUnit as a type alias
TimeUnit = Literal["DAY", "WEEK", "MONTH", "YEAR"]
"""ShotGrid time unit for relative date filters."""


class TimeFilter(BaseModel):
    """ShotGrid time filter for relative date queries.

    Example:
        >>> filter = TimeFilter(
        ...     field="created_at",
        ...     operator="in_last",
        ...     count=7,
        ...     unit="DAY"
        ... )
    """

    field: str = Field(..., description="Field name to filter on")
    operator: Literal["in_last", "not_in_last", "in_next", "not_in_next"] = Field(
        ..., description="Time filter operator"
    )
    count: int = Field(..., gt=0, description="Number of time units")
    unit: TimeUnit = Field(..., description="Time unit (DAY, WEEK, MONTH, YEAR)")


class DateRangeFilter(BaseModel):
    """ShotGrid date range filter.

    Example:
        >>> filter = DateRangeFilter(
        ...     field="created_at",
        ...     start_date="2025-01-01",
        ...     end_date="2025-01-31"
        ... )
    """

    field: str = Field(..., description="Field name to filter on")
    start_date: str = Field(..., description="Start date (YYYY-MM-DD)")
    end_date: str = Field(..., description="End date (YYYY-MM-DD)")
    additional_filters: Optional[List[Filter]] = Field(None, description="Additional filters to apply")


class ProjectsResponse(BaseModel):
    """Response for find_recently_active_projects."""

    projects: List[ProjectDict] = Field(..., description="List of projects")


class UsersResponse(BaseModel):
    """Response for find_active_users."""

    users: List[UserDict] = Field(..., description="List of users")


class EntitiesResponse(BaseModel):
    """Response for find_entities_by_date_range."""

    entities: List[EntityDict] = Field(..., description="List of entities")
