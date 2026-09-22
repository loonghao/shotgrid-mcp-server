"""MCP Apps support for the ShotGrid MCP server.

MCP Apps bind a tool to an interactive UI: the tool advertises
``_meta.ui.resourceUri`` and the server serves the matching ``ui://``
resource as a single self-contained HTML document with the
``text/html;profile=mcp-app`` MIME type.

The UI bundle is built ahead of time from the Node sources in ``web/`` with
``vite-plugin-singlefile`` and committed under
``shotgrid_mcp_server/apps/dashboard/index.html``. Node is therefore a
development-time tool only: neither the runtime dependency graph nor the
packaged wheel needs it.
"""

from shotgrid_mcp_server.apps.dashboard import DASHBOARD_RESOURCE_URI, register_dashboard_app
from shotgrid_mcp_server.tools.types import FastMCPType

__all__ = ["DASHBOARD_RESOURCE_URI", "register_apps"]


def register_apps(server: FastMCPType, sg: object) -> None:
    """Register every MCP App tool and resource on the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection (may be a mock in lazy-connection mode).
    """
    register_dashboard_app(server, sg)
