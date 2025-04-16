"""Pydantic models for ShotGrid MCP server.

This module provides Pydantic models for ShotGrid API data types and filters.
"""

from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple, Union

from pydantic import BaseModel, Field, model_validator


class TimeUnit(str, Enum):
    """ShotGrid time unit."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"


class FilterOperator(str, Enum):
    """ShotGrid filter operators."""

    IS = "is"
    IS_NOT = "is_not"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    BETWEEN = "between"
    NOT_BETWEEN = "not_between"
    IN = "in"
    NOT_IN = "not_in"
    IN_LAST = "in_last"
    NOT_IN_LAST = "not_in_last"
    IN_NEXT = "in_next"
    NOT_IN_NEXT = "not_in_next"
    IN_CALENDAR_DAY = "in_calendar_day"
    IN_CALENDAR_WEEK = "in_calendar_week"
    IN_CALENDAR_MONTH = "in_calendar_month"
    IN_CALENDAR_YEAR = "in_calendar_year"
    TYPE_IS = "type_is"
    TYPE_IS_NOT = "type_is_not"
    NAME_CONTAINS = "name_contains"
    NAME_NOT_CONTAINS = "name_not_contains"
    NAME_IS = "name_is"


class ShotGridDataType(str, Enum):
    """ShotGrid data types."""

    ADDRESSING = "addressing"
    CHECKBOX = "checkbox"
    COLOR = "color"
    CURRENCY = "currency"
    DATE = "date"
    DATE_TIME = "date_time"
    DURATION = "duration"
    ENTITY = "entity"
    FLOAT = "float"
    FOOTAGE = "footage"
    IMAGE = "image"
    LIST = "list"
    MULTI_ENTITY = "multi_entity"
    NUMBER = "number"
    PASSWORD = "password"
    PERCENT = "percent"
    SERIALIZABLE = "serializable"
    STATUS_LIST = "status_list"
    TAG_LIST = "tag_list"
    TEXT = "text"
    TIMECODE = "timecode"
    URL = "url"


class EntityRef(BaseModel):
    """ShotGrid entity reference."""

    type: str
    id: int
    name: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields


class Filter(BaseModel):
    """ShotGrid filter model."""

    field: str
    operator: FilterOperator
    value: Any

    @model_validator(mode='after')
    def validate_time_filter(self):
        """Validate time filter values."""
        operator = self.operator
        value = self.value

        if operator in [
            FilterOperator.IN_LAST,
            FilterOperator.NOT_IN_LAST,
            FilterOperator.IN_NEXT,
            FilterOperator.NOT_IN_NEXT,
        ]:
            if isinstance(value, str) and " " in value:
                # Will be processed later
                pass
            elif isinstance(value, list) and len(value) == 2:
                count, unit = value
                if not isinstance(count, int):
                    raise ValueError(f"Time filter count must be an integer, got {type(count).__name__}")

                if unit not in [u.value for u in TimeUnit]:
                    raise ValueError(f"Invalid time unit: {unit}. Must be one of {[u.value for u in TimeUnit]}")
            else:
                raise ValueError("Time filter value must be [number, 'UNIT'] or 'number unit'")

        if operator in [FilterOperator.BETWEEN, FilterOperator.NOT_BETWEEN]:
            if not isinstance(value, list) or len(value) != 2:
                raise ValueError("Between filter value must be a list with exactly 2 elements [min, max]")

        return self

    def to_tuple(self) -> Tuple[str, str, Any]:
        """Convert to tuple format for ShotGrid API."""
        return (self.field, self.operator.value, self.value)

    @classmethod
    def from_tuple(cls, filter_tuple: Tuple[str, str, Any]) -> "Filter":
        """Create from tuple format."""
        field, operator, value = filter_tuple
        return cls(field=field, operator=operator, value=value)


class FilterList(BaseModel):
    """List of ShotGrid filters."""

    filters: List[Filter]
    filter_operator: Literal["and", "or"] = "and"


class TimeFilter(BaseModel):
    """ShotGrid time filter."""

    field: str
    operator: Literal["in_last", "not_in_last", "in_next", "not_in_next"]
    count: int = Field(..., gt=0)
    unit: TimeUnit

    def to_filter(self) -> Filter:
        """Convert to Filter model."""
        return Filter(
            field=self.field,
            operator=self.operator,
            value=[self.count, self.unit.value],
        )


class DateRangeFilter(BaseModel):
    """ShotGrid date range filter."""

    field: str
    start_date: str
    end_date: str
    additional_filters: Optional[List[Filter]] = None

    def to_filter(self) -> Filter:
        """Convert to Filter model."""
        return Filter(
            field=self.field,
            operator=FilterOperator.BETWEEN,
            value=[self.start_date, self.end_date],
        )


class ProjectDict(BaseModel):
    """ShotGrid project dictionary."""

    id: int
    type: str
    name: str
    sg_status: Optional[str] = None
    updated_at: Optional[str] = None
    updated_by: Optional[EntityRef] = None

    class Config:
        extra = "allow"  # Allow extra fields


class UserDict(BaseModel):
    """ShotGrid user dictionary."""

    id: int
    type: str
    name: str
    login: str
    email: Optional[str] = None
    last_login: Optional[str] = None
    sg_status_list: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields


class EntityDict(BaseModel):
    """ShotGrid entity dictionary."""

    id: int
    type: str
    name: Optional[str] = None
    code: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    sg_status_list: Optional[str] = None

    class Config:
        extra = "allow"  # Allow extra fields


class ProjectsResponse(BaseModel):
    """Response for find_recently_active_projects."""

    projects: List[ProjectDict]


class UsersResponse(BaseModel):
    """Response for find_active_users."""

    users: List[UserDict]


class EntitiesResponse(BaseModel):
    """Response for find_entities_by_date_range."""

    entities: List[EntityDict]


# Helper functions for filter creation
def create_is_filter(field: str, value: Any) -> Filter:
    """Create an 'is' filter."""
    return Filter(field=field, operator=FilterOperator.IS, value=value)


def create_contains_filter(field: str, value: str) -> Filter:
    """Create a 'contains' filter."""
    return Filter(field=field, operator=FilterOperator.CONTAINS, value=value)


def create_in_last_filter(field: str, count: int, unit: TimeUnit) -> Filter:
    """Create an 'in_last' filter."""
    return Filter(field=field, operator=FilterOperator.IN_LAST, value=[count, unit.value])


def create_in_next_filter(field: str, count: int, unit: TimeUnit) -> Filter:
    """Create an 'in_next' filter."""
    return Filter(field=field, operator=FilterOperator.IN_NEXT, value=[count, unit.value])


def create_between_filter(field: str, min_value: Any, max_value: Any) -> Filter:
    """Create a 'between' filter."""
    return Filter(field=field, operator=FilterOperator.BETWEEN, value=[min_value, max_value])


def create_date_filter(
    field: str, operator: FilterOperator, date_value: Union[str, datetime, date, timedelta]
) -> Filter:
    """Create a date filter with proper formatting."""
    # Convert datetime to string format
    if isinstance(date_value, datetime):
        date_value = date_value.strftime("%Y-%m-%d")
    # Convert date to string format
    elif isinstance(date_value, date):
        date_value = date_value.strftime("%Y-%m-%d")
    # Handle timedelta (relative to today)
    elif isinstance(date_value, timedelta):
        date_value = (datetime.now() + date_value).strftime("%Y-%m-%d")

    return Filter(field=field, operator=operator, value=date_value)


def create_today_filter(field: str) -> Filter:
    """Create a filter for field matching today's date."""
    return create_date_filter(field, FilterOperator.IS, datetime.now())


def create_yesterday_filter(field: str) -> Filter:
    """Create a filter for field matching yesterday's date."""
    return create_date_filter(field, FilterOperator.IS, datetime.now() - timedelta(days=1))


def create_tomorrow_filter(field: str) -> Filter:
    """Create a filter for field matching tomorrow's date."""
    return create_date_filter(field, FilterOperator.IS, datetime.now() + timedelta(days=1))


def create_in_project_filter(project_id: int) -> Filter:
    """Create a filter for entities in a specific project."""
    return Filter(
        field="project",
        operator=FilterOperator.IS,
        value={"type": "Project", "id": project_id},
    )


def create_by_user_filter(user_id: int) -> Filter:
    """Create a filter for entities created by a specific user."""
    return Filter(
        field="created_by",
        operator=FilterOperator.IS,
        value={"type": "HumanUser", "id": user_id},
    )


def create_assigned_to_filter(user_id: int) -> Filter:
    """Create a filter for tasks assigned to a specific user."""
    return Filter(
        field="task_assignees",
        operator=FilterOperator.IS,
        value={"type": "HumanUser", "id": user_id},
    )


def process_filters(filters: List[Union[Filter, Tuple[str, str, Any]]]) -> List[Tuple[str, str, Any]]:
    """Process filters to handle special values and time-related filters.

    Args:
        filters: List of filters to process.

    Returns:
        List of processed filters in tuple format.
    """
    processed_filters = []

    for filter_item in filters:
        # Convert tuple to Filter if needed
        if isinstance(filter_item, tuple):
            filter_item = Filter.from_tuple(filter_item)

        field = filter_item.field
        operator = filter_item.operator
        value = filter_item.value

        # Handle time-related operators
        if operator in [
            FilterOperator.IN_LAST,
            FilterOperator.NOT_IN_LAST,
            FilterOperator.IN_NEXT,
            FilterOperator.NOT_IN_NEXT,
        ]:
            # ShotGrid expects format [number, "UNIT"]
            if isinstance(value, str) and " " in value:
                try:
                    count_str, unit = value.split(" ", 1)
                    count = int(count_str)

                    # Map user-friendly unit names to ShotGrid format
                    unit_map = {
                        "day": TimeUnit.DAY.value,
                        "days": TimeUnit.DAY.value,
                        "week": TimeUnit.WEEK.value,
                        "weeks": TimeUnit.WEEK.value,
                        "month": TimeUnit.MONTH.value,
                        "months": TimeUnit.MONTH.value,
                        "year": TimeUnit.YEAR.value,
                        "years": TimeUnit.YEAR.value,
                    }

                    if unit.lower() in unit_map:
                        value = [count, unit_map[unit.lower()]]
                except (ValueError, TypeError):
                    # Keep original value if parsing fails
                    pass

        # Handle special date values
        elif isinstance(value, str) and value.startswith("$"):
            if value == "$today":
                value = datetime.now().strftime("%Y-%m-%d")
            elif value == "$yesterday":
                value = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
            elif value == "$tomorrow":
                value = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

        # Convert to tuple format for ShotGrid API
        processed_filters.append((field, operator.value if isinstance(operator, FilterOperator) else operator, value))

    return processed_filters
