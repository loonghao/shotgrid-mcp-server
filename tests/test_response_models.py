"""Tests for response_models module."""

from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel

from shotgrid_mcp_server.response_models import (
    BaseResponse,
    EntitiesResponse,
    EntityResponse,
    ErrorResponse,
    PlaylistResponse,
    create_error_response,
    create_playlist_response,
    create_success_response,
    generate_playlist_url,
    generate_playlist_url_variants,
    serialize_response,
)


class DummyModel(BaseModel):
    """Simple Pydantic model used to test serialize_response."""

    value: int


def test_create_success_response_single_entity_with_url() -> None:
    """create_success_response returns an EntityResponse for dict payloads."""

    data: Dict[str, Any] = {"id": 1, "name": "Test Entity"}
    response = create_success_response(
        data,
        message="ok",
        url="https://example.com/item/1",
    )

    assert isinstance(response, EntityResponse)
    assert response.data["id"] == 1
    assert response.url == "https://example.com/item/1"
    assert response.metadata.status == "success"
    assert response.metadata.message == "ok"


def test_create_success_response_multiple_entities() -> None:
    """create_success_response returns EntitiesResponse for list payloads."""

    items: List[Dict[str, Any]] = [{"id": 1}, {"id": 2}]
    response = create_success_response(
        items,
        message="ok",
        total_count=10,
        page=2,
        page_size=5,
    )

    assert isinstance(response, EntitiesResponse)
    assert response.total_count == 10
    assert response.page == 2
    assert response.page_size == 5
    assert len(response.data) == 2
    assert response.metadata.message == "ok"


def test_create_success_response_generic_payload() -> None:
    """create_success_response falls back to BaseResponse for other payloads."""

    data = "raw-result"
    response = create_success_response(data, message="ok")

    assert isinstance(response, BaseResponse)
    assert response.data == "raw-result"
    assert response.metadata.message == "ok"


def test_create_error_response_wrapper() -> None:
    """create_error_response builds an ErrorResponse with metadata set."""

    response = create_error_response(
        message="Something went wrong",
        error_type="CustomError",
        error_details={"detail": "info"},
    )

    assert isinstance(response, ErrorResponse)
    assert response.metadata.status == "error"
    assert response.metadata.message == "Something went wrong"
    assert response.metadata.error_type == "CustomError"
    assert response.metadata.error_details == {"detail": "info"}
    assert response.data is None


def test_create_playlist_response_sets_url_and_metadata() -> None:
    """create_playlist_response returns a PlaylistResponse with URL set."""

    data: Dict[str, Any] = {"id": 42, "code": "Review Playlist"}
    response = create_playlist_response(
        data=data,
        url="https://example.com/page/screening_room?entity_id=42",
        message="created",
    )

    assert isinstance(response, PlaylistResponse)
    assert response.data["code"] == "Review Playlist"
    assert response.url.endswith("entity_id=42")
    assert response.metadata.message == "created"


def test_generate_playlist_url_variants_without_project() -> None:
    """media_center URL is omitted when project_id is not provided."""

    base_url = "https://mcp-site.shotgrid.autodesk.com/"
    urls = generate_playlist_url_variants(base_url, playlist_id=6)

    assert urls["screening_room"] == (
        "https://mcp-site.shotgrid.autodesk.com/page/screening_room?entity_type=Playlist&entity_id=6"
    )
    assert urls["detail"] == "https://mcp-site.shotgrid.autodesk.com/Playlist/detail/6"
    assert "media_center" not in urls


def test_generate_playlist_url_variants_with_project() -> None:
    """media_center URL includes project_id when provided."""

    base_url = "https://mcp-site.shotgrid.autodesk.com/"
    urls = generate_playlist_url_variants(base_url, playlist_id=6, project_id=70)

    assert urls["media_center"] == (
        "https://mcp-site.shotgrid.autodesk.com/page/media_center?type=Playlist&id=6&project_id=70"
    )


def test_generate_playlist_url_delegates_to_variants() -> None:
    """generate_playlist_url returns the screening_room variant."""

    base_url = "https://mcp-site.shotgrid.autodesk.com/"
    url = generate_playlist_url(base_url, playlist_id=6)
    variants = generate_playlist_url_variants(base_url, playlist_id=6)

    assert url == variants["screening_room"]


def test_serialize_response_with_pydantic_model() -> None:
    """serialize_response uses model_dump for Pydantic models."""

    model = DummyModel(value=123)
    result = serialize_response(model)

    assert result == {"value": 123}


def test_serialize_response_with_plain_dict() -> None:
    """serialize_response returns plain mappings unchanged."""

    payload = {"foo": "bar"}
    result = serialize_response(payload)

    assert result == payload

