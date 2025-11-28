"""Pydantic models for ShotGrid API requests.

This module provides Pydantic models for validating and standardizing ShotGrid API requests.
These models ensure that all parameters passed to the ShotGrid API are valid and properly formatted.

All models follow the official ShotGrid Python API conventions:
https://developers.shotgridsoftware.com/python-api/reference.html
"""

import re
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.models import TimeFilter


def _normalize_datetime_value(value: Any) -> Any:
    """Normalize datetime values to ISO 8601 format required by ShotGrid API.

    ShotGrid API requires datetime values in ISO 8601 format:
    - With timezone: "2025-11-23T00:00:00Z" or "2025-11-23T00:00:00+08:00"
    - Without timezone: "2025-11-23T00:00:00Z" (assumes UTC)

    This function converts common datetime formats to ISO 8601:
    - "2025-11-23 00:00:00" -> "2025-11-23T00:00:00Z"
    - "2025-11-23" -> "2025-11-23T00:00:00Z"

    Args:
        value: Value to normalize (can be string, datetime, or any other type)

    Returns:
        Normalized value in ISO 8601 format if it's a datetime string, otherwise unchanged
    """
    if not isinstance(value, str):
        return value

    # Pattern for datetime without timezone: "YYYY-MM-DD HH:MM:SS"
    datetime_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}$")
    # Pattern for date only: "YYYY-MM-DD"
    date_pattern = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    # If already in ISO 8601 format (contains 'T' or timezone), return as is
    if "T" in value or "+" in value or value.endswith("Z"):
        return value

    # Convert "YYYY-MM-DD HH:MM:SS" to "YYYY-MM-DDTHH:MM:SSZ"
    if datetime_pattern.match(value):
        return value.replace(" ", "T") + "Z"

    # Convert "YYYY-MM-DD" to "YYYY-MM-DDT00:00:00Z"
    if date_pattern.match(value):
        return value + "T00:00:00Z"

    return value


class BaseAPIRequest(BaseModel):
    """Base model for all ShotGrid API requests.

    All API request models inherit from this base class to ensure consistent
    validation and configuration across all ShotGrid API operations.
    """

    model_config = ConfigDict(extra="forbid")  # Prevent extra fields to catch typos early


class FindRequest(BaseAPIRequest):
    """Model for ShotGrid find() API requests.

    Find entities matching the given filters.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.find

    Example:
        >>> request = FindRequest(
        ...     entity_type="Shot",
        ...     filters=[["sg_status_list", "is", "ip"]],
        ...     fields=["code", "sg_status_list"],
        ...     order=[{"field_name": "code", "direction": "asc"}]
        ... )
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to find")
    filters: List[Any] = Field(..., description="List of filter conditions. Each filter is [field, operator, value]")
    fields: Optional[List[str]] = Field(
        None, description="List of field names to return. Defaults to ['id'] if not specified"
    )
    order: Optional[List[Dict[str, str]]] = Field(
        None, description="List of dicts with 'field_name' and 'direction' keys for sorting results"
    )
    filter_operator: Optional[Literal["all", "any"]] = Field(
        None, description="Operator to combine filters. 'all' = AND, 'any' = OR. Defaults to 'all'"
    )
    limit: Optional[int] = Field(
        None, description="Maximum number of entities to return. 0 or None returns all matches"
    )
    retired_only: bool = Field(False, description="If True, return only retired (deleted) entities")
    page: Optional[int] = Field(
        None, gt=0, description="Page number for pagination (1-based). Use with limit parameter"
    )
    include_archived_projects: bool = Field(True, description="If True, include entities from archived projects")
    additional_filter_presets: Optional[List[Dict[str, Any]]] = Field(
        None, description="Additional filter presets to apply (e.g., LATEST, CUT_SHOT_VERSIONS)"
    )

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        """Validate limit parameter."""
        if v is not None and v <= 0:
            raise ValueError("limit must be a positive integer")
        return v

    @field_validator("order")
    @classmethod
    def validate_order(cls, v):
        """Validate order parameter follows official API format.

        Official API expects: [{"field_name": "foo", "direction": "asc"}]
        """
        if v is None:
            return v

        for i, order_dict in enumerate(v):
            if not isinstance(order_dict, dict):
                raise ValueError(f"Order item {i} must be a dictionary")

            if "field_name" not in order_dict:
                raise ValueError(
                    f"Order item {i} must have 'field_name' key. " f"Available keys: {list(order_dict.keys())}"
                )

            if "direction" not in order_dict:
                raise ValueError(
                    f"Order item {i} must have 'direction' key. " f"Available keys: {list(order_dict.keys())}"
                )

            direction = order_dict["direction"]
            if direction not in ["asc", "desc"]:
                raise ValueError(f"Order item {i} direction must be 'asc' or 'desc', got '{direction}'")

        return v


class FindOneRequest(BaseAPIRequest):
    """Model for ShotGrid find_one() API requests.

    Shortcut for find() with limit=1 that returns a single result.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.find_one

    Example:
        >>> request = FindOneRequest(
        ...     entity_type="Asset",
        ...     filters=[["id", "is", 32]],
        ...     fields=["code", "sg_status_list"]
        ... )
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to find")
    filters: List[Any] = Field(..., description="List of filter conditions. Each filter is [field, operator, value]")
    fields: Optional[List[str]] = Field(
        None, description="List of field names to return. Defaults to ['id'] if not specified"
    )
    order: Optional[List[Dict[str, str]]] = Field(
        None, description="List of dicts with 'field_name' and 'direction' keys for sorting results"
    )
    filter_operator: Optional[Literal["all", "any"]] = Field(
        None, description="Operator to combine filters. 'all' = AND, 'any' = OR. Defaults to 'all'"
    )
    retired_only: bool = Field(False, description="If True, return only retired (deleted) entities")
    include_archived_projects: bool = Field(True, description="If True, include entities from archived projects")

    @field_validator("order")
    @classmethod
    def validate_order(cls, v):
        """Validate order parameter follows official API format."""
        if v is None:
            return v

        for i, order_dict in enumerate(v):
            if not isinstance(order_dict, dict):
                raise ValueError(f"Order item {i} must be a dictionary")

            if "field_name" not in order_dict:
                raise ValueError(
                    f"Order item {i} must have 'field_name' key. " f"Available keys: {list(order_dict.keys())}"
                )

            if "direction" not in order_dict:
                raise ValueError(
                    f"Order item {i} must have 'direction' key. " f"Available keys: {list(order_dict.keys())}"
                )

            direction = order_dict["direction"]
            if direction not in ["asc", "desc"]:
                raise ValueError(f"Order item {i} direction must be 'asc' or 'desc', got '{direction}'")

        return v


class CreateRequest(BaseAPIRequest):
    """Model for ShotGrid create() API requests.

    Create a new entity of the specified entity_type.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.create

    Example:
        >>> request = CreateRequest(
        ...     entity_type="Shot",
        ...     data={
        ...         "project": {"type": "Project", "id": 161},
        ...         "code": "001_100",
        ...         "sg_status_list": "ip"
        ...     },
        ...     return_fields=["code", "sg_status_list", "created_at"]
        ... )
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to create")
    data: Dict[str, Any] = Field(..., description="Dictionary of field names and values to set on the new entity")
    return_fields: Optional[List[str]] = Field(
        None, description="Additional fields to return. Always includes 'type', 'id', and fields from 'data'"
    )


class UpdateRequest(BaseAPIRequest):
    """Model for ShotGrid update() API requests.

    Update the specified entity with the supplied data.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.update

    Example:
        >>> request = UpdateRequest(
        ...     entity_type="Asset",
        ...     entity_id=55,
        ...     data={"sg_status_list": "rev"},
        ...     multi_entity_update_modes={"shots": "add"}
        ... )
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to update")
    entity_id: int = Field(..., gt=0, description="ID of the entity to update")
    data: Dict[str, Any] = Field(..., description="Dictionary of field names and values to update")
    multi_entity_update_modes: Optional[Dict[str, Literal["set", "add", "remove"]]] = Field(
        None, description="Update mode for multi-entity fields: 'set' (replace), 'add', or 'remove'"
    )


class DeleteRequest(BaseAPIRequest):
    """Model for ShotGrid delete() API requests.

    Retire (soft delete) the specified entity.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.delete

    Note:
        Entities are "retired" (soft deleted), not permanently deleted.
        They can be restored using revive().

    Example:
        >>> request = DeleteRequest(entity_type="Shot", entity_id=2557)
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to delete")
    entity_id: int = Field(..., gt=0, description="ID of the entity to delete")


class ReviveRequest(BaseAPIRequest):
    """Model for ShotGrid revive() API requests.

    Revive an entity that has previously been deleted (retired).

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.revive

    Example:
        >>> request = ReviveRequest(entity_type="Shot", entity_id=860)
    """

    entity_type: EntityType = Field(..., description="ShotGrid entity type to revive")
    entity_id: int = Field(..., gt=0, description="ID of the entity to revive")


class BatchRequest(BaseAPIRequest):
    """Model for ShotGrid batch() API requests.

    Make a batch request of several create(), update(), and delete() calls.
    All requests are performed within a transaction - either all complete or none do.

    Official API Reference:
    https://developers.shotgridsoftware.com/python-api/reference.html#shotgun.Shotgun.batch

    Example:
        >>> request = BatchRequest(
        ...     requests=[
        ...         {
        ...             "request_type": "create",
        ...             "entity_type": "Shot",
        ...             "data": {"code": "New Shot 1", "project": {"type": "Project", "id": 4}}
        ...         },
        ...         {
        ...             "request_type": "update",
        ...             "entity_type": "Shot",
        ...             "entity_id": 3624,
        ...             "data": {"code": "Changed 1"}
        ...         },
        ...         {
        ...             "request_type": "delete",
        ...             "entity_type": "Shot",
        ...             "entity_id": 3625
        ...         }
        ...     ]
        ... )
    """

    requests: List[Dict[str, Any]] = Field(
        ..., description="List of create/update/delete operations to perform atomically"
    )

    @model_validator(mode="after")
    def validate_batch_requests(self):
        """Validate batch requests follow official API format."""
        for i, request in enumerate(self.requests):
            if "request_type" not in request:
                raise ValueError(f"Batch request {i} must have a 'request_type'")

            request_type = request["request_type"]
            if request_type not in ["create", "update", "delete"]:
                raise ValueError(
                    f"Batch request {i} has invalid request_type: {request_type}. "
                    f"Must be one of: create, update, delete"
                )

            if "entity_type" not in request:
                raise ValueError(f"Batch request {i} must have an 'entity_type'")

            if request_type in ["update", "delete"] and "entity_id" not in request:
                raise ValueError(f"Batch request {i} of type '{request_type}' must have an 'entity_id'")

            if request_type in ["create", "update"] and "data" not in request:
                raise ValueError(f"Batch request {i} of type '{request_type}' must have 'data'")

        return self


class SummarizeRequest(BaseAPIRequest):
    """Model for ShotGrid summarize API requests."""

    entity_type: EntityType
    filters: List[Any]
    summary_fields: List[Dict[str, Any]]
    filter_operator: Optional[str] = Field(
        None,
        description="Logical operator for combining filters. Must be 'all' (AND logic) or 'any' (OR logic). Only used when filters is a complex filter dict with 'filters' key.",
    )
    grouping: Optional[List[Dict[str, Any]]] = None
    include_archived_projects: bool = True

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["all", "any"]:
            raise ValueError("filter_operator must be 'all' or 'any'")
        return v


class TextSearchRequest(BaseAPIRequest):
    """Model for ShotGrid text_search API requests."""

    text: str
    entity_types: List[EntityType]
    project_ids: Optional[List[int]] = None
    limit: Optional[int] = Field(None, gt=0)


class SchemaFieldReadRequest(BaseAPIRequest):
    """Model for ShotGrid schema_field_read API requests."""

    entity_type: EntityType
    field_name: Optional[str] = None


class UploadRequest(BaseAPIRequest):
    """Model for ShotGrid upload API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)
    path: str
    field_name: str = "sg_uploaded_movie"
    display_name: Optional[str] = None
    tag_list: Optional[List[str]] = None


class DownloadAttachmentRequest(BaseAPIRequest):
    """Model for ShotGrid download_attachment API requests."""

    attachment: Dict[str, Any]
    file_path: Optional[str] = None


class ActivityStreamReadRequest(BaseAPIRequest):
    """Model for ShotGrid activity_stream_read API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)
    limit: Optional[int] = Field(None, gt=0)
    max_id: Optional[int] = None
    min_id: Optional[int] = None


class FollowRequest(BaseAPIRequest):
    """Model for ShotGrid follow API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)
    user_id: Optional[int] = None


class FollowersRequest(BaseAPIRequest):
    """Model for ShotGrid followers API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)


class FollowingRequest(BaseAPIRequest):
    """Model for ShotGrid following API requests."""

    user_id: Optional[int] = None
    entity_type: Optional[EntityType] = None


class NoteThreadReadRequest(BaseAPIRequest):
    """Model for ShotGrid note_thread_read API requests."""

    note_id: int = Field(..., gt=0)


class SearchEntitiesRequest(BaseAPIRequest):
    """Model for search_entities API requests."""

    entity_type: EntityType
    filters: List[Any] = Field(default_factory=list)
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        None,
        description="Logical operator for combining filters. Must be 'all' (AND logic) or 'any' (OR logic). Only used when filters is a complex filter dict with 'filters' key.",
    )
    limit: Optional[int] = Field(None, gt=0)

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["all", "any"]:
            raise ValueError("filter_operator must be 'all' or 'any'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate filters parameter.

        Accepts list/tuple format: ["field", "operator", value]

        Auto-normalizes for AI model convenience:

        1. Time filters with 4 elements -> 3 elements (for specific operators):
           - Operators: "in_last", "not_in_last", "in_next", "not_in_next"
           - Format: ["field", "in_last", 1, "DAY"] -> ["field", "in_last", [1, "DAY"]]
           - Units: "HOUR", "DAY", "WEEK", "MONTH", "YEAR"

        2. Calendar operators (NO conversion needed - already 3 elements):
           - Operators: "in_calendar_day", "in_calendar_week", "in_calendar_month", "in_calendar_year"
           - Format: ["field", "in_calendar_day", 0] (0=today, 1=tomorrow, -1=yesterday)
           - These use integer offset, NOT [count, unit] format

        3. Datetime value normalization:
           - "2025-11-23" -> "2025-11-23T00:00:00Z"
           - "2025-11-23 14:30:00" -> "2025-11-23T14:30:00Z"
           - Applied to all filter values

        Note: Detailed validation is handled by shotgrid-query's process_filters().
        """
        # Allow empty filters list - ShotGrid API allows this to return all entities
        if not v:
            return v

        normalized_filters = []
        TIME_OPERATORS = ["in_last", "not_in_last", "in_next", "not_in_next"]

        # Basic structure validation and normalization
        for i, filter_item in enumerate(v):
            if not isinstance(filter_item, (list, tuple)):
                raise ValueError(
                    f"Filter {i} must be a list/tuple [field, operator, value], got {type(filter_item).__name__}"
                )
            if len(filter_item) < 3:
                raise ValueError(
                    f"Filter {i} must have at least 3 elements [field, operator, value], got {len(filter_item)}"
                )

            filter_list = list(filter_item)

            # Auto-normalize 4-element time filters to 3-element format for AI convenience
            # ["field", "in_last", 1, "DAY"] -> ["field", "in_last", [1, "DAY"]]
            if len(filter_list) == 4 and filter_list[1] in TIME_OPERATORS:
                filter_list = [filter_list[0], filter_list[1], [filter_list[2], filter_list[3]]]

            # Auto-normalize datetime values in the filter
            filter_list[2] = _normalize_datetime_value(filter_list[2])
            normalized_filters.append(filter_list)

        return normalized_filters


class SearchEntitiesWithRelatedRequest(SearchEntitiesRequest):
    """Model for search_entities_with_related API requests."""

    related_fields: Optional[Dict[str, List[str]]] = None

    @field_validator("related_fields")
    @classmethod
    def validate_related_fields(cls, v):
        """Validate related_fields parameter."""
        if v is not None:
            for field, related_field_list in v.items():
                if not isinstance(field, str):
                    raise ValueError(f"Related field key must be a string, got {type(field).__name__}")

                if not isinstance(related_field_list, list):
                    raise ValueError(
                        f"Related field value for '{field}' must be a list, got {type(related_field_list).__name__}"
                    )

                for related_field in related_field_list:
                    if not isinstance(related_field, str):
                        raise ValueError(
                            f"Related field item for '{field}' must be a string, got {type(related_field).__name__}"
                        )

        return v


class FindOneEntityRequest(BaseAPIRequest):
    """Model for find_one_entity API requests."""

    entity_type: EntityType
    filters: List[Any] = Field(default_factory=list)
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        None,
        description="Logical operator for combining filters. Must be 'all' (AND logic) or 'any' (OR logic). Only used when filters is a complex filter dict with 'filters' key.",
    )

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["all", "any"]:
            raise ValueError("filter_operator must be 'all' or 'any'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate and normalize filters parameter.

        Accepts both list format and dict format:
        - List format: ["field", "operator", value]
        - Dict format: {"field": "...", "operator": "...", "value": ...}
        """
        # For find_one, we should have at least one filter to identify the entity
        # But ShotGrid API technically allows empty filters to return the first entity
        if not v:
            return v

        normalized_filters = []
        for i, filter_item in enumerate(v):
            # Handle list/tuple format: ["field", "operator", value]
            if isinstance(filter_item, (list, tuple)):
                if len(filter_item) < 3:
                    raise ValueError(
                        f"Filter {i} in list format must have at least 3 elements [field, operator, value], got {len(filter_item)}"
                    )
                normalized_filters.append(
                    {
                        "field": filter_item[0],
                        "operator": filter_item[1],
                        "value": filter_item[2] if len(filter_item) == 3 else filter_item[2:],
                    }
                )
                continue

            # Handle dict format
            if not isinstance(filter_item, dict):
                raise ValueError(
                    f"Filter {i} must be a list [field, operator, value] or dict {{field, operator, value}}, got {type(filter_item).__name__}"
                )

            # Create a copy to avoid modifying the original
            normalized_filter = dict(filter_item)

            # Auto-correct common mistakes: field_name -> field
            if "field_name" in normalized_filter and "field" not in normalized_filter:
                normalized_filter["field"] = normalized_filter.pop("field_name")

            # Validate required keys
            if "field" not in normalized_filter:
                available_keys = list(filter_item.keys())
                raise ValueError(
                    f"Filter {i} must have a 'field' key. "
                    f"Available keys: {available_keys}. "
                    f"Did you mean to use 'field' instead of 'field_name'?"
                )

            if "operator" not in normalized_filter:
                available_keys = list(filter_item.keys())
                raise ValueError(f"Filter {i} must have an 'operator' key. Available keys: {available_keys}")

            if "value" not in normalized_filter:
                available_keys = list(filter_item.keys())
                raise ValueError(f"Filter {i} must have a 'value' key. Available keys: {available_keys}")

            normalized_filters.append(normalized_filter)

        return normalized_filters


class AdvancedSearchRequest(BaseAPIRequest):
    """Model for sg.search.advanced API requests.

    This model extends the basic search request with time-based filters and
    related_fields support so it can drive more complex queries while
    remaining compatible with the existing ShotGrid find API.
    """

    entity_type: EntityType
    filters: List[Any] = Field(default_factory=list)
    time_filters: List[TimeFilter] = Field(
        default_factory=list,
        description="Optional list of time-based filters such as in_last/in_next.",
    )
    fields: Optional[List[str]] = None
    related_fields: Optional[Dict[str, List[str]]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        None,
        description="Logical operator for combining filters. Must be 'all' (AND logic) or 'any' (OR logic). Only used when filters is a complex filter dict with 'filters' key.",
    )
    limit: Optional[int] = Field(None, gt=0)

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["all", "any"]:
            raise ValueError("filter_operator must be 'all' or 'any'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate and normalize filters parameter.

        Supports four input styles:
        - List format: ["field", "operator", value]
        - Dict format: {"field", "operator", "value"}: internal/Python API style
        - Dict format: {"field_name", "operator", "value"}: common mistake (auto-corrected)
        - Dict format: {"path", "relation", "values"}: ShotGrid REST API _search style
        """
        # Allow empty filters list - ShotGrid API allows this to return all entities
        if not v:
            return v

        normalized_filters: List[Dict[str, Any]] = []

        for i, filter_item in enumerate(v):
            # Handle list/tuple format: ["field", "operator", value]
            if isinstance(filter_item, (list, tuple)):
                if len(filter_item) < 3:
                    raise ValueError(
                        f"Filter {i} in list format must have at least 3 elements [field, operator, value], got {len(filter_item)}"
                    )
                # Normalize datetime values in filter value
                value = filter_item[2] if len(filter_item) == 3 else filter_item[2:]
                value = _normalize_datetime_value(value)

                normalized_filters.append(
                    {
                        "field": filter_item[0],
                        "operator": filter_item[1],
                        "value": value,
                    }
                )
                continue

            # Handle dict format
            if not isinstance(filter_item, dict):
                raise ValueError(
                    f"Filter {i} must be a list [field, operator, value] or dict {{field, operator, value}}, got {type(filter_item).__name__}"
                )

            # Create a copy to avoid modifying the original
            working_filter = dict(filter_item)

            # Auto-correct common mistakes: field_name -> field
            if "field_name" in working_filter and "field" not in working_filter:
                working_filter["field"] = working_filter.pop("field_name")

            # Already in internal style
            if all(key in working_filter for key in ("field", "operator", "value")):
                # Normalize datetime values
                working_filter["value"] = _normalize_datetime_value(working_filter["value"])
                normalized_filters.append(working_filter)
                continue

            # ShotGrid REST style: path/relation/values
            if all(key in working_filter for key in ("path", "relation", "values")):
                path = working_filter["path"]
                relation = working_filter["relation"]
                values = working_filter["values"]

                # Normalize REST 'values' (always list) to our 'value'
                value = values
                if isinstance(values, list) and len(values) == 1 and relation in ("is", "is_not"):
                    value = values[0]

                # Normalize datetime values
                value = _normalize_datetime_value(value)

                normalized_filters.append({"field": path, "operator": relation, "value": value})
                continue

            # Provide helpful error message
            available_keys = list(filter_item.keys())
            raise ValueError(
                f"Filter {i} must have either ('field', 'operator', 'value') or ('path', 'relation', 'values') keys. "
                f"Available keys: {available_keys}. "
                f"Did you mean to use 'field' instead of 'field_name'?"
            )

        return normalized_filters

    @field_validator("related_fields")
    @classmethod
    def validate_related_fields(cls, v):
        """Validate related_fields parameter."""
        if v is not None:
            for field, related_field_list in v.items():
                if not isinstance(field, str):
                    raise ValueError(f"Related field key must be a string, got {type(field).__name__}")

                if not isinstance(related_field_list, list):
                    raise ValueError(
                        f"Related field value for '{field}' must be a list, got {type(related_field_list).__name__}"
                    )

                for related_field in related_field_list:
                    if not isinstance(related_field, str):
                        raise ValueError(
                            f"Related field item for '{field}' must be a string, got {type(related_field).__name__}"
                        )

        return v
