"""MCP Resources exposing ShotGrid schema information.

This module defines read-only MCP resources that surface ShotGrid schema
and status field metadata as contextual data for LLMs.

Resources added here are intended to complement, not replace, the
existing ``sg.schema_*`` tools. Tools are for RPC-style calls; resources
are for static / slowly-changing context that models can read cheaply.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Mapping

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.schema_loader import get_entity_types_from_schema
from shotgrid_mcp_server.tools.types import FastMCPType

logger = logging.getLogger(__name__)


def _extract_status_choices(field_schema: Mapping[str, Any]) -> Dict[str, Any]:
    """Extract status choice metadata from a single field schema.

    The ShotGrid Python API exposes schema in a nested structure. For
    status-list fields we care about the valid codes, their display
    labels, and any default value. This helper normalises that structure
    into a compact, JSON-serialisable mapping.
    """

    properties: Mapping[str, Any] = field_schema.get("properties", {}) or {}

    valid_values = (properties.get("valid_values") or {}).get("value")
    display_values = (properties.get("display_values") or {}).get("value")
    default_value = (properties.get("default_value") or {}).get("value")
    data_type = (field_schema.get("data_type") or {}).get("value")

    result: Dict[str, Any] = {}

    if data_type is not None:
        result["data_type"] = data_type
    if valid_values is not None:
        result["valid_values"] = valid_values
    if display_values is not None:
        result["display_values"] = display_values
    if default_value is not None:
        result["default_value"] = default_value

    return result


def _build_status_payload_for_entity(sg: Shotgun, entity_type: str) -> Dict[str, Any]:
    """Build status-field metadata for a single entity type.

    We scan the field schema for the entity and pick out any fields whose
    ``data_type`` is ``"status_list"``. For each such field we expose the
    choice metadata via :func:`_extract_status_choices`.
    """

    try:
        schema = sg.schema_field_read(entity_type)
    except Exception as exc:  # pragma: no cover - very defensive
        logger.warning("Failed to read schema for entity %s: %s", entity_type, exc)
        return {}

    status_fields: Dict[str, Any] = {}

    for field_name, field_info in schema.items():
        data_type = (field_info.get("data_type") or {}).get("value")
        if data_type != "status_list":
            continue

        choices = _extract_status_choices(field_info)
        if choices:
            status_fields[field_name] = choices

    return status_fields


def _build_all_status_payload(sg: Shotgun) -> Dict[str, Any]:
    """Build status metadata for all entity types.

    The result is a mapping of ``entity_type -> {field_name -> metadata}``.
    Entity types without any status-list fields are omitted.
    """

    payload: Dict[str, Any] = {}

    entity_types = sorted(get_entity_types_from_schema(sg))
    for entity_type in entity_types:
        fields = _build_status_payload_for_entity(sg, entity_type)
        if fields:
            payload[entity_type] = fields

    return payload


def register_schema_resources(server: FastMCPType, sg: Shotgun) -> None:
    """Register schema-related MCP resources on the server.

    Currently we expose two resources:

    * ``shotgrid://schema/entities`` – full entity schema as returned by
      :meth:`Shotgun.schema_read`.
    * ``shotgrid://schema/statuses`` – status-list field metadata grouped
      by entity type.
    * ``shotgrid://schema/statuses/{entity_type}`` – status-list fields
      for a single entity type.
    """

    @server.resource("shotgrid://schema/entities")
    def schema_entities() -> Dict[str, Any]:
        """Return full entity schema from ShotGrid.

        This mirrors the behaviour of ``sg.schema_read()`` but surfaces
        the result as a read-only MCP resource so that AI clients can
        load it as context without incurring a tool call.
        """

        try:
            return sg.schema_read()
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Failed to read ShotGrid schema: %s", exc)
            return {}

    @server.resource("shotgrid://schema/statuses")
    def schema_statuses() -> Dict[str, Any]:
        """Return status field metadata for all entity types."""

        return _build_all_status_payload(sg)

    @server.resource("shotgrid://schema/statuses/{entity_type}")
    def schema_statuses_for_entity(entity_type: str) -> Dict[str, Any]:
        """Return status field metadata for a specific entity type."""

        return _build_status_payload_for_entity(sg, entity_type)
