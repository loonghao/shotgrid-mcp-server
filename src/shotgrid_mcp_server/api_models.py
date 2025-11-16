"""Pydantic models for ShotGrid API requests.

This module provides Pydantic models for validating and standardizing ShotGrid API requests.
These models ensure that all parameters passed to the ShotGrid API are valid and properly formatted.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.models import TimeFilter


class BaseAPIRequest(BaseModel):
    """Base model for all ShotGrid API requests."""

    class Config:
        """Pydantic configuration."""

        extra = "forbid"  # Prevent extra fields


class FindRequest(BaseAPIRequest):
    """Model for ShotGrid find API requests."""

    entity_type: EntityType
    filters: List[Any]
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = None
    limit: Optional[int] = None
    retired_only: bool = False
    page: Optional[int] = Field(
        None, gt=0, description="Page number for pagination. Must be a positive integer if provided."
    )
    include_archived_projects: bool = True
    additional_filter_presets: Optional[List[Dict[str, Any]]] = None

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, v):
        """Validate limit parameter."""
        if v is not None and v <= 0:
            raise ValueError("limit must be a positive integer")
        return v


class FindOneRequest(BaseAPIRequest):
    """Model for ShotGrid find_one API requests."""

    entity_type: EntityType
    filters: List[Any]
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = None
    retired_only: bool = False
    include_archived_projects: bool = True


class CreateRequest(BaseAPIRequest):
    """Model for ShotGrid create API requests."""

    entity_type: EntityType
    data: Dict[str, Any]
    return_fields: Optional[List[str]] = None


class UpdateRequest(BaseAPIRequest):
    """Model for ShotGrid update API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)
    data: Dict[str, Any]
    multi_entity_update_mode: Optional[str] = None


class DeleteRequest(BaseAPIRequest):
    """Model for ShotGrid delete API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)


class ReviveRequest(BaseAPIRequest):
    """Model for ShotGrid revive API requests."""

    entity_type: EntityType
    entity_id: int = Field(..., gt=0)


class BatchRequest(BaseAPIRequest):
    """Model for ShotGrid batch API requests."""

    requests: List[Dict[str, Any]]

    @model_validator(mode="after")
    def validate_batch_requests(self):
        """Validate batch requests."""
        for request in self.requests:
            if "request_type" not in request:
                raise ValueError("Each batch request must have a 'request_type'")

            request_type = request["request_type"]
            if request_type not in ["create", "update", "delete"]:
                raise ValueError(f"Invalid request_type: {request_type}. Must be one of: create, update, delete")

            if "entity_type" not in request:
                raise ValueError("Each batch request must have an 'entity_type'")

            if request_type in ["update", "delete"] and "entity_id" not in request:
                raise ValueError(f"Batch request of type '{request_type}' must have an 'entity_id'")

            if request_type in ["create", "update"] and "data" not in request:
                raise ValueError(f"Batch request of type '{request_type}' must have 'data'")

        return self


class SummarizeRequest(BaseAPIRequest):
    """Model for ShotGrid summarize API requests."""

    entity_type: EntityType
    filters: List[Any]
    summary_fields: List[Dict[str, Any]]
    filter_operator: Optional[str] = None
    grouping: Optional[List[Dict[str, Any]]] = None
    include_archived_projects: bool = True


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
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        "and", description="Logical operator for combining filters. Must be 'and' or 'or'."
    )
    limit: Optional[int] = Field(None, gt=0)

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["and", "or"]:
            raise ValueError("filter_operator must be 'and' or 'or'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate filters parameter."""
        # Allow empty filters list - ShotGrid API allows this to return all entities
        if not v:
            return v

        for i, filter_dict in enumerate(v):
            if not isinstance(filter_dict, dict):
                raise ValueError(f"Filter {i} must be a dictionary")

            if "field" not in filter_dict:
                raise ValueError(f"Filter {i} must have a 'field' key")

            if "operator" not in filter_dict:
                raise ValueError(f"Filter {i} must have an 'operator' key")

            if "value" not in filter_dict:
                raise ValueError(f"Filter {i} must have a 'value' key")

        return v


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
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    fields: Optional[List[str]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        "and", description="Logical operator for combining filters. Must be 'and' or 'or'."
    )

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["and", "or"]:
            raise ValueError("filter_operator must be 'and' or 'or'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate filters parameter."""
        # For find_one, we should have at least one filter to identify the entity
        # But ShotGrid API technically allows empty filters to return the first entity
        if not v:
            return v

        for i, filter_dict in enumerate(v):
            if not isinstance(filter_dict, dict):
                raise ValueError(f"Filter {i} must be a dictionary")

            if "field" not in filter_dict:
                raise ValueError(f"Filter {i} must have a 'field' key")

            if "operator" not in filter_dict:
                raise ValueError(f"Filter {i} must have an 'operator' key")

            if "value" not in filter_dict:
                raise ValueError(f"Filter {i} must have a 'value' key")

        return v


class AdvancedSearchRequest(BaseAPIRequest):
    """Model for sg.search.advanced API requests.

    This model extends the basic search request with time-based filters and
    related_fields support so it can drive more complex queries while
    remaining compatible with the existing ShotGrid find API.
    """

    entity_type: EntityType
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    time_filters: List[TimeFilter] = Field(
        default_factory=list,
        description="Optional list of time-based filters such as in_last/in_next.",
    )
    fields: Optional[List[str]] = None
    related_fields: Optional[Dict[str, List[str]]] = None
    order: Optional[List[Dict[str, str]]] = None
    filter_operator: Optional[str] = Field(
        "and", description="Logical operator for combining filters. Must be 'and' or 'or'."
    )
    limit: Optional[int] = Field(None, gt=0)

    @field_validator("filter_operator")
    @classmethod
    def validate_filter_operator(cls, v):
        """Validate filter_operator parameter."""
        if v is not None and v not in ["and", "or"]:
            raise ValueError("filter_operator must be 'and' or 'or'")
        return v

    @field_validator("filters")
    @classmethod
    def validate_filters(cls, v):
        """Validate and normalize filters parameter.

        Supports two input styles:
        - {"field", "operator", "value"}: internal/Python API style
        - {"path", "relation", "values"}: ShotGrid REST API _search style
        """
        # Allow empty filters list - ShotGrid API allows this to return all entities
        if not v:
            return v

        normalized_filters: List[Dict[str, Any]] = []

        for i, filter_dict in enumerate(v):
            if not isinstance(filter_dict, dict):
                raise ValueError(f"Filter {i} must be a dictionary")

            # Already in internal style
            if all(key in filter_dict for key in ("field", "operator", "value")):
                normalized_filters.append(filter_dict)
                continue

            # ShotGrid REST style: path/relation/values
            if all(key in filter_dict for key in ("path", "relation", "values")):
                path = filter_dict["path"]
                relation = filter_dict["relation"]
                values = filter_dict["values"]

                # Normalize REST 'values' (always list) to our 'value'
                value = values
                if isinstance(values, list) and len(values) == 1 and relation in ("is", "is_not"):
                    value = values[0]

                normalized_filters.append({"field": path, "operator": relation, "value": value})
                continue

            raise ValueError(
                "Filter {i} must have either ('field', 'operator', 'value') or ('path', 'relation', 'values') keys".format(
                    i=i
                )
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
