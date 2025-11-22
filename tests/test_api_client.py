"""Tests for the ShotGridAPIClient wrapper and its parameter handling."""

from typing import Any, Dict, List, Optional

from shotgrid_mcp_server.api_client import ShotGridAPIClient
from shotgrid_mcp_server.api_models import FindOneRequest, FindRequest


class _DummyConnection:
    """Minimal fake ShotGrid connection used to verify client kwargs.

    The class name is intentionally not ``MockgunExt`` so that the client
    exercises the "real ShotGrid" branch where all keyword arguments are
    passed through.
    """

    def __init__(self) -> None:
        self.last_find_call: Optional[Dict[str, Any]] = None
        self.last_find_one_call: Optional[Dict[str, Any]] = None

    # The real ShotGrid API ``find`` signature is
    #   find(entity_type, filters, **kwargs)
    def find(self, entity_type: str, filters: List[Any], **kwargs: Any) -> List[Dict[str, Any]]:  # type: ignore[override]
        self.last_find_call = {
            "entity_type": entity_type,
            "filters": filters,
            "kwargs": kwargs,
        }
        # Return a simple payload so the client has a realistic result type
        return [{"id": 1, "type": entity_type, "code": "TEST"}]

    def find_one(self, entity_type: str, filters: List[Any], **kwargs: Any) -> Optional[Dict[str, Any]]:  # type: ignore[override]
        self.last_find_one_call = {
            "entity_type": entity_type,
            "filters": filters,
            "kwargs": kwargs,
        }
        return {"id": 1, "type": entity_type, "code": "TEST_ONE"}


def test_find_uses_full_kwargs_for_non_mockgun_connection() -> None:
    """ShotGridAPIClient.find should pass all supported kwargs for real connections."""

    connection = _DummyConnection()
    client = ShotGridAPIClient(connection)

    request = FindRequest(
        entity_type="Shot",
        filters=[["code", "is", "TEST"]],
        fields=["code"],
        order=[{"field_name": "code", "direction": "asc"}],
        filter_operator="all",
        limit=10,
        retired_only=True,
        page=2,
        include_archived_projects=False,
        additional_filter_presets=[{"preset_name": "recent"}],
    )

    result = client.find(request)

    # The dummy connection should have been called once with the expected kwargs
    assert connection.last_find_call is not None
    assert result == [{"id": 1, "type": "Shot", "code": "TEST"}]

    kwargs = connection.last_find_call["kwargs"]
    assert kwargs["fields"] == ["code"]
    assert kwargs["order"] == [{"field_name": "code", "direction": "asc"}]
    assert kwargs["filter_operator"] == "all"
    assert kwargs["retired_only"] is True
    assert kwargs["page"] == 2
    assert kwargs["include_archived_projects"] is False
    # These two were the main uncovered branches in the client
    assert kwargs["limit"] == 10
    assert kwargs["additional_filter_presets"] == [{"preset_name": "recent"}]


def test_find_one_uses_full_kwargs_for_non_mockgun_connection() -> None:
    """ShotGridAPIClient.find_one should also pass retired_only and include_archived_projects."""

    connection = _DummyConnection()
    client = ShotGridAPIClient(connection)

    request = FindOneRequest(
        entity_type="Shot",
        filters=[["code", "is", "TEST_ONE"]],
        fields=["code"],
        order=None,
        filter_operator="all",
        retired_only=True,
        include_archived_projects=False,
    )

    result = client.find_one(request)

    assert connection.last_find_one_call is not None
    assert result == {"id": 1, "type": "Shot", "code": "TEST_ONE"}

    kwargs = connection.last_find_one_call["kwargs"]
    assert kwargs["fields"] == ["code"]
    assert kwargs["order"] is None
    assert kwargs["filter_operator"] == "all"
    assert kwargs["retired_only"] is True
    assert kwargs["include_archived_projects"] is False
