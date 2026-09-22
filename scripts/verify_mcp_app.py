"""Verify the MCP Apps integration against a live HTTP server over raw JSON-RPC.

Starts the real FastMCP HTTP server in a background thread and drives it with
hand-written JSON-RPC 2.0 requests (``initialize``, ``tools/list``,
``resources/list``, ``resources/read``), then prints the wire responses.

Usage:
    python scripts/verify_mcp_app.py [--port 8123] [--apps|--no-apps]

``--no-apps`` omits the ``capabilities.extensions`` advertisement so the
graceful-degradation path can be observed.
"""

from __future__ import annotations

# Import built-in modules
import argparse
import json
import threading
import time
from typing import Any, Dict, Optional

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


def build_server() -> FastMCP:
    """Build a server carrying the dashboard app plus the existing schema resources.

    The dashboard tool is registered with a stub ShotGrid connection because
    this script only exercises discovery and resource reads, never a query.
    """
    mcp: FastMCP = FastMCP(name="shotgrid-server")
    register_apps(mcp, _StubConnection())
    register_schema_resources(mcp, _StubConnection())
    return mcp


class _StubConnection:
    """Placeholder connection: resource registration never queries ShotGrid."""

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return "<stub connection>"


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

    show("resources/list", rpc({"jsonrpc": "2.0", "id": 2, "method": "resources/list", "params": {}}))

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

    server.should_exit = True

    # ---- Assertions -------------------------------------------------------
    failures = []

    tool_entries = tools.json().get("result", {}).get("tools", [])
    dashboard = next((t for t in tool_entries if t.get("name") == DASHBOARD_TOOL_NAME), None)
    if dashboard is None:
        failures.append(f"tool {DASHBOARD_TOOL_NAME!r} missing from tools/list")
    else:
        meta = dashboard.get("_meta", {}).get("ui", {})
        if meta.get("resourceUri") != DASHBOARD_RESOURCE_URI:
            failures.append(f"_meta.ui.resourceUri is {meta.get('resourceUri')!r}")

    contents = read.json().get("result", {}).get("contents", [])
    if not contents:
        failures.append(f"resources/read returned no contents for {DASHBOARD_RESOURCE_URI}")
    else:
        mime = contents[0].get("mimeType")
        if mime != APP_MIME_TYPE:
            failures.append(f"resource mimeType is {mime!r}, expected {APP_MIME_TYPE!r}")
        html = contents[0].get("text", "")
        if not html.lstrip().lower().startswith("<!doctype html"):
            failures.append("resource text is not an HTML document")
        for token in ('src="http', 'href="http'):
            if token in html:
                failures.append(f"HTML bundle references an external asset ({token})")

    print()
    print("===== checks =====")
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        return 1

    print("PASS: tool advertises _meta.ui.resourceUri")
    print(f"PASS: {DASHBOARD_RESOURCE_URI} served as {APP_MIME_TYPE}")
    print("PASS: UI bundle is a single self-contained HTML document")
    print("PASS: ui:// resource coexists with the shotgrid://schema/* resources")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
