"""Tests for the MCP Apps (interactive UI) integration."""

from __future__ import annotations

# Import built-in modules
from typing import Any, Dict
from unittest.mock import MagicMock

# Import third-party modules
import pytest
from fastmcp import Client, FastMCP
from shotgun_api3.lib.mockgun import Shotgun

# Import local modules
from shotgrid_mcp_server.apps import DASHBOARD_RESOURCE_URI, register_apps
from shotgrid_mcp_server.apps import dashboard as dashboard_module
from shotgrid_mcp_server.schema_resources import register_schema_resources

APP_MIME_TYPE = "text/html;profile=mcp-app"
DASHBOARD_TOOL_NAME = "shotgrid_dashboard"


@pytest.fixture
def app_server(mock_sg: Shotgun) -> FastMCP:
    """Server carrying the dashboard app plus the pre-existing schema resources."""
    server: FastMCP = FastMCP(name="test-apps")
    register_apps(server, mock_sg)
    register_schema_resources(server, mock_sg)
    return server


def test_dashboard_html_is_a_single_self_contained_document() -> None:
    """The committed bundle must not reference any external asset."""

    html = dashboard_module.load_dashboard_html()

    assert html.lstrip().lower().startswith("<!doctype html")
    assert "<html" in html.lower()
    assert "</html>" in html.lower()
    assert 'src="http' not in html
    assert 'href="http' not in html


def test_load_dashboard_html_is_cached() -> None:
    """Reading the bundle repeatedly must hit the cache, not the disk."""

    dashboard_module.load_dashboard_html.cache_clear()
    first = dashboard_module.load_dashboard_html()
    second = dashboard_module.load_dashboard_html()

    assert first is second
    assert dashboard_module.load_dashboard_html.cache_info().hits >= 1


def test_build_dashboard_payload_groups_by_status(mock_sg: Shotgun) -> None:
    """Payload counts each status once and keeps the shares consistent."""

    payload = dashboard_module.build_dashboard_payload(mock_sg, "Task")

    assert payload["entity_type"] == "Task"
    assert payload["total"] == len(payload["entities"])
    assert payload["project"] is None
    assert payload["generated_at"]

    counts = {bucket["status"]: bucket["count"] for bucket in payload["breakdown"]}
    assert sum(counts.values()) == payload["total"]

    # The fixture creates one task per status: ip / wtg / rdy.
    assert counts.get("ip") == 1
    assert counts.get("wtg") == 1
    assert counts.get("rdy") == 1

    for bucket in payload["breakdown"]:
        assert bucket["label"]
        assert 0.0 <= bucket["share"] <= 100.0

    for entity in payload["entities"]:
        assert entity["label"]
        assert entity["status"]
        assert entity["status_label"]


def test_build_dashboard_payload_filters_by_project(mock_sg: Shotgun) -> None:
    """A project filter is forwarded to ShotGrid and echoed back."""

    project = mock_sg.find_one("Project", [], ["id"]) or {}

    payload = dashboard_module.build_dashboard_payload(mock_sg, "Task", project_id=project.get("id"))

    assert payload["project"] is not None
    assert payload["project"]["id"] == project.get("id")


def test_build_dashboard_payload_clamps_the_limit(mock_sg: Shotgun) -> None:
    """Non-positive limits are lifted to 1 and huge limits are capped."""

    single = dashboard_module.build_dashboard_payload(mock_sg, "Task", limit=-5)
    assert single["total"] <= 1

    capped = dashboard_module.build_dashboard_payload(mock_sg, "Task", limit=10_000)
    assert capped["total"] <= dashboard_module.MAX_LIMIT


def test_build_dashboard_payload_reports_truncation(mock_sg: Shotgun) -> None:
    """`truncated` is true only once the limit caps the result."""

    payload = dashboard_module.build_dashboard_payload(mock_sg, "Task", limit=1)
    assert payload["total"] == 1
    assert payload["truncated"] is True


def test_format_dashboard_text_covers_the_payload() -> None:
    """The text fallback repeats the breakdown and the entity list."""

    payload: Dict[str, Any] = {
        "entity_type": "Task",
        "total": 3,
        "truncated": False,
        "breakdown": [
            {"status": "ip", "label": "In Progress", "count": 2, "share": 66.67},
            {"status": "fin", "label": "Final", "count": 1, "share": 33.33},
        ],
        "entities": [
            {"label": "anim", "status": "ip", "status_label": "In Progress", "detail": ""},
        ],
    }

    text = dashboard_module.format_dashboard_text(payload)

    assert "Task" in text
    assert "In Progress: 2 (66.67%)" in text
    assert "Final: 1 (33.33%)" in text
    assert "- anim [In Progress]" in text


def test_format_dashboard_text_handles_an_empty_result() -> None:
    """An empty dashboard still produces readable text."""

    text = dashboard_module.format_dashboard_text({"entity_type": "Asset", "total": 0, "breakdown": [], "entities": []})

    assert "0 entities" in text
    assert "No entities found." in text


@pytest.mark.asyncio
async def test_app_resource_is_served_with_the_apps_mime_type(app_server: FastMCP) -> None:
    """`resources/read` on the ui:// URI returns an mcp-app HTML document."""

    async with Client(app_server) as client:
        result = await client.read_resource(DASHBOARD_RESOURCE_URI)

    contents = list(result)
    assert len(contents) == 1
    assert contents[0].mime_type == APP_MIME_TYPE
    assert "<!doctype html" in str(contents[0].text).lower()


@pytest.mark.asyncio
async def test_app_tool_declares_the_ui_resource(app_server: FastMCP) -> None:
    """`tools/list` exposes `_meta.ui.resourceUri` for the dashboard tool."""

    async with Client(app_server) as client:
        tools = await client.list_tools()

    dashboard = next(tool for tool in tools if tool.name == DASHBOARD_TOOL_NAME)
    meta = dashboard.meta or {}
    ui_meta = meta.get("ui") if isinstance(meta, dict) else None

    assert ui_meta is not None, f"expected _meta.ui on the tool, got {meta}"
    assert ui_meta["resourceUri"] == DASHBOARD_RESOURCE_URI
    assert "model" in ui_meta["visibility"]
    assert "app" in ui_meta["visibility"]


@pytest.mark.asyncio
async def test_ui_resource_coexists_with_schema_resources(app_server: FastMCP) -> None:
    """The ui:// resource must not displace the existing shotgrid://schema/* ones."""

    async with Client(app_server) as client:
        resources = await client.list_resources()

    uris = [str(resource.uri) for resource in resources]

    assert DASHBOARD_RESOURCE_URI in uris
    assert "shotgrid://schema/entities" in uris
    assert "shotgrid://schema/statuses" in uris


@pytest.mark.asyncio
async def test_dashboard_tool_falls_back_to_text_without_apps_support(app_server: FastMCP) -> None:
    """A client that never negotiated Apps gets the plain-text summary."""

    async with Client(app_server) as client:
        result = await client.call_tool(DASHBOARD_TOOL_NAME, {"entity_type": "Task"})

    payload = result.structured_content or {}
    assert payload["entity_type"] == "Task"
    assert payload["apps_supported"] is False
    assert "status overview" in payload["text"]

    text_blocks = [block.text for block in result.content if hasattr(block, "text")]
    assert any("status overview" in block for block in text_blocks)


@pytest.mark.asyncio
async def test_dashboard_tool_returns_data_for_a_real_query(app_server: FastMCP) -> None:
    """The tool runs an actual ShotGrid query and summarises the result."""

    async with Client(app_server) as client:
        result = await client.call_tool(DASHBOARD_TOOL_NAME, {"entity_type": "Asset"})

    payload = result.structured_content or {}
    assert payload["entity_type"] == "Asset"
    assert payload["total"] > 0
    assert payload["breakdown"]
    assert payload["entities"]


def test_status_labels_come_from_the_status_list_schema() -> None:
    """Display labels are resolved from a real status_list field schema."""

    sg = MagicMock()
    sg.schema_field_read.return_value = {
        "sg_status_list": {
            "data_type": {"value": "status_list"},
            "properties": {
                "valid_values": {"value": ["wtg", "ip", "fin"]},
                "display_values": {"value": {"wtg": "Waiting to Start", "ip": "In Progress", "fin": "Approved"}},
            },
        }
    }

    labels = dashboard_module._status_labels(sg, "Task")

    assert labels == {"wtg": "Waiting to Start", "ip": "In Progress", "fin": "Approved"}


def test_status_labels_fall_back_to_the_raw_code() -> None:
    """Without display values the status code is used as its own label."""

    sg = MagicMock()
    sg.schema_field_read.return_value = {
        "sg_status_list": {
            "data_type": {"value": "status_list"},
            "properties": {"valid_values": {"value": ["ip", "fin"]}},
        }
    }

    assert dashboard_module._status_labels(sg, "Task") == {"ip": "ip", "fin": "fin"}


def test_status_labels_degrade_when_schema_cannot_be_read() -> None:
    """A schema failure must not break the dashboard."""

    sg = MagicMock()
    sg.schema_field_read.side_effect = RuntimeError("no permission")

    assert dashboard_module._status_labels(sg, "Task") == {}
