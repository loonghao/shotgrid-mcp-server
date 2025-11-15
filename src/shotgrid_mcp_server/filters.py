"""ShotGrid filter utilities.

This module provides utilities for working with ShotGrid filters,
making it easier to create, validate, and process filters for API queries.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Tuple, Union

from shotgrid_mcp_server.custom_types import Filter

logger = logging.getLogger(__name__)


# Define constants for filter operators
class TimeUnit:
    """Constants for time units used in time-related filters."""

    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    YEAR = "YEAR"


class FilterBuilder:
    """Helper class for building ShotGrid filters."""

    @staticmethod
    def is_field(field: str, value: Any) -> Filter:
        """Create an 'is' filter.

        Args:
            field: Field name to filter on
            value: Value to match

        Returns:
            Filter: [field, "is", value]
        """
        return [field, "is", value]

    @staticmethod
    def is_not_field(field: str, value: Any) -> Filter:
        """Create an 'is_not' filter.

        Args:
            field: Field name to filter on
            value: Value to not match

        Returns:
            Filter: [field, "is_not", value]
        """
        return [field, "is_not", value]

    @staticmethod
    def contains(field: str, value: str) -> Filter:
        """Create a 'contains' filter.

        Args:
            field: Field name to filter on
            value: Substring to search for

        Returns:
            Filter: [field, "contains", value]
        """
        return [field, "contains", value]

    @staticmethod
    def not_contains(field: str, value: str) -> Filter:
        """Create a 'not_contains' filter.

        Args:
            field: Field name to filter on
            value: Substring to exclude

        Returns:
            Filter: [field, "not_contains", value]
        """
        return [field, "not_contains", value]

    @staticmethod
    def starts_with(field: str, value: str) -> Filter:
        """Create a 'starts_with' filter.

        Args:
            field: Field name to filter on
            value: Prefix to match

        Returns:
            Filter: [field, "starts_with", value]
        """
        return [field, "starts_with", value]

    @staticmethod
    def ends_with(field: str, value: str) -> Filter:
        """Create a 'ends_with' filter.

        Args:
            field: Field name to filter on
            value: Suffix to match

        Returns:
            Filter: [field, "ends_with", value]
        """
        return [field, "ends_with", value]

    @staticmethod
    def greater_than(field: str, value: Any) -> Filter:
        """Create a 'greater_than' filter.

        Args:
            field: Field name to filter on
            value: Value to compare against

        Returns:
            Filter: [field, "greater_than", value]
        """
        return [field, "greater_than", value]

    @staticmethod
    def less_than(field: str, value: Any) -> Filter:
        """Create a 'less_than' filter.

        Args:
            field: Field name to filter on
            value: Value to compare against

        Returns:
            Filter: [field, "less_than", value]
        """
        return [field, "less_than", value]

    @staticmethod
    def between(field: str, min_value: Any, max_value: Any) -> Filter:
        """Create a 'between' filter.

        Args:
            field: Field name to filter on
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)

        Returns:
            Filter: [field, "between", [min_value, max_value]]
        """
        return [field, "between", [min_value, max_value]]

    @staticmethod
    def in_list(field: str, values: List[Any]) -> Filter:
        """Create an 'in' filter.

        Args:
            field: Field name to filter on
            values: List of values to match

        Returns:
            Filter: [field, "in", values]
        """
        return [field, "in", values]

    @staticmethod
    def not_in_list(field: str, values: List[Any]) -> Filter:
        """Create a 'not_in' filter.

        Args:
            field: Field name to filter on
            values: List of values to exclude

        Returns:
            Filter: [field, "not_in", values]
        """
        return [field, "not_in", values]

    @staticmethod
    def in_last(field: str, count: int, unit: str) -> Filter:
        """Create an 'in_last' filter.

        Args:
            field: Field name to filter on
            count: Number of time units
            unit: Time unit (DAY, WEEK, MONTH, YEAR)

        Returns:
            Filter: [field, "in_last", [count, unit]]
        """
        return [field, "in_last", [count, unit]]

    @staticmethod
    def in_next(field: str, count: int, unit: str) -> Filter:
        """Create an 'in_next' filter.

        Args:
            field: Field name to filter on
            count: Number of time units
            unit: Time unit (DAY, WEEK, MONTH, YEAR)

        Returns:
            Filter: [field, "in_next", [count, unit]]
        """
        return [field, "in_next", [count, unit]]

    @staticmethod
    def in_calendar_day(field: str) -> Filter:
        """Create an 'in_calendar_day' filter.

        Args:
            field: Field name to filter on

        Returns:
            Filter: [field, "in_calendar_day", None]
        """
        return [field, "in_calendar_day", None]

    @staticmethod
    def in_calendar_week(field: str) -> Filter:
        """Create an 'in_calendar_week' filter.

        Args:
            field: Field name to filter on

        Returns:
            Filter: [field, "in_calendar_week", None]
        """
        return [field, "in_calendar_week", None]

    @staticmethod
    def in_calendar_month(field: str) -> Filter:
        """Create an 'in_calendar_month' filter.

        Args:
            field: Field name to filter on

        Returns:
            Filter: [field, "in_calendar_month", None]
        """
        return [field, "in_calendar_month", None]

    @staticmethod
    def in_calendar_year(field: str) -> Filter:
        """Create an 'in_calendar_year' filter.

        Args:
            field: Field name to filter on

        Returns:
            Filter: [field, "in_calendar_year", None]
        """
        return [field, "in_calendar_year", None]

    @staticmethod
    def type_is(field: str, entity_type: str) -> Filter:
        """Create a 'type_is' filter for entity fields.

        Args:
            field: Field name to filter on
            entity_type: Entity type to match

        Returns:
            Filter: [field, "type_is", entity_type]
        """
        return [field, "type_is", entity_type]

    @staticmethod
    def type_is_not(field: str, entity_type: str) -> Filter:
        """Create a 'type_is_not' filter for entity fields.

        Args:
            field: Field name to filter on
            entity_type: Entity type to exclude

        Returns:
            Filter: [field, "type_is_not", entity_type]
        """
        return [field, "type_is_not", entity_type]

    @staticmethod
    def name_contains(field: str, name: str) -> Filter:
        """Create a 'name_contains' filter for entity fields.

        Args:
            field: Field name to filter on
            name: Name substring to match

        Returns:
            Filter: [field, "name_contains", name]
        """
        return [field, "name_contains", name]

    @staticmethod
    def name_not_contains(field: str, name: str) -> Filter:
        """Create a 'name_not_contains' filter for entity fields.

        Args:
            field: Field name to filter on
            name: Name substring to exclude

        Returns:
            Filter: [field, "name_not_contains", name]
        """
        return [field, "name_not_contains", name]

    @staticmethod
    def name_is(field: str, name: str) -> Filter:
        """Create a 'name_is' filter for entity fields.

        Args:
            field: Field name to filter on
            name: Name to match exactly

        Returns:
            Filter: [field, "name_is", name]
        """
        return [field, "name_is", name]

    @staticmethod
    def today(field: str) -> Filter:
        """Create a filter for field matching today's date.

        Args:
            field: Date field name to filter on

        Returns:
            Filter: [field, "is", today's date]
        """
        return [field, "is", datetime.now().strftime("%Y-%m-%d")]

    @staticmethod
    def yesterday(field: str) -> Filter:
        """Create a filter for field matching yesterday's date.

        Args:
            field: Date field name to filter on

        Returns:
            Filter: [field, "is", yesterday's date]
        """
        return [field, "is", (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")]

    @staticmethod
    def tomorrow(field: str) -> Filter:
        """Create a filter for field matching tomorrow's date.

        Args:
            field: Date field name to filter on

        Returns:
            Filter: [field, "is", tomorrow's date]
        """
        return [field, "is", (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")]

    @staticmethod
    def in_project(project_id: int) -> Filter:
        """Create a filter for entities in a specific project.

        Args:
            project_id: Project ID

        Returns:
            Filter: ["project", "is", {"type": "Project", "id": project_id}]
        """
        return ["project", "is", {"type": "Project", "id": project_id}]

    @staticmethod
    def by_user(user_id: int) -> Filter:
        """Create a filter for entities created by a specific user.

        Args:
            user_id: User ID

        Returns:
            Filter: ["created_by", "is", {"type": "HumanUser", "id": user_id}]
        """
        return ["created_by", "is", {"type": "HumanUser", "id": user_id}]

    @staticmethod
    def assigned_to(user_id: int) -> Filter:
        """Create a filter for tasks assigned to a specific user.

        Args:
            user_id: User ID

        Returns:
            Filter: ["task_assignees", "is", {"type": "HumanUser", "id": user_id}]
        """
        return ["task_assignees", "is", {"type": "HumanUser", "id": user_id}]


def _validate_filter_structure(filter_item: Any, index: int) -> List[str]:
    """Validate the basic structure of a filter.

    Args:
        filter_item: Filter to validate
        index: Index of the filter in the list (for error messages)

    Returns:
        List of error messages
    """
    errors = []

    if not isinstance(filter_item, list) or len(filter_item) != 3:
        errors.append(f"Filter {index + 1} must be a list with exactly 3 elements [field, operator, value]")

    return errors


def _validate_filter_field(field: Any, index: int) -> List[str]:
    """Validate the field part of a filter.

    Args:
        field: Field to validate
        index: Index of the filter in the list (for error messages)

    Returns:
        List of error messages
    """
    errors = []

    if not isinstance(field, str):
        errors.append(f"Filter {index + 1}: Field must be a string, got {type(field).__name__}")

    return errors


def _validate_filter_operator(operator: Any, index: int) -> List[str]:
    """Validate the operator part of a filter.

    Args:
        operator: Operator to validate
        index: Index of the filter in the list (for error messages)

    Returns:
        List of error messages
    """
    errors = []

    valid_operators = [
        "is",
        "is_not",
        "less_than",
        "greater_than",
        "contains",
        "not_contains",
        "starts_with",
        "ends_with",
        "between",
        "not_between",
        "in",
        "not_in",
        "in_last",
        "not_in_last",
        "in_next",
        "not_in_next",
        "in_calendar_day",
        "in_calendar_week",
        "in_calendar_month",
        "in_calendar_year",
        "type_is",
        "type_is_not",
        "name_contains",
        "name_not_contains",
        "name_is",
    ]

    if not isinstance(operator, str) or operator not in valid_operators:
        errors.append(
            f"Filter {index + 1}: Invalid operator '{operator}'. Valid operators are: {', '.join(valid_operators)}"
        )

    return errors


def _validate_time_filter_value(value: Any, index: int) -> List[str]:
    """Validate a time filter value.

    Args:
        value: Value to validate
        index: Index of the filter in the list (for error messages)

    Returns:
        List of error messages
    """
    errors = []

    if isinstance(value, str):
        # Check if string has the format "number unit"
        if " " in value:
            try:
                count_str, unit = value.split(" ", 1)
                count = int(count_str)

                # Map user-friendly unit names to ShotGrid format
                unit_map = {
                    "day": "DAY",
                    "days": "DAY",
                    "week": "WEEK",
                    "weeks": "WEEK",
                    "month": "MONTH",
                    "months": "MONTH",
                    "year": "YEAR",
                    "years": "YEAR",
                }

                if unit.lower() not in unit_map:
                    errors.append(
                        f"Filter {index + 1}: Invalid time unit '{unit}'. Valid units are: day(s), week(s), month(s), year(s)"
                    )
            except (ValueError, TypeError):
                errors.append(
                    f"Filter {index + 1}: Time filter string value must be in format 'number unit', e.g. '30 days'"
                )
        else:
            errors.append(
                f"Filter {index + 1}: Time filter string value must be in format 'number unit', e.g. '30 days'"
            )
    elif isinstance(value, list) and len(value) == 2:
        # Check if it's already in ShotGrid format [number, "UNIT"]
        count, unit = value
        if not isinstance(count, int) or not isinstance(unit, str):
            errors.append(f"Filter {index + 1}: Time filter value must be [number, 'UNIT'] or 'number unit'")

        valid_units = ["DAY", "WEEK", "MONTH", "YEAR"]
        if unit not in valid_units:
            errors.append(f"Filter {index + 1}: Invalid time unit '{unit}'. Valid units are: {', '.join(valid_units)}")
    else:
        errors.append(f"Filter {index + 1}: Time filter value must be [number, 'UNIT'] or 'number unit'")

    return errors


def _validate_between_filter_value(value: Any, index: int) -> List[str]:
    """Validate a between filter value.

    Args:
        value: Value to validate
        index: Index of the filter in the list (for error messages)

    Returns:
        List of error messages
    """
    errors = []

    if not isinstance(value, list) or len(value) != 2:
        errors.append(f"Filter {index + 1}: Between filter value must be a list with exactly 2 elements [min, max]")

    return errors


def validate_filters(filters: List[Filter]) -> List[str]:
    """Validate filter format and values.

    Args:
        filters: List of filters to validate.

    Returns:
        List[str]: List of validation error messages. Empty list if all filters are valid.
    """
    errors = []

    for i, filter_item in enumerate(filters):
        # Check basic structure
        structure_errors = _validate_filter_structure(filter_item, i)
        if structure_errors:
            errors.extend(structure_errors)
            continue

        field, operator, value = filter_item

        # Check field is a string
        errors.extend(_validate_filter_field(field, i))

        # Check operator is valid
        errors.extend(_validate_filter_operator(operator, i))

        # Check time-related filter values
        if operator in ["in_last", "not_in_last", "in_next", "not_in_next"]:
            errors.extend(_validate_time_filter_value(value, i))

        # Check between filter values
        if operator in ["between", "not_between"]:
            errors.extend(_validate_between_filter_value(value, i))

    return errors


def _process_time_filter_value(value: Any) -> Any:
    """Process a time filter value.

    Args:
        value: Value to process

    Returns:
        Processed value
    """
    # ShotGrid expects format [number, "UNIT"]
    if isinstance(value, str) and " " in value:
        try:
            count_str, unit = value.split(" ", 1)
            count = int(count_str)

            # Map user-friendly unit names to ShotGrid format
            unit_map = {
                "day": "DAY",
                "days": "DAY",
                "week": "WEEK",
                "weeks": "WEEK",
                "month": "MONTH",
                "months": "MONTH",
                "year": "YEAR",
                "years": "YEAR",
            }

            if unit.lower() in unit_map:
                logger.debug("Converting time filter: %s %s to [%s, %s]", count, unit, count, unit_map[unit.lower()])
                return [count, unit_map[unit.lower()]]
        except (ValueError, TypeError) as e:
            logger.warning("Failed to parse time filter value '%s': %s", value, str(e))
            # Keep original value if parsing fails

    return value


def _process_special_keyword(value: str) -> Any:
    """Process a special date keyword starting with $.

    Args:
        value: Special date keyword to process

    Returns:
        Processed date value or original value if not a recognized keyword
    """
    today = datetime.now()

    if value == "$today":
        return today.strftime("%Y-%m-%d")
    elif value == "$yesterday":
        return (today - timedelta(days=1)).strftime("%Y-%m-%d")
    elif value == "$tomorrow":
        return (today + timedelta(days=1)).strftime("%Y-%m-%d")
    elif value == "$this_week":
        # Start of current week (Monday)
        start_of_week = today - timedelta(days=today.weekday())
        return start_of_week.strftime("%Y-%m-%d")
    elif value == "$this_month":
        # Start of current month
        return today.replace(day=1).strftime("%Y-%m-%d")
    elif value == "$this_year":
        # Start of current year
        return today.replace(month=1, day=1).strftime("%Y-%m-%d")
    elif value == "$next_week":
        # Start of next week
        days_until_next_monday = 7 - today.weekday()
        next_monday = today + timedelta(days=days_until_next_monday)
        return next_monday.strftime("%Y-%m-%d")
    elif value == "$next_month":
        # Start of next month
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        return next_month.strftime("%Y-%m-%d")

    # Not a recognized keyword
    return value


def _try_parse_date_string(value: str) -> Any:
    """Try to parse a string as a date using various formats.

    Args:
        value: String to parse as date

    Returns:
        Parsed date in ISO format or original value if parsing fails
    """
    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",  # ISO format: 2023-01-31
        "%m/%d/%Y",  # US format: 01/31/2023
        "%d/%m/%Y",  # European format: 31/01/2023
        "%Y/%m/%d",  # Alternative ISO: 2023/01/31
        "%d-%m-%Y",  # European with dashes: 31-01-2023
        "%m-%d-%Y",  # US with dashes: 01-31-2023
    ]

    try:
        for date_format in date_formats:
            try:
                parsed_date = datetime.strptime(value, date_format)
                return parsed_date.strftime("%Y-%m-%d")
            except ValueError:
                continue
    except Exception as e:
        logger.debug("Failed to parse date value '%s': %s", value, str(e))

    return value


def _process_special_date_value(value: Any) -> Any:
    """Process a special date value.

    Args:
        value: Value to process

    Returns:
        Processed value
    """
    if isinstance(value, str):
        # Handle special date keywords
        if value.startswith("$"):
            return _process_special_keyword(value)

        # Try to parse common date formats
        return _try_parse_date_string(value)

    return value


def process_filters(filters: List[Filter]) -> List[Tuple[str, str, Any]]:
    """Process filters to handle special values and time-related filters.

    This function enhances filter processing by:
    1. Converting user-friendly time strings (e.g., "3 months") to ShotGrid format ([3, "MONTH"])
    2. Handling special values like $today, $yesterday, $tomorrow
    3. Validating filter formats

    Args:
        filters: List of filters to process.

    Returns:
        List[Filter]: Processed filters.

    Raises:
        ValueError: If filters contain invalid format or values.
    """
    # Validate filters first
    errors = validate_filters(filters)
    if errors:
        error_msg = "\n".join(errors)
        logger.error("Filter validation errors: %s", error_msg)
        raise ValueError(f"Invalid filters: {error_msg}")

    processed_filters = []

    for field, operator, value in filters:
        # Handle time-related operators
        if operator in ["in_last", "not_in_last", "in_next", "not_in_next"]:
            value = _process_time_filter_value(value)
        else:
            # Handle special date values
            value = _process_special_date_value(value)

        processed_filters.append([field, operator, value])

    return processed_filters  # type: ignore[return-value]


def create_date_filter(field: str, operator: str, date_value: Union[str, datetime, timedelta]) -> Filter:
    """Create a date filter with proper formatting.

    Args:
        field: Field name to filter on
        operator: Filter operator
        date_value: Date value as string, datetime, or timedelta

    Returns:
        Filter: Properly formatted date filter
    """
    # Convert datetime to string format
    if hasattr(date_value, "strftime"):
        # Handle datetime and date objects
        date_value = date_value.strftime("%Y-%m-%d")
    # Handle timedelta (relative to today)
    elif hasattr(date_value, "days") and hasattr(date_value, "seconds"):
        # This is likely a timedelta
        date_value = (datetime.now() + date_value).strftime("%Y-%m-%d")

    return [field, operator, date_value]


def build_date_filter(
    field: str, operator: str, date_value: Union[str, datetime, date, timedelta, None] = None
) -> Filter:
    """Build a date filter with proper formatting.

    This function handles various date formats and special values:
    - datetime objects are converted to ISO format
    - date objects are converted to ISO format
    - timedelta objects are applied to today's date
    - strings are processed for special values like $today
    - None defaults to today's date

    Args:
        field: Field name to filter on
        operator: Filter operator (is, is_not, greater_than, less_than, between, etc.)
        date_value: Date value as string, datetime, date, timedelta, or None (defaults to today)

    Returns:
        Filter: Properly formatted date filter

    Examples:
        >>> build_date_filter("created_at", "is", "$today")
        >>> build_date_filter("due_date", "greater_than", datetime.now())
        >>> build_date_filter("start_date", "less_than", timedelta(days=7))
    """
    # Default to today if no date provided
    if date_value is None:
        date_value = datetime.now()

    # Convert datetime to string format
    if isinstance(date_value, datetime):
        formatted_date = date_value.strftime("%Y-%m-%d")
    # Convert date to string format
    elif isinstance(date_value, date):
        formatted_date = date_value.strftime("%Y-%m-%d")
    # Handle timedelta (relative to today)
    elif isinstance(date_value, timedelta):
        formatted_date = (datetime.now() + date_value).strftime("%Y-%m-%d")
    # Process string values
    elif isinstance(date_value, str):
        # Process special values like $today
        formatted_date = _process_special_date_value(date_value)
    else:
        # Use as-is for other types
        formatted_date = date_value

    return [field, operator, formatted_date]


def combine_filters(filters: List[Filter], operator: str = "and") -> Dict[str, Any]:
    """Combine multiple filters with a logical operator.

    Args:
        filters: List of filters to combine
        operator: Logical operator, either "and" or "or"

    Returns:
        Dict with filter_operator and filters keys

    Raises:
        ValueError: If operator is not "and" or "or"
    """
    if operator not in ["and", "or"]:
        raise ValueError(f"Invalid filter operator: {operator}. Must be 'and' or 'or'")

    return {"filters": process_filters(filters), "filter_operator": operator}
