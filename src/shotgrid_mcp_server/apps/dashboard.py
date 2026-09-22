"""ShotGrid status dashboard — the first MCP App for this server.

Two things get registered here:

* a ``ui://shotgrid/dashboard`` resource serving the single-file HTML bundle
  built from ``web/``, under the ``text/html;profile=mcp-app`` MIME type;
* the :func:`shotgrid_dashboard` tool, which carries
  ``_meta.ui.resourceUri`` so an MCP Apps host renders that bundle.

Hosts that did not negotiate the Apps extension still get a plain-text
summary of the very same data, per SEP-2133 graceful degradation.
"""

from __future__ import annotations

# Import built-in modules
import functools
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import third-party modules
from fastmcp import Context
from fastmcp.apps import UI_MIME_TYPE, AppConfig
from fastmcp.tools import ToolResult
from mcp.server.apps import client_supports_apps
from mcp.types import TextContent
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.tools.base import handle_error
from shotgrid_mcp_server.tools.types import FastMCPType

logger = logging.getLogger(__name__)

DASHBOARD_RESOURCE_URI = "ui://shotgrid/dashboard"
"""URI of the dashboard UI resource, referenced by the tool's ``_meta.ui``."""

DASHBOARD_TOOL_NAME = "shotgrid_dashboard"
"""Name of the tool that renders the dashboard."""

_HTML_PATH = Path(__file__).parent / "dashboard" / "index.html"
"""Location of the committed single-file UI bundle."""

DEFAULT_ENTITY_TYPE = "Task"
DEFAULT_LIMIT = 200
MAX_LIMIT = 1000

_STATUS_FIELD = "sg_status_list"
"""ShotGrid's conventional status field; entities without it are counted once."""

_ENTITY_LABEL_FIELDS = ("code", "name", "title", "content", "subject")
"""Candidate fields used to build a human-readable label for an entity."""

_ENTITY_DETAIL_FIELDS = (
    "description",
    "entity",
    "project",
    "assigned_to",
    "sg_sequence",
    "updated_at",
)
"""Fields rendered in the dashboard's detail column."""


@functools.lru_cache(maxsize=1)
def load_dashboard_html() -> str:
    """Return the single-file dashboard HTML bundle.

    The bundle is produced by ``web/`` (Vite + ``vite-plugin-singlefile``)
    and committed to the package, so no Node toolchain is needed at runtime.
    The result is cached: the resource is read on every ``resources/read``
    and the file never changes while the process is alive.

    Returns:
        str: The HTML document to hand to the host.

    Raises:
        FileNotFoundError: If the bundle is missing from the installation.
    """
    return _HTML_PATH.read_text(encoding="utf-8")


def _status_labels(sg: Shotgun, entity_type: str) -> Dict[str, str]:
    """Map ShotGrid status codes to their display labels.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type to read the status schema for.

    Returns:
        Dict[str, str]: Status code -> display label. Empty when the entity
            type has no status field or the schema cannot be read.
    """
    try:
        field_schema = sg.schema_field_read(entity_type, _STATUS_FIELD)
    except Exception as exc:  # noqa: BLE001 - schema is best-effort only
        logger.debug("No status schema for %s: %s", entity_type, exc)
        return {}

    if not isinstance(field_schema, dict):
        return {}

    properties = (field_schema.get(_STATUS_FIELD) or {}).get("properties") or {}
    valid_values = (properties.get("valid_values") or {}).get("value") or []
    display_values = (properties.get("display_values") or {}).get("value") or {}

    labels: Dict[str, str] = {}
    for code in valid_values:
        labels[code] = display_values.get(code, code) if isinstance(display_values, dict) else code
    return labels


def _status_label(labels: Dict[str, str], status: str) -> str:
    """Resolve a status code to its display label.

    Falls back to the raw status code rather than a placeholder such as
    ``"Unknown"``: the breakdown buckets and the entity rows are rendered
    side by side, so both must resolve the very same way or the dashboard
    shows two different names for one status.

    Args:
        labels: Status code -> display label mapping.
        status: Raw ShotGrid status code.

    Returns:
        str: The display label, or ``status`` when it has none.
    """
    return labels.get(status, status)


def _project_summary(sg: Shotgun, project_id: int) -> Dict[str, Any]:
    """Look up the real name of the project the dashboard is filtered to.

    Args:
        sg: ShotGrid connection.
        project_id: Id of the project to describe.

    Returns:
        Dict[str, Any]: ``{"id", "name"}`` for the project. The name is read
            from ShotGrid; a synthetic ``"Project <id>"`` label is only used
            when the project cannot be read (missing, deleted, or hidden by
            permissions), because a fabricated name on the dashboard is
            worse than an obviously synthetic one.
    """
    project_id = int(project_id)
    fallback = f"Project {project_id}"

    try:
        project = sg.find_one("Project", [["id", "is", project_id]], ["name", "code"])
    except Exception as exc:  # noqa: BLE001 - the name is cosmetic, never fatal
        logger.debug("Could not read Project %s: %s", project_id, exc)
        return {"id": project_id, "name": fallback}

    if not isinstance(project, dict):
        return {"id": project_id, "name": fallback}

    name = project.get("name") or project.get("code")
    return {"id": project_id, "name": str(name) if name else fallback}


def _entity_label(entity: Dict[str, Any], entity_type: str, entity_id: Any) -> str:
    """Build a human-readable label for an entity."""
    for field in _ENTITY_LABEL_FIELDS:
        value = entity.get(field)
        if isinstance(value, str) and value.strip():
            return value.strip()
    if entity_id is not None:
        return f"{entity_type} #{entity_id}"
    return entity_type


def _entity_detail(entity: Dict[str, Any]) -> str:
    """Build the dashboard's secondary description column for an entity."""
    parts: List[str] = []
    for field in _ENTITY_DETAIL_FIELDS:
        value = entity.get(field)
        if value is None:
            continue
        if isinstance(value, dict):
            value = value.get("name") or value.get("code") or value.get("id")
        if value is None or value == "":
            continue
        parts.append(str(value))
        if len(parts) == 2:
            break
    return " · ".join(parts)


def build_dashboard_payload(
    sg: Shotgun,
    entity_type: str = DEFAULT_ENTITY_TYPE,
    project_id: Optional[int] = None,
    limit: int = DEFAULT_LIMIT,
) -> Dict[str, Any]:
    """Collect the data rendered by the dashboard UI.

    Args:
        sg: ShotGrid connection.
        entity_type: Entity type to summarise (for example ``"Task"``).
        project_id: Optional project filter.
        limit: Maximum number of entities to fetch.

    Returns:
        Dict[str, Any]: JSON-serialisable dashboard payload.
    """
    if limit < 1:
        limit = 1
    limit = min(limit, MAX_LIMIT)

    filters: List[List[Any]] = []
    if project_id is not None:
        filters.append(["project", "is", {"type": "Project", "id": int(project_id)}])

    # dict.fromkeys keeps the field order deterministic across processes;
    # a set literal would reorder it with PYTHONHASHSEED.
    fields = list(dict.fromkeys(("id", _STATUS_FIELD, *_ENTITY_LABEL_FIELDS, *_ENTITY_DETAIL_FIELDS)))
    try:
        entities = sg.find(entity_type, filters, fields, limit=limit) or []
    except Exception as err:
        handle_error(err, operation="build_dashboard_payload")
        raise  # pragma: no cover - handle_error always raises

    labels = _status_labels(sg, entity_type)

    counts: Dict[str, int] = {}
    for entity in entities:
        status = entity.get(_STATUS_FIELD) or "unknown"
        counts[status] = counts.get(status, 0) + 1

    total = len(entities)
    breakdown = [
        {
            "status": status,
            "label": _status_label(labels, status),
            "count": count,
            "share": round(count * 100.0 / total, 2) if total else 0.0,
        }
        for status, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    project: Optional[Dict[str, Any]] = None
    if project_id is not None:
        project = _project_summary(sg, int(project_id))

    entity_rows: List[Dict[str, Any]] = []
    for entity in entities:
        status = entity.get(_STATUS_FIELD) or "unknown"
        entity_rows.append(
            {
                "id": entity.get("id"),
                "label": _entity_label(entity, entity_type, entity.get("id")),
                "status": status,
                "status_label": _status_label(labels, status),
                "detail": _entity_detail(entity),
            }
        )

    return {
        "entity_type": entity_type,
        "project": project,
        "total": total,
        "truncated": total >= limit,
        "breakdown": breakdown,
        "entities": entity_rows,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def format_dashboard_text(payload: Dict[str, Any]) -> str:
    """Render the dashboard payload as plain text for hosts without Apps support.

    Args:
        payload: Payload produced by :func:`build_dashboard_payload`.

    Returns:
        str: Human-readable summary.
    """
    entity_type = payload.get("entity_type", DEFAULT_ENTITY_TYPE)
    total = payload.get("total", 0)
    lines = [f"ShotGrid {entity_type} status overview — {total} entities"]

    breakdown = payload.get("breakdown") or []
    if breakdown:
        lines.append("")
        for bucket in breakdown:
            lines.append(f"  {bucket['label']}: {bucket['count']} ({bucket['share']}%)")
    else:
        lines.append("")
        lines.append("  No entities found.")

    entities = payload.get("entities") or []
    if entities:
        lines.append("")
        lines.append("Entities:")
        for entity in entities[:25]:
            lines.append(f"  - {entity['label']} [{entity['status_label']}]")
        if len(entities) > 25:
            lines.append(f"  ... and {len(entities) - 25} more")

    if payload.get("truncated"):
        lines.append("")
        lines.append("Note: results were truncated by the requested limit.")

    return "\n".join(lines)


def register_dashboard_app(server: FastMCPType, sg: Shotgun) -> None:
    """Register the dashboard ``ui://`` resource and its bound tool.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection (may be a mock in lazy-connection mode).
    """

    @server.resource(DASHBOARD_RESOURCE_URI, mime_type=UI_MIME_TYPE)
    def dashboard_ui() -> str:
        """Single-file HTML UI for the ShotGrid status dashboard."""
        return load_dashboard_html()

    @server.tool(
        DASHBOARD_TOOL_NAME,
        app=AppConfig(resource_uri=DASHBOARD_RESOURCE_URI, visibility=["model", "app"]),
    )
    def shotgrid_dashboard(
        entity_type: str = DEFAULT_ENTITY_TYPE,
        project_id: Optional[int] = None,
        limit: int = DEFAULT_LIMIT,
        ctx: Optional[Context] = None,
    ) -> ToolResult:
        """Summarise ShotGrid entity statuses and render them in an interactive dashboard.

        **When to use this tool:**
        - You need an overview of how work is distributed across statuses
        - The user asks for a dashboard, board, or status breakdown
        - You want a visual summary of tasks, assets, shots, or versions

        **When NOT to use this tool:**
        - To change entity status - Use `update_entity` instead
        - To search with complex filters - Use `search_entities` instead
        - To read a single entity - Use `find_one_entity` instead

        Args:
            entity_type: Entity type to summarise.
                Common values: "Task", "Asset", "Shot", "Version", "PublishedFile".
            project_id: Optional Project id to restrict the summary to one project.
            limit: Maximum number of entities to load (1-1000).
            ctx: FastMCP context, injected by the server.

        Returns:
            Dictionary containing:
            - entity_type: The summarised entity type
            - project: Project filter, or null
            - total: Number of entities loaded
            - truncated: Whether `limit` capped the result
            - breakdown: List of {status, label, count, share} buckets
            - entities: List of {id, label, status, status_label, detail}
            - generated_at: UTC timestamp of the query

            The summary above is returned as the tool's text content as well,
            so hosts without MCP Apps support render it as plain text.

        Raises:
            ToolError: If ShotGrid cannot be queried.

        Examples:
            Task overview for the whole site:
            {
                "entity_type": "Task"
            }

            Asset overview for one project:
            {
                "entity_type": "Asset",
                "project_id": 123
            }
        """
        payload = build_dashboard_payload(sg, entity_type, project_id, limit)

        supported = False
        if ctx is not None:
            try:
                supported = client_supports_apps(ctx)
            except Exception as exc:  # noqa: BLE001 - degradation must never break the tool
                logger.debug("Could not determine Apps support: %s", exc)
                supported = False

        payload["apps_supported"] = supported

        # The text content is what a host without MCP Apps support renders, so
        # it must be the readable summary. Returning the payload alone would
        # hand the model a JSON blob holding every fetched entity instead.
        # Apps hosts read ``structured_content`` and ignore this block.
        return ToolResult(
            content=[TextContent(type="text", text=format_dashboard_text(payload))],
            structured_content=payload,
        )
