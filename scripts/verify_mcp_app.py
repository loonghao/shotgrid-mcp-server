"""Verify the MCP Apps integration against a live HTTP server over raw JSON-RPC.

Starts the real FastMCP HTTP server in a background thread and drives it with
hand-written JSON-RPC 2.0 requests (``initialize``, ``resources/list``,
``tools/list``, ``resources/read``, ``tools/call``), then prints the wire
responses and asserts the acceptance criteria.

Usage:
    python scripts/verify_mcp_app.py [--port 8123] [--apps|--no-apps]

``--no-apps`` omits the ``capabilities.extensions`` advertisement, so the
``tools/call`` below takes the graceful-degradation path and the tool's text
content is asserted to be the readable summary rather than a JSON dump.
"""

from __future__ import annotations

# Import built-in modules
import argparse
import json
import threading
import time
from typing import Any, Dict, List, Optional

# Import third-party modules
import httpx
import uvicorn
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.apps import DASHBOARD_RESOURCE_URI, register_apps
from shotgrid_mcp_server.schema_resources import register_schema_resources

APP_MIME_TYPE = "text/html;profile=mcp-app"
UI_EXTENSION_ID = "io.modelcontextprotocol/ui"
DASHBOARD_TOOL_NAME = "shotgrid_dashboard"

SCHEMA_RESOURCE_URIS = ("shotgrid://schema/entities", "shotgrid://schema/statuses")


class _StubConnection:
    """In-memory ShotGrid stand-in covering what the dashboard tool queries.

    Resource and tool discovery never touch the connection, but ``tools/call``
    does, so this implements exactly the three methods the dashboard uses.
    """

    PROJECTS: Dict[int, Dict[str, Any]] = {
        1: {"id": 1, "name": "Main Project", "code": "main"},
    }

    TASKS: List[Dict[str, Any]] = [
        {
            "id": 1,
            "code": "TASK_001",
            "content": "Hero Modeling",
            "sg_status_list": "ip",
            "description": "Model the hero asset",
            "project": {"type": "Project", "id": 1, "name": "Main Project"},
        },
        {
            "id": 2,
            "code": "TASK_002",
            "content": "Hero Rigging",
            "sg_status_list": "wtg",
            "description": "Rig the hero asset",
            "project": {"type": "Project", "id": 1, "name": "Main Project"},
        },
        {
            "id": 3,
            "code": "TASK_003",
            "content": "Shot Animation",
            "sg_status_list": "ip",
            "description": "Animate the opening shot",
            "project": {"type": "Project", "id": 1, "name": "Main Project"},
        },
    ]

    STATUS_LABELS: Dict[str, str] = {
        "ip": "In Progress",
        "wtg": "Waiting to Start",
        "fin": "Approved",
    }

    def find(
        self,
        entity_type: str,
        filters: Optional[List[Any]] = None,
        fields: Optional[List[str]] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        rows = list(self.TASKS) if entity_type == "Task" else []

        for condition in filters or []:
            if condition[0] == "project":
                project_id = (condition[2] or {}).get("id")
                rows = [row for row in rows if (row.get("project") or {}).get("id") == project_id]

        if limit:
            rows = rows[:limit]

        if fields:
            return [{field: row.get(field) for field in fields} for row in rows]
        return rows

    def find_one(
        self,
        entity_type: str,
        filters: Optional[List[Any]] = None,
        fields: Optional[List[str]] = None,
    ) -> Optional[Dict[str, Any]]:
        if entity_type == "Project":
            for condition in filters or []:
                if condition[0] == "id":
                    project = self.PROJECTS.get(condition[2])
                    if project is None:
                        return None
                    return {field: project.get(field) for field in fields or project}
            return None

        rows = self.find(entity_type, filters, fields)
        return rows[0] if rows else None

    def schema_field_read(
        self,
        entity_type: str,
        field_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        if field_name != "sg_status_list":
            return {}
        return {
            field_name: {
                "data_type": {"value": "status_list"},
                "properties": {
                    "valid_values": {"value": list(self.STATUS_LABELS)},
                    "display_values": {"value": dict(self.STATUS_LABELS)},
                },
            }
        }


def build_server() -> FastMCP:
    """Build a server carrying the dashboard app plus the existing schema resources."""
    mcp: FastMCP = FastMCP(name="shotgrid-server")
    register_apps(mcp, _StubConnection())
    register_schema_resources(mcp, _StubConnection())
    return mcp


class Response:
    """Read a Streamable HTTP response as JSON, handling SSE and JSON bodies."""

    def __init__(self, raw: httpx.Response) -> None:
        self._raw = raw
        self._data: Optional[Dict[str, Any]] = None

    @property
    def status_code(self) -> int:
        return self._raw.status_code

    @property
    def headers(self) -> Any:
        return self._raw.headers

    def json(self) -> Dict[str, Any]:
        if self._data is None:
            content_type = self._raw.headers.get("content-type", "")
            if "text/event-stream" in content_type:
                payload: Optional[Dict[str, Any]] = None
                for line in self._raw.text.splitlines():
                    if line.startswith("data:"):
                        payload = json.loads(line[len("data:") :].strip())
                self._data = payload or {}
            else:
                self._data = self._raw.json()
        return self._data


def _wait_until_ready(url: str, attempts: int = 100) -> None:
    for _ in range(attempts):
        try:
            httpx.get(url, timeout=0.5)
        except Exception:  # noqa: BLE001 - server may not listen yet
            time.sleep(0.2)
        else:
            return
    raise RuntimeError(f"Server at {url} did not become ready")


def show(title: str, response: Response) -> None:
    """Print one JSON-RPC exchange."""
    print()
    print(f"===== {title} =====")
    print(f"HTTP {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


def _result(response: Response) -> Dict[str, Any]:
    return response.json().get("result", {})


def _text_blocks(result: Dict[str, Any]) -> List[str]:
    return [block.get("text", "") for block in result.get("content", []) if block.get("type") == "text"]


def check_tool_meta(tools: Response, failures: List[str]) -> None:
    """The dashboard tool must advertise ``_meta.ui.resourceUri``."""
    entries = _result(tools).get("tools", [])
    dashboard = next((entry for entry in entries if entry.get("name") == DASHBOARD_TOOL_NAME), None)

    if dashboard is None:
        failures.append(f"tool {DASHBOARD_TOOL_NAME!r} missing from tools/list")
        return

    resource_uri = (dashboard.get("_meta", {}).get("ui", {}) or {}).get("resourceUri")
    if resource_uri != DASHBOARD_RESOURCE_URI:
        failures.append(f"_meta.ui.resourceUri is {resource_uri!r}")


def check_resource(read: Response, failures: List[str]) -> None:
    """The ``ui://`` resource must be a single self-contained HTML document."""
    contents = _result(read).get("contents", [])

    if not contents:
        failures.append(f"resources/read returned no contents for {DASHBOARD_RESOURCE_URI}")
        return

    mime = contents[0].get("mimeType")
    if mime != APP_MIME_TYPE:
        failures.append(f"resource mimeType is {mime!r}, expected {APP_MIME_TYPE!r}")

    html = contents[0].get("text", "")
    if not html.lstrip().lower().startswith("<!doctype html"):
        failures.append("resource text is not an HTML document")

    for token in ('src="http', 'href="http'):
        if token in html:
            failures.append(f"HTML bundle references an external asset ({token})")


def check_coexistence(resources: Response, failures: List[str]) -> None:
    """The ``ui://`` resource must not displace the existing schema resources."""
    uris = [str(entry.get("uri")) for entry in _result(resources).get("resources", [])]

    if DASHBOARD_RESOURCE_URI not in uris:
        failures.append(f"{DASHBOARD_RESOURCE_URI} missing from resources/list")

    for uri in SCHEMA_RESOURCE_URIS:
        if uri not in uris:
            failures.append(f"{uri} missing from resources/list")


def check_dashboard_call(call: Response, failures: List[str], apps_advertised: bool) -> None:
    """The tool must return structured data plus a readable text summary."""
    result = _result(call)
    if not result:
        failures.append("tools/call returned no result")
        return

    if result.get("isError"):
        failures.append(f"tools/call failed: {_text_blocks(result)}")
        return

    payload = result.get("structuredContent") or {}
    if not payload:
        failures.append("tools/call returned no structuredContent")

    # The whole point of --no-apps: a host without Apps support must be handed
    # the readable summary, not a JSON blob holding every fetched entity.
    blocks = _text_blocks(result)
    if not blocks:
        failures.append("tools/call returned no text content block")
    else:
        summary = blocks[0]
        if not summary.startswith("ShotGrid "):
            failures.append("text content is not the plain-text summary")
        if summary.lstrip().startswith("{"):
            failures.append("text content is a JSON dump, not the plain-text summary")

    expected_support = apps_advertised
    if payload and payload.get("apps_supported") is not expected_support:
        failures.append(f"apps_supported is {payload.get('apps_supported')!r}, expected {expected_support!r}")

    # The project card must show the real ShotGrid name, not "Project <id>".
    project = payload.get("project")
    if project and project.get("name") == f"Project {project.get('id')}":
        failures.append(f"project name is the synthetic fallback {project.get('name')!r}")


def main() -> int:
    """Run the verification and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8123)
    parser.add_argument(
        "--no-apps",
        action="store_true",
        help="Do not advertise the Apps extension, exercising the text fallback.",
    )
    args = parser.parse_args()

    app = build_server().http_app(path="/mcp")
    config = uvicorn.Config(app, host="127.0.0.1", port=args.port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{args.port}/mcp"
    _wait_until_ready(url)

    headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    session_id: Optional[str] = None

    def rpc(payload: Dict[str, Any]) -> Response:
        request_headers = dict(headers)
        if session_id:
            request_headers["MCP-Session-Id"] = session_id
        with httpx.Client(timeout=30) as client:
            return Response(client.post(url, json=payload, headers=request_headers))

    capabilities: Dict[str, Any] = {}
    if not args.no_apps:
        capabilities["extensions"] = {UI_EXTENSION_ID: {"mimeTypes": [APP_MIME_TYPE]}}

    init = rpc(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-11-25",
                "capabilities": capabilities,
                "clientInfo": {"name": "verify-mcp-app", "version": "1.0.0"},
            },
        }
    )
    show("initialize", init)
    session_id = init.headers.get("mcp-session-id")
    print(f"\nsession id: {session_id}")

    rpc({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})

    resources = rpc({"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}})
    show("resources/list", resources)

    tools = rpc({"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}})
    show("tools/list", tools)

    read = rpc(
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "resources/read",
            "params": {"uri": DASHBOARD_RESOURCE_URI},
        }
    )
    show(f"resources/read {DASHBOARD_RESOURCE_URI}", read)

    call = rpc(
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": DASHBOARD_TOOL_NAME,
                "arguments": {"entity_type": "Task", "project_id": 1},
            },
        }
    )
    show(f"tools/call {DASHBOARD_TOOL_NAME}", call)

    server.should_exit = True

    # ---- Assertions -------------------------------------------------------
    failures: List[str] = []
    check_tool_meta(tools, failures)
    check_resource(read, failures)
    check_coexistence(resources, failures)
    check_dashboard_call(call, failures, apps_advertised=not args.no_apps)

    print()
    print("===== checks =====")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print(f"PASS: tool advertises _meta.ui.resourceUri ({DASHBOARD_RESOURCE_URI})")
    print(f"PASS: {DASHBOARD_RESOURCE_URI} served as {APP_MIME_TYPE}")
    print("PASS: UI bundle is a single self-contained HTML document")
    print("PASS: ui:// resource coexists with the shotgrid://schema/* resources")
    print("PASS: tools/call returns structured data plus a plain-text summary")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
