"""Tests for ShotGrid MCP schema resources.

These tests focus on the helper functions that shape schema data into a
stable JSON structure suitable for MCP resources.
"""

from __future__ import annotations

from typing import Any, Dict

import pytest
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server import schema_resources as sr


def test_extract_status_choices_full_payload() -> None:
    """_extract_status_choices handles full ShotGrid-style payload."""

    field_schema: Dict[str, Any] = {
        "data_type": {"value": "status_list"},
        "properties": {
            "valid_values": {"value": ["wtg", "ip", "fin"]},
            "display_values": {"value": {"wtg": "Waiting", "ip": "In Progress", "fin": "Final"}},
            "default_value": {"value": "wtg"},
        },
    }

    result = sr._extract_status_choices(field_schema)

    assert result["data_type"] == "status_list"
    assert result["valid_values"] == ["wtg", "ip", "fin"]
    assert result["display_values"]["ip"] == "In Progress"
    assert result["default_value"] == "wtg"


def test_extract_status_choices_missing_optional_keys() -> None:
    """_extract_status_choices behaves when optional keys are absent."""

    field_schema: Dict[str, Any] = {
        "data_type": {"value": "status_list"},
        "properties": {},
    }

    result = sr._extract_status_choices(field_schema)

    # We always at least expose the data_type
    assert result == {"data_type": "status_list"}


def test_build_status_payload_for_entity_uses_schema(mock_sg: Shotgun) -> None:
    """_build_status_payload_for_entity picks up status_list fields.

    Our test schema defines an ``sg_status_list`` field with ``data_type``
    ``"status_list"`` on the ``Asset`` entity, so that is the minimal
    contract we assert here. The real ShotGrid schema usually provides
    richer ``valid_values`` and ``display_values`` data, which will also
    be surfaced by the helpers but is not required for these tests.
    """

    payload = sr._build_status_payload_for_entity(mock_sg, "Asset")

    assert "sg_status_list" in payload
    status_info = payload["sg_status_list"]
    assert status_info["data_type"] == "status_list"


def test_build_all_status_payload_aggregates_entity_types(mock_sg: Shotgun, monkeypatch: pytest.MonkeyPatch) -> None:
    """_build_all_status_payload groups status fields by entity type.

    We stub ``get_entity_types_from_schema`` so that this test focuses on how
    the helper aggregates per-entity payloads rather than on the exact
    behaviour of the schema loader in different environments (Mockgun vs
    real ShotGrid).
    """

    def fake_get_entity_types_from_schema(_sg: Shotgun) -> set[str]:
        return {"Asset"}

    monkeypatch.setattr(sr, "get_entity_types_from_schema", fake_get_entity_types_from_schema)

    payload = sr._build_all_status_payload(mock_sg)

    assert "Asset" in payload
    asset_status = payload["Asset"]["sg_status_list"]
    assert asset_status["data_type"] == "status_list"


def test_register_schema_resources_registers_and_resolves(mock_sg: Shotgun, monkeypatch: pytest.MonkeyPatch) -> None:
    """register_schema_resources wires up resources that read from schema.

    We stub the schema loader to make the behaviour deterministic under
    Mockgun while still exercising the real helper functions.
    """

    class DummyServer:
        def __init__(self) -> None:
            self.resources: Dict[str, Any] = {}

        def resource(self, uri: str):
            def decorator(func):
                self.resources[uri] = func
                return func

            return decorator

    def fake_get_entity_types_from_schema(_sg: Shotgun) -> set[str]:
        return {"Asset"}

    monkeypatch.setattr(sr, "get_entity_types_from_schema", fake_get_entity_types_from_schema)

    server = DummyServer()
    sr.register_schema_resources(server, mock_sg)

    # All expected resource URIs should be registered.
    assert "shotgrid://schema/entities" in server.resources
    assert "shotgrid://schema/statuses" in server.resources
    assert "shotgrid://schema/statuses/{entity_type}" in server.resources

    # Calling the resources should return sensible data.
    entities = server.resources["shotgrid://schema/entities"]()
    assert "Shot" in entities

    all_statuses = server.resources["shotgrid://schema/statuses"]()
    assert "Asset" in all_statuses

    per_entity = server.resources["shotgrid://schema/statuses/{entity_type}"](entity_type="Asset")
    assert "sg_status_list" in per_entity
