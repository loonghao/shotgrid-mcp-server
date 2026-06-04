"""Shared business-logic library for ShotGrid MCP server.

This module contains pure ShotGrid business logic extracted from the
tools layer. All functions accept a ``shotgun_api3.Shotgun`` connection
as their first argument and return typed data.

This module does NOT import FastMCP, dcc-mcp-core, or any MCP framework.
It only depends on ShotGrid API, shotgrid-query, and local infra modules
(connection_pool, exceptions, api_client, utils).
"""

# Import built-in modules
import logging
from typing import Any, Dict, List, Optional

# Import third-party modules
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.api_client import ShotGridAPIClient
from shotgrid_mcp_server.api_models import FindOneRequest, FindRequest
from shotgrid_mcp_server.custom_types import EntityType
from shotgrid_mcp_server.exceptions import (
    EntityNotFoundError,
    ShotGridMCPError,
)
from shotgrid_mcp_server.response_models import (
    SchemaResult,
)
from shotgrid_mcp_server.utils import serialize_entity

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Connection helper
# ═══════════════════════════════════════════════════════════════════════════


def get_current_connection(sg_fallback: Optional[Shotgun] = None) -> Shotgun:
    """Get the current ShotGrid connection for the request.

    Tries HTTP headers first, then env vars, then fallback.

    Args:
        sg_fallback: Optional fallback connection.

    Returns:
        Active Shotgun connection.

    Raises:
        ShotGridMCPError: If no connection can be established.
    """
    from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection

    return get_current_shotgrid_connection(fallback_sg=sg_fallback)


# ═══════════════════════════════════════════════════════════════════════════
# Schema helpers
# ═══════════════════════════════════════════════════════════════════════════


def get_entity_schema(sg: Shotgun, entity_type: EntityType) -> Dict[str, Any]:
    """Get field schema for an entity type.

    Args:
        sg: ShotGrid connection.
        entity_type: Valid ShotGrid entity type (e.g., "Shot", "Asset", "Task").

    Returns:
        Dict with entity_type and fields schema.

    Raises:
        ShotGridMCPError: If schema retrieval fails.
    """
    try:
        result = sg.schema_field_read(entity_type)
        if result is None:
            raise ShotGridMCPError(f"Failed to read schema for {entity_type}")
        return SchemaResult(entity_type=entity_type, fields=dict(result)).model_dump()
    except ShotGridMCPError:
        raise
    except Exception as e:
        logger.error("Schema read failed for %s: %s", entity_type, e)
        raise ShotGridMCPError(f"Schema read failed: {e}") from e


def get_all_entity_types(sg: Shotgun) -> List[str]:
    """Get all available entity types from ShotGrid.

    Args:
        sg: ShotGrid connection.

    Returns:
        List of entity type names.
    """
    try:
        result = sg.schema_entity_read()
        return list(result.keys()) if result else []
    except Exception as e:
        logger.error("Failed to read entity types: %s", e)
        raise ShotGridMCPError(f"Failed to read entity types: {e}") from e


def get_field_schema(sg: Shotgun, entity_type: EntityType, field_name: str) -> Dict[str, Any]:
    """Get schema for a specific field of an entity type.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type name.
        field_name: Field name to get schema for.

    Returns:
        Field schema dict.
    """
    try:
        result = sg.schema_field_read(entity_type, field_name)
        if result is None:
            raise ShotGridMCPError(f"Field {field_name} not found on {entity_type}")
        return dict(result)
    except ShotGridMCPError:
        raise
    except Exception as e:
        logger.error("Field schema read failed: %s", e)
        raise ShotGridMCPError(f"Field schema read failed: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# CRUD operations
# ═══════════════════════════════════════════════════════════════════════════


def create_entity_record(
    sg: Shotgun,
    entity_type: EntityType,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Create a new entity in ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity to create.
        data: Entity field data as key-value pairs.

    Returns:
        Dict with created entity data (type, id, etc.).

    Raises:
        ShotGridMCPError: If creation fails.
    """
    try:
        result = sg.create(entity_type, data)
        if result is None:
            raise ShotGridMCPError(f"Failed to create {entity_type}")
        return serialize_entity(result)
    except ShotGridMCPError:
        raise
    except Exception as e:
        logger.error("Failed to create %s: %s", entity_type, e)
        raise ShotGridMCPError(f"Failed to create {entity_type}: {e}") from e


def read_entity_record(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    fields: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Read a single entity by ID from ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        entity_id: Entity ID to read.
        fields: Optional fields to return. Defaults to all fields.

    Returns:
        Dict with entity data.

    Raises:
        EntityNotFoundError: If entity doesn't exist.
        ShotGridMCPError: If read fails.
    """
    try:
        filters = [["id", "is", entity_id]]
        result = sg.find_one(entity_type, filters, fields=fields or [])
        if result is None:
            raise EntityNotFoundError(entity_type, entity_id)
        return serialize_entity(result)
    except EntityNotFoundError:
        raise
    except Exception as e:
        logger.error("Failed to read %s[%d]: %s", entity_type, entity_id, e)
        raise ShotGridMCPError(f"Failed to read {entity_type}[{entity_id}]: {e}") from e


def update_entity_record(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Update an existing entity in ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        entity_id: Entity ID to update.
        data: Fields to update.

    Returns:
        Dict with updated entity data.

    Raises:
        ShotGridMCPError: If update fails.
    """
    try:
        result = sg.update(entity_type, entity_id, data)
        if result is None:
            raise ShotGridMCPError(f"Failed to update {entity_type}[{entity_id}]")
        return serialize_entity(result)
    except ShotGridMCPError:
        raise
    except Exception as e:
        logger.error("Failed to update %s[%d]: %s", entity_type, entity_id, e)
        raise ShotGridMCPError(f"Failed to update {entity_type}[{entity_id}]: {e}") from e


def delete_entity_record(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
) -> bool:
    """Delete (retire) an entity in ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Type of entity.
        entity_id: Entity ID to delete.

    Returns:
        True if deletion succeeded.

    Raises:
        ShotGridMCPError: If deletion fails.
    """
    try:
        result = sg.delete(entity_type, entity_id)
        return bool(result)
    except Exception as e:
        logger.error("Failed to delete %s[%d]: %s", entity_type, entity_id, e)
        raise ShotGridMCPError(f"Failed to delete {entity_type}[{entity_id}]: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Search helpers
# ═══════════════════════════════════════════════════════════════════════════


def execute_search(
    sg: Shotgun,
    entity_type: EntityType,
    filters: Optional[List[Any]] = None,
    fields: Optional[List[str]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    filter_operator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search for entities in ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        fields: Fields to return.
        order: Sort order.
        limit: Max results.
        filter_operator: "all" (AND) or "any" (OR).

    Returns:
        List of entity dicts.
    """
    api_client = ShotGridAPIClient(sg)
    from shotgrid_query import process_filters

    processed_filters = process_filters(filters or [])

    find_request = FindRequest(
        entity_type=entity_type,
        filters=processed_filters,
        fields=fields,
        order=order,
        filter_operator=filter_operator,
        limit=limit,
        page=1,
    )

    result = api_client.find(find_request) or []
    return [serialize_entity(entity) for entity in result]


def execute_find_one(
    sg: Shotgun,
    entity_type: EntityType,
    filters: List[Any],
    fields: Optional[List[str]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
    filter_operator: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Find a single entity by filters.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        fields: Fields to return.
        order: Sort order.
        filter_operator: Logical operator.

    Returns:
        Entity dict or None if not found.
    """
    api_client = ShotGridAPIClient(sg)
    from shotgrid_query import process_filters

    processed_filters = process_filters(filters or [])

    find_one_request = FindOneRequest(
        entity_type=entity_type,
        filters=processed_filters,
        fields=fields,
        order=order,
        filter_operator=filter_operator,
    )

    result = api_client.find_one(find_one_request)
    return serialize_entity(result) if result else None


def execute_find_with_related(
    sg: Shotgun,
    entity_type: EntityType,
    filters: Optional[List[Any]] = None,
    fields: Optional[List[str]] = None,
    related_fields: Optional[Dict[str, List[str]]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    filter_operator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Search entities with related entity data.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        fields: Direct fields.
        related_fields: Dict mapping entity link fields to sub-fields.
        order: Sort order.
        limit: Max results.
        filter_operator: Logical operator.

    Returns:
        List of entity dicts with related data populated.
    """
    from shotgrid_query import process_filters

    processed_filters = process_filters(filters or [])

    # Build all_fields including related entity fields via dot notation
    all_fields = list(fields or [])
    if related_fields:
        for entity_field, related_field_list in related_fields.items():
            field_info = sg.schema_field_read(entity_type, entity_field)
            if not field_info:
                continue
            valid_types = field_info.get("properties", {}).get("valid_types", {}).get("value", [])
            if not valid_types:
                continue
            for related_field in related_field_list:
                related_entity_type = valid_types[0]
                all_fields.append(f"{entity_field}.{related_entity_type}.{related_field}")

    api_client = ShotGridAPIClient(sg)
    find_request = FindRequest(
        entity_type=entity_type,
        filters=processed_filters,
        fields=all_fields,
        order=order,
        filter_operator=filter_operator,
        limit=limit,
        page=1,
    )

    result = api_client.find(find_request) or []
    return [serialize_entity(entity) for entity in result]


# ═══════════════════════════════════════════════════════════════════════════
# Batch operations
# ═══════════════════════════════════════════════════════════════════════════


def batch_create(
    sg: Shotgun,
    entity_type: EntityType,
    data_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Batch create entities.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        data_list: List of entity data dicts.

    Returns:
        List of created entity dicts.
    """
    try:
        batch_data = sg.batch(
            [{"request_type": "create", "entity_type": entity_type, "data": data} for data in data_list]
        )
        return [serialize_entity(item) for item in (batch_data or [])]
    except Exception as e:
        logger.error("Batch create failed: %s", e)
        raise ShotGridMCPError(f"Batch create failed: {e}") from e


def batch_update(
    sg: Shotgun,
    entity_type: EntityType,
    data_list: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Batch update entities.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        data_list: List of dicts with "id" and field data.

    Returns:
        List of updated entity dicts.
    """
    try:
        batch_data = sg.batch(
            [
                {
                    "request_type": "update",
                    "entity_type": entity_type,
                    "entity_id": item["id"],
                    "data": {k: v for k, v in item.items() if k != "id"},
                }
                for item in data_list
            ]
        )
        return [serialize_entity(item) for item in (batch_data or [])]
    except Exception as e:
        logger.error("Batch update failed: %s", e)
        raise ShotGridMCPError(f"Batch update failed: {e}") from e


def batch_delete(
    sg: Shotgun,
    entity_type: EntityType,
    entity_ids: List[int],
) -> List[bool]:
    """Batch delete (retire) entities.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        entity_ids: List of entity IDs.

    Returns:
        List of bool results per entity.
    """
    try:
        batch_data = sg.batch(
            [{"request_type": "delete", "entity_type": entity_type, "entity_id": eid} for eid in entity_ids]
        )
        return [bool(item) for item in (batch_data or [])]
    except Exception as e:
        logger.error("Batch delete failed: %s", e)
        raise ShotGridMCPError(f"Batch delete failed: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Note operations
# ═══════════════════════════════════════════════════════════════════════════


def create_note(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    subject: str,
    content: str,
    note_type: str = "Note",
) -> Dict[str, Any]:
    """Create a note on a ShotGrid entity.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type to note on.
        entity_id: Entity ID.
        subject: Note subject.
        content: Note content (HTML or text).
        note_type: Note type (default: "Note").

    Returns:
        Dict with created note data.
    """
    try:
        data = {
            "subject": subject,
            "content": content,
            "note_type": note_type,
        }
        # Link note to entity
        if entity_type and entity_id:
            data["note_links"] = [{"type": entity_type, "id": entity_id}]
        result = sg.create("Note", data)
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to create note: %s", e)
        raise ShotGridMCPError(f"Failed to create note: {e}") from e


def get_entity_notes(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Read notes from a ShotGrid entity.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        entity_id: Entity ID.
        fields: Optional fields to return.

    Returns:
        List of note dicts.
    """
    try:
        default_fields = ["id", "subject", "content", "created_at", "created_by", "user"]
        filters = [["note_links", "in", {"type": entity_type, "id": entity_id}]]
        result = sg.find("Note", filters, fields=fields or default_fields)
        return [serialize_entity(note) for note in (result or [])]
    except Exception as e:
        logger.error("Failed to read notes for %s[%d]: %s", entity_type, entity_id, e)
        raise ShotGridMCPError(f"Failed to read notes: {e}") from e


def update_note(
    sg: Shotgun,
    note_id: int,
    data: Dict[str, Any],
) -> Dict[str, Any]:
    """Update a note in ShotGrid.

    Args:
        sg: ShotGrid connection.
        note_id: Note ID.
        data: Fields to update.

    Returns:
        Dict with updated note data.
    """
    try:
        result = sg.update("Note", note_id, data)
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to update note %d: %s", note_id, e)
        raise ShotGridMCPError(f"Failed to update note: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Thumbnail / media operations
# ═══════════════════════════════════════════════════════════════════════════


def download_thumbnail(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    field_name: str = "image",
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Download a thumbnail from ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        entity_id: Entity ID.
        field_name: Thumbnail field name (default: "image").
        output_path: Optional output file path.

    Returns:
        Dict with download result info.
    """
    try:
        if output_path:
            sg.download_attachment(
                {"type": entity_type, "id": entity_id},
                attachment_field_name=field_name,
                file_path=output_path,
            )
            return {"status": "downloaded", "path": output_path, "entity_type": entity_type, "entity_id": entity_id}
        else:
            # Return base64 data
            import base64
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp_path = tmp.name
            try:
                sg.download_attachment(
                    {"type": entity_type, "id": entity_id},
                    attachment_field_name=field_name,
                    file_path=tmp_path,
                )
                with open(tmp_path, "rb") as f:
                    data = base64.b64encode(f.read()).decode("utf-8")
                return {
                    "status": "downloaded",
                    "data": data,
                    "format": "base64",
                    "entity_type": entity_type,
                    "entity_id": entity_id,
                }
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
    except Exception as e:
        logger.error("Failed to download thumbnail: %s", e)
        raise ShotGridMCPError(f"Failed to download thumbnail: {e}") from e


def upload_thumbnail(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    field_name: str,
    file_path: str,
) -> Dict[str, Any]:
    """Upload a thumbnail to ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        entity_id: Entity ID.
        field_name: Thumbnail field name.
        file_path: Path to image file.

    Returns:
        Dict with upload result.
    """
    try:
        result = sg.upload(
            entity_type,
            entity_id,
            file_path,
            field_name=field_name,
        )
        return {"status": "uploaded", "result": serialize_entity(result) if result else None}
    except Exception as e:
        logger.error("Failed to upload thumbnail: %s", e)
        raise ShotGridMCPError(f"Failed to upload thumbnail: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Playlist operations
# ═══════════════════════════════════════════════════════════════════════════


def create_playlist(
    sg: Shotgun,
    name: str,
    project_id: int,
    description: Optional[str] = None,
    version_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Create a playlist for version review.

    Args:
        sg: ShotGrid connection.
        name: Playlist name.
        project_id: Project ID.
        description: Optional description.
        version_ids: Optional initial version IDs.

    Returns:
        Dict with created playlist data.
    """
    try:
        data: Dict[str, Any] = {
            "code": name,
            "description": description or "",
            "project": {"type": "Project", "id": project_id},
        }
        if version_ids:
            data["versions"] = [{"type": "Version", "id": vid} for vid in version_ids]
        result = sg.create("Playlist", data)
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to create playlist: %s", e)
        raise ShotGridMCPError(f"Failed to create playlist: {e}") from e


def find_playlists(
    sg: Shotgun,
    project_id: Optional[int] = None,
    name_contains: Optional[str] = None,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Search for playlists.

    Args:
        sg: ShotGrid connection.
        project_id: Optional project filter.
        name_contains: Optional name filter.
        fields: Optional fields to return.

    Returns:
        List of playlist dicts.
    """
    try:
        filters = []
        if project_id:
            filters.append(["project", "is", {"type": "Project", "id": project_id}])
        if name_contains:
            filters.append(["code", "contains", name_contains])

        default_fields = ["id", "code", "description", "project", "versions", "created_at"]
        result = sg.find("Playlist", filters, fields=fields or default_fields)
        return [serialize_entity(p) for p in (result or [])]
    except Exception as e:
        logger.error("Failed to find playlists: %s", e)
        raise ShotGridMCPError(f"Failed to find playlists: {e}") from e


def add_versions_to_playlist(
    sg: Shotgun,
    playlist_id: int,
    version_ids: List[int],
) -> Dict[str, Any]:
    """Add versions to an existing playlist.

    Args:
        sg: ShotGrid connection.
        playlist_id: Playlist ID.
        version_ids: Version IDs to add.

    Returns:
        Dict with updated playlist data.
    """
    try:
        result = sg.update(
            "Playlist",
            playlist_id,
            {
                "versions": [{"type": "Version", "id": vid} for vid in version_ids],
                "update_mode": "multi_entity_update_mode_add",
            },
        )
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to add versions to playlist %d: %s", playlist_id, e)
        raise ShotGridMCPError(f"Failed to add versions to playlist: {e}") from e


def remove_versions_from_playlist(
    sg: Shotgun,
    playlist_id: int,
    version_ids: List[int],
) -> Dict[str, Any]:
    """Remove versions from a playlist.

    Args:
        sg: ShotGrid connection.
        playlist_id: Playlist ID.
        version_ids: Version IDs to remove.

    Returns:
        Dict with updated playlist data.
    """
    try:
        result = sg.update(
            "Playlist",
            playlist_id,
            {
                "versions": [{"type": "Version", "id": vid} for vid in version_ids],
                "update_mode": "multi_entity_update_mode_remove",
            },
        )
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to remove versions from playlist %d: %s", playlist_id, e)
        raise ShotGridMCPError(f"Failed to remove versions from playlist: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Low-level ShotGrid API
# ═══════════════════════════════════════════════════════════════════════════


def sg_find(
    sg: Shotgun,
    entity_type: EntityType,
    filters: List[Any],
    fields: Optional[List[str]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
    filter_operator: Optional[str] = None,
    limit: Optional[int] = None,
    page: int = 1,
) -> List[Dict[str, Any]]:
    """Low-level ShotGrid find.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        fields: Fields to return.
        order: Sort order.
        filter_operator: Logical operator.
        limit: Max results.
        page: Page number.

    Returns:
        List of raw entity dicts.
    """
    try:
        result = sg.find(
            entity_type, filters, fields=fields, order=order, filter_operator=filter_operator, limit=limit, page=page
        )
        return [serialize_entity(r) for r in (result or [])]
    except Exception as e:
        logger.error("sg.find failed: %s", e)
        raise ShotGridMCPError(f"sg.find failed: {e}") from e


def sg_find_one(
    sg: Shotgun,
    entity_type: EntityType,
    filters: List[Any],
    fields: Optional[List[str]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
) -> Optional[Dict[str, Any]]:
    """Low-level ShotGrid find_one.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        fields: Fields to return.
        order: Sort order.

    Returns:
        Entity dict or None.
    """
    try:
        result = sg.find_one(entity_type, filters, fields=fields, order=order)
        return serialize_entity(result) if result else None
    except Exception as e:
        logger.error("sg.find_one failed: %s", e)
        raise ShotGridMCPError(f"sg.find_one failed: {e}") from e


def sg_create(sg: Shotgun, entity_type: EntityType, data: Dict[str, Any]) -> Dict[str, Any]:
    """Low-level ShotGrid create."""
    return create_entity_record(sg, entity_type, data)


def sg_update(sg: Shotgun, entity_type: EntityType, entity_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """Low-level ShotGrid update."""
    return update_entity_record(sg, entity_type, entity_id, data)


def sg_delete(sg: Shotgun, entity_type: EntityType, entity_id: int) -> bool:
    """Low-level ShotGrid delete."""
    return delete_entity_record(sg, entity_type, entity_id)


def sg_batch(sg: Shotgun, requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Low-level ShotGrid batch operation.

    Args:
        sg: ShotGrid connection.
        requests: List of batch request dicts (request_type, entity_type, etc.).

    Returns:
        List of result dicts.
    """
    try:
        result = sg.batch(requests)
        return [serialize_entity(r) for r in (result or [])]
    except Exception as e:
        logger.error("sg.batch failed: %s", e)
        raise ShotGridMCPError(f"sg.batch failed: {e}") from e


def sg_schema_entity_read(sg: Shotgun) -> Dict[str, Any]:
    """Read all entity types from ShotGrid schema."""
    try:
        result = sg.schema_entity_read()
        return result or {}
    except Exception as e:
        logger.error("sg.schema_entity_read failed: %s", e)
        raise ShotGridMCPError(f"sg.schema_entity_read failed: {e}") from e


def sg_schema_field_read(sg: Shotgun, entity_type: EntityType, field_name: Optional[str] = None) -> Dict[str, Any]:
    """Read field schema from ShotGrid.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        field_name: Optional specific field name.

    Returns:
        Field schema dict.
    """
    try:
        if field_name:
            result = sg.schema_field_read(entity_type, field_name)
        else:
            result = sg.schema_field_read(entity_type)
        return result or {}
    except Exception as e:
        logger.error("sg.schema_field_read failed: %s", e)
        raise ShotGridMCPError(f"sg.schema_field_read failed: {e}") from e


def sg_text_search(
    sg: Shotgun,
    text: str,
    entity_types: List[str],
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Full-text search across entities.

    Args:
        sg: ShotGrid connection.
        text: Search text.
        entity_types: Entity types to search in.
        fields: Optional fields to return.

    Returns:
        List of matching entity dicts.
    """
    try:
        result = sg.text_search(text, entity_types, fields=fields)
        return [serialize_entity(r) for r in (result or [])]
    except Exception as e:
        logger.error("sg.text_search failed: %s", e)
        raise ShotGridMCPError(f"sg.text_search failed: {e}") from e


def sg_revive(sg: Shotgun, entity_type: EntityType, entity_id: int) -> bool:
    """Revive a retired entity."""
    try:
        result = sg.revive(entity_type, entity_id)
        return bool(result)
    except Exception as e:
        logger.error("sg.revive failed: %s", e)
        raise ShotGridMCPError(f"sg.revive failed: {e}") from e


def sg_upload(
    sg: Shotgun,
    entity_type: EntityType,
    entity_id: int,
    field_name: str,
    file_path: str,
) -> Dict[str, Any]:
    """Upload a file to ShotGrid."""
    try:
        result = sg.upload(entity_type, entity_id, file_path, field_name=field_name)
        return {"status": "uploaded", "id": result}
    except Exception as e:
        logger.error("sg.upload failed: %s", e)
        raise ShotGridMCPError(f"sg.upload failed: {e}") from e


def sg_download_attachment(
    sg: Shotgun,
    attachment_id: int,
    output_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Download an attachment from ShotGrid."""
    try:
        sg.download_attachment(attachment_id, file_path=output_path)
        return {"status": "downloaded", "attachment_id": attachment_id, "path": output_path}
    except Exception as e:
        logger.error("sg.download_attachment failed: %s", e)
        raise ShotGridMCPError(f"sg.download_attachment failed: {e}") from e


def sg_summarize(
    sg: Shotgun,
    entity_type: EntityType,
    filters: List[Any],
    summarize_field: str,
) -> Dict[str, Any]:
    """Summarize entities grouped by a field.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Filter conditions.
        summarize_field: Field to group by.

    Returns:
        Dict with summary counts per field value.
    """
    try:
        result = sg.summarize(
            entity_type, filters=filters, summary_fields=[{"field": summarize_field, "type": "count"}]
        )
        return {"summarize_field": summarize_field, "groups": result or {}}
    except Exception as e:
        logger.error("sg.summarize failed: %s", e)
        raise ShotGridMCPError(f"sg.summarize failed: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Vendor operations
# ═══════════════════════════════════════════════════════════════════════════


def find_vendor_users(
    sg: Shotgun,
    name_contains: Optional[str] = None,
    email_contains: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Find vendor users by name or email.

    Args:
        sg: ShotGrid connection.
        name_contains: Optional name filter.
        email_contains: Optional email filter.

    Returns:
        List of user dicts.
    """
    try:
        filters: List[Any] = [["sg_status_list", "is", "act"]]
        if name_contains:
            filters.append(["name", "contains", name_contains])
        if email_contains:
            filters.append(["email", "contains", email_contains])

        fields = ["id", "name", "login", "email", "groups"]
        result = sg.find("HumanUser", filters, fields=fields)
        return [serialize_entity(user) for user in (result or [])]
    except Exception as e:
        logger.error("Failed to find vendor users: %s", e)
        raise ShotGridMCPError(f"Failed to find vendor users: {e}") from e


def find_vendor_versions(
    sg: Shotgun,
    project_id: int,
    vendor_id: Optional[int] = None,
    status: Optional[str] = None,
    days: int = 30,
) -> List[Dict[str, Any]]:
    """Find versions for vendor review.

    Args:
        sg: ShotGrid connection.
        project_id: Project ID.
        vendor_id: Optional vendor user ID.
        status: Optional status filter.
        days: Days to look back.

    Returns:
        List of version dicts.
    """
    try:
        from shotgrid_query import TimeFilter, TimeUnit

        filters: List[Any] = [["project", "is", {"type": "Project", "id": project_id}]]
        if vendor_id:
            filters.append(["user", "is", {"type": "HumanUser", "id": vendor_id}])
        if status:
            filters.append(["sg_status_list", "is", status])

        time_filter = TimeFilter(field="created_at", operator="in_last", count=days, unit=TimeUnit.DAY)
        filters.append(time_filter.to_filter().to_tuple())

        fields = ["id", "code", "sg_status_list", "user", "entity", "sg_task", "created_at"]
        result = sg.find("Version", filters, fields=fields, order=[{"field_name": "created_at", "direction": "desc"}])
        return [serialize_entity(v) for v in (result or [])]
    except Exception as e:
        logger.error("Failed to find vendor versions: %s", e)
        raise ShotGridMCPError(f"Failed to find vendor versions: {e}") from e


def create_vendor_playlist(
    sg: Shotgun,
    name: str,
    project_id: int,
    version_ids: Optional[List[int]] = None,
    vendor_user_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """Create a playlist for vendor review with access controls.

    Args:
        sg: ShotGrid connection.
        name: Playlist name.
        project_id: Project ID.
        version_ids: Version IDs to include.
        vendor_user_ids: Vendor user IDs for access.

    Returns:
        Dict with created playlist.
    """
    try:
        data: Dict[str, Any] = {
            "code": name,
            "description": "Vendor review playlist",
            "project": {"type": "Project", "id": project_id},
        }
        if version_ids:
            data["versions"] = [{"type": "Version", "id": vid} for vid in version_ids]
        result = sg.create("Playlist", data)
        return serialize_entity(result or {})
    except Exception as e:
        logger.error("Failed to create vendor playlist: %s", e)
        raise ShotGridMCPError(f"Failed to create vendor playlist: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# User and project helpers
# ═══════════════════════════════════════════════════════════════════════════


def find_active_projects(sg: Shotgun, days: int = 90) -> List[Dict[str, Any]]:
    """Find projects active in the last N days.

    Args:
        sg: ShotGrid connection.
        days: Days to look back (default: 90).

    Returns:
        List of project dicts.
    """
    try:
        from shotgrid_query import TimeFilter, TimeUnit

        time_filter = TimeFilter(field="updated_at", operator="in_last", count=days, unit=TimeUnit.DAY)
        filters = [time_filter.to_filter().to_tuple()]
        fields = ["id", "name", "sg_status", "updated_at", "updated_by"]
        order = [{"field_name": "updated_at", "direction": "desc"}]
        result = sg.find("Project", filters, fields=fields, order=order, page=1)
        return [serialize_entity(p) for p in (result or [])]
    except Exception as e:
        logger.error("Failed to find active projects: %s", e)
        raise ShotGridMCPError(f"Failed to find active projects: {e}") from e


def find_active_users(sg: Shotgun, days: int = 30) -> List[Dict[str, Any]]:
    """Find users active in the last N days.

    Notes:
        Uses ``updated_at`` as a proxy for activity since
        ``HumanUser`` entities lack a ``last_login`` field.

    Args:
        sg: ShotGrid connection.
        days: Days to look back (default: 30).

    Returns:
        List of user dicts.
    """
    try:
        from shotgrid_query import FilterModel, TimeFilter, TimeUnit

        status_filter = FilterModel(field="sg_status_list", operator="is", value="act")
        time_filter = TimeFilter(field="updated_at", operator="in_last", count=days, unit=TimeUnit.DAY)
        filters = [status_filter.to_tuple(), time_filter.to_filter().to_tuple()]
        fields = ["id", "name", "login", "email", "updated_at"]
        order = [{"field_name": "updated_at", "direction": "desc"}]
        result = sg.find("HumanUser", filters, fields=fields, order=order)
        return [serialize_entity(user) for user in (result or [])]
    except Exception as e:
        logger.error("Failed to find active users: %s", e)
        raise ShotGridMCPError(f"Failed to find active users: {e}") from e


def find_entities_by_date_range(
    sg: Shotgun,
    entity_type: EntityType,
    date_field: str,
    start_date: str,
    end_date: str,
    additional_filters: Optional[List[Any]] = None,
    fields: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Find entities within a date range.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        date_field: Date field to filter on.
        start_date: Start date (auto-normalized).
        end_date: End date (auto-normalized).
        additional_filters: Additional filters.
        fields: Fields to return.

    Returns:
        List of entity dicts.
    """
    try:
        from shotgrid_mcp_server.api_models import _normalize_datetime_value

        normalized_start = _normalize_datetime_value(start_date)
        normalized_end = _normalize_datetime_value(end_date)
        from shotgrid_query import FilterModel

        date_filter = FilterModel(field=date_field, operator="between", value=[normalized_start, normalized_end])
        filters = [date_filter.to_tuple()]

        if additional_filters:
            for f in additional_filters:
                if hasattr(f, "to_tuple"):
                    filters.append(f.to_tuple())
                else:
                    filters.append(f)

        default_fields = ["id", "code", date_field] if date_field not in (fields or []) else fields
        result = sg.find(entity_type, filters, fields=fields or default_fields, page=1)
        return [serialize_entity(e) for e in (result or [])]
    except Exception as e:
        logger.error("Failed to find entities by date range: %s", e)
        raise ShotGridMCPError(f"Failed to find entities by date range: {e}") from e


# ═══════════════════════════════════════════════════════════════════════════
# Aliases — backward compatibility with skill script imports
# ═══════════════════════════════════════════════════════════════════════════


# CRUD aliases
create_sg_entity = create_entity_record
delete_sg_entity = delete_entity_record
update_sg_entity = update_entity_record
read_sg_entity = read_entity_record
get_sg_entity_schema = get_entity_schema

# Note aliases
create_sg_note = create_note
read_sg_notes = get_entity_notes
update_sg_note = update_note

# Search aliases
find_one_sg_entity = execute_find_one
search_sg_entities = execute_search
search_sg_entities_with_related = execute_find_with_related
find_active_sg_projects = find_active_projects
find_active_sg_users = find_active_users
find_sg_entities_by_date = find_entities_by_date_range


# Advanced search with time filters
def sg_search_advanced(
    sg: Shotgun,
    entity_type: EntityType,
    filters: Optional[List[Any]] = None,
    time_filters: Optional[List[Any]] = None,
    fields: Optional[List[str]] = None,
    related_fields: Optional[Dict[str, List[str]]] = None,
    order: Optional[List[Dict[str, Any]]] = None,
    limit: Optional[int] = None,
    filter_operator: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Advanced search with time-based filters and related fields.

    This is a convenience wrapper that combines execute_search with
    time-filter conversion and related-field support.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        filters: Standard filter conditions.
        time_filters: Time-based filter conditions (in_last, in_next, etc.).
        fields: Fields to return.
        related_fields: Related entity fields.
        order: Sort order.
        limit: Max results.
        filter_operator: Logical operator.

    Returns:
        List of entity dicts.
    """
    from shotgrid_query import process_filters

    # Process standard filters
    all_filters = list(filters or [])

    # Convert time filters
    if time_filters:
        for tf in time_filters:
            if hasattr(tf, "to_tuple"):
                all_filters.append(tf.to_tuple())
            elif isinstance(tf, dict) and "field" in tf:
                all_filters.append(
                    [tf["field"], tf.get("operator", "in_last"), tf.get("count", 0), tf.get("unit", "DAY")]
                )
            else:
                all_filters.append(tf)

    processed_filters = process_filters(all_filters)

    # Build all_fields with related entities via dot notation
    all_fields = list(fields or [])
    if related_fields:
        for entity_field, related_field_list in related_fields.items():
            field_info = sg.schema_field_read(entity_type, entity_field)
            if not field_info:
                continue
            valid_types = field_info.get("properties", {}).get("valid_types", {}).get("value", [])
            if not valid_types:
                continue
            for related_field in related_field_list:
                related_entity_type = valid_types[0]
                all_fields.append(f"{entity_field}.{related_entity_type}.{related_field}")

    # Use execute_search for the actual query
    return execute_search(
        sg=sg,
        entity_type=entity_type,
        filters=processed_filters,
        fields=all_fields,
        order=order,
        limit=limit,
        filter_operator=filter_operator,
    )


def batch_download_thumbnails(
    sg: Shotgun,
    entity_type: EntityType,
    entity_ids: List[int],
    field_name: str = "image",
    output_dir: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Download multiple thumbnails in batch.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type.
        entity_ids: List of entity IDs.
        field_name: Thumbnail field name (default: "image").
        output_dir: Optional output directory.

    Returns:
        List of download result dicts.
    """
    import os

    results = []
    for entity_id in entity_ids:
        try:
            path = os.path.join(output_dir, f"{entity_type}_{entity_id}.png") if output_dir else None
            result = download_thumbnail(sg, entity_type, entity_id, field_name, path)
            results.append({"entity_id": entity_id, **result})
        except Exception as e:
            results.append({"entity_id": entity_id, "status": "error", "error": str(e)})
    return results
