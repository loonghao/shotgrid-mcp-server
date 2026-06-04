"""ShotGrid Adapter — DccServerBase subclass for ShotGrid MCP server.

This module provides the :class:`ShotGridServer` adapter that bridges
ShotGrid (Flow Production Tracking) into the dcc-mcp-core ecosystem.
ShotGrid has no GUI host, so tools default to ``affinity: any`` and
the adapter uses the custom-studio-tool / external-bridge pattern.

Usage::

    from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer
    server = ShotGridServer()
    server.start()
"""

# Import built-in modules
import logging
import os
from pathlib import Path
from typing import Any, Optional

# Import third-party modules
from dcc_mcp_core import DccServerBase, DccServerOptions

# Import local modules
from shotgrid_mcp_server.connection_pool import (
    ShotGridConnectionContext,
    create_shotgun_connection,
    get_shotgun_credentials,
)

logger = logging.getLogger(__name__)


class ShotGridServer(DccServerBase):
    """ShotGrid MCP server adapter built on dcc-mcp-core.

    This adapter wraps the existing ShotGrid infrastructure (connection pool,
    schema cache, credential management) into a :class:`DccServerBase` subclass.
    ShotGrid capabilities are exposed as dcc-mcp skills, discovered and loaded
    on-demand by Agent/gateway.

    Key differences from DCC adapters (Maya/Blender):
        - No GUI host → no ``HostExecutionBridge`` main-thread dispatcher
        - Tool affinity defaults to ``any`` (no DCC main-thread requirement)
        - Credentials from env vars (:envvar:`SHOTGRID_URL`, etc.) or HTTP headers
        - Supports both stdio and HTTP transport modes
    """

    def __init__(
        self,
        skills_dir: Optional[str] = None,
        port: int = 8765,
        server_name: Optional[str] = None,
        server_version: Optional[str] = None,
    ) -> None:
        """Initialize the ShotGrid adapter.

        Args:
            skills_dir: Path to the skills directory. Defaults to ``skills/``
                relative to the project root.
            port: TCP port for the HTTP transport (default: 8765).
            server_name: Override the server name shown in gateway listings.
            server_version: Override the reported server version.
        """
        # Resolve skills directory
        if skills_dir is None:
            # Default: skills/ relative to the shotgrid_mcp_server package
            package_dir = Path(__file__).resolve().parent.parent.parent
            skills_dir = str(package_dir / "skills")

        self._skills_dir = skills_dir
        self._shotgrid_connection: Any = None  # Lazy-initialized ShotGrid connection

        # Build options using the recommended constructor
        # dcc_name = "shotgrid" — used for gateway discovery and log naming
        options = DccServerOptions.from_env(
            dcc_name="shotgrid",
            builtin_skills_dir=skills_dir,
            port=port,
            server_name=server_name or "shotgrid-mcp-server",
            server_version=server_version,
        )

        super().__init__(options)

        # Register ShotGrid schema resources on the MCP server
        self._register_shotgrid_resources()

        logger.info(
            "ShotGridServer initialized — skills_dir=%s, port=%d",
            skills_dir,
            port,
        )

    # ── ShotGrid connection management ────────────────────────────────────

    @property
    def shotgrid_connection(self) -> Any:
        """Lazy-initialized ShotGrid connection.

        Credentials are resolved from:
        1. HTTP headers (``X-ShotGrid-*``) — for HTTP transport
        2. Environment variables (``SHOTGRID_*``) — for stdio transport
        """
        if self._shotgrid_connection is None:
            try:
                url, script_name, api_key = get_shotgun_credentials(require_env_vars=False)
                self._shotgrid_connection = create_shotgun_connection(
                    url=url,
                    script_name=script_name,
                    api_key=api_key,
                )
                logger.info("ShotGrid connection established — URL: %s", url)
            except Exception:
                # Lazy mode: connection will be created per-request
                logger.debug("ShotGrid connection deferred (lazy mode)")
        return self._shotgrid_connection

    def get_connection_context(self, connection: Any = None) -> ShotGridConnectionContext:
        """Get a :class:`ShotGridConnectionContext` for the current request.

        Args:
            connection: Optional direct ShotGrid connection (for testing).

        Returns:
            A context manager that yields a ``shotgun_api3.Shotgun`` instance.
        """
        if connection is not None:
            return ShotGridConnectionContext(factory_or_connection=connection)

        # Try HTTP header credentials first, then env vars
        from shotgrid_mcp_server.http_context import get_shotgrid_credentials_from_headers

        url, script_name, api_key = get_shotgrid_credentials_from_headers()
        return ShotGridConnectionContext(
            factory_or_connection=None,
            url=url,
            script_name=script_name,
            api_key=api_key,
        )

    # ── MCP resources ─────────────────────────────────────────────────────

    def _register_shotgrid_resources(self) -> None:
        """Register ShotGrid-specific MCP resources.

        Resources include schema metadata (entity types, field schemas, status codes)
        that are available at well-known URIs like ``shotgrid://schema/entities``.
        """
        # Schema resources are registered lazily on first access
        # to avoid requiring a ShotGrid connection at import time.
        # The actual registration happens when tools/call requests schema data.
        pass

    # ── Lifecycle ─────────────────────────────────────────────────────────

    def start(self, transport: str = "stdio", **kwargs: Any) -> Any:
        """Start the ShotGrid MCP server.

        Args:
            transport: Transport mode — ``"stdio"`` (default) or ``"http"``.
                In HTTP mode, credentials can be provided via HTTP headers.
            **kwargs: Additional transport-specific arguments:
                - ``host``: Bind address for HTTP (default: ``"127.0.0.1"``)
                - ``port``: Override the port set during init
                - ``path``: API endpoint path (default: ``"/mcp"``)

        Returns:
            A server handle (implementation-specific).
        """
        host = kwargs.get("host", "127.0.0.1")
        path = kwargs.get("path", "/mcp")

        if transport == "http":
            port = kwargs.get("port", self._options.port)
            logger.info(
                "Starting ShotGrid MCP server (HTTP) on %s:%d%s",
                host,
                port,
                path,
            )
            # Use DccServerBase's HTTP serving
            return super().serve(host=host, port=port, path=path)
        else:
            logger.info("Starting ShotGrid MCP server (stdio)")
            return super().serve(transport="stdio")

    def stop(self) -> None:
        """Stop the ShotGrid MCP server and clean up resources."""
        logger.info("Stopping ShotGrid MCP server")
        self._shotgrid_connection = None


def create_shotgrid_server(
    skills_dir: Optional[str] = None,
    port: int = 8765,
    lazy_connection: bool = True,
) -> ShotGridServer:
    """Factory function to create a :class:`ShotGridServer` instance.

    This is the recommended entry point for programmatic usage.

    Args:
        skills_dir: Path to the skills directory.
        port: TCP port for HTTP transport.
        lazy_connection: If True (default), defer ShotGrid connection until
            a tool actually needs it. This is essential for HTTP mode where
            credentials come from request headers.

    Returns:
        A configured :class:`ShotGridServer` instance.

    Example::

        server = create_shotgrid_server(skills_dir="./skills")
        server.start(transport="http", host="0.0.0.0", port=8000)
    """
    import os

    if lazy_connection:
        os.environ.setdefault("DCC_MCP_SHOTGRID_LAZY", "1")

    return ShotGridServer(
        skills_dir=skills_dir,
        port=port,
    )
