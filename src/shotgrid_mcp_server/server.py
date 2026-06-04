"""ShotGrid MCP server implementation.

This module provides the MCP server for ShotGrid integration, now built on
dcc-mcp-core. The existing ``create_server`` and module-level ``mcp``
instance are kept for backward compatibility.

For new deployments, prefer :func:`create_shotgrid_server` from
:mod:`shotgrid_mcp_server.shotgrid_adapter`.

For FastMCP Cloud / dcc-gateway deployment, the entrypoint should be::

    src/shotgrid_mcp_server/server.py:mcp

For local development, use the CLI::

    shotgrid-mcp-server --transport http --port 8000
"""

# Import built-in modules
import logging
from typing import Any

# Import local modules
from shotgrid_mcp_server.logger import setup_logging
from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer, create_shotgrid_server

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()


def create_server(
    connection: Any = None,
    lazy_connection: bool = False,
    enable_caching: bool = True,
    preload_schema: bool = True,
) -> "FastMCP":
    """Create a FastMCP-compatible server instance.

    **Deprecated**: This function returns a dcc-mcp-core based server.
    For new code, use :func:`create_shotgrid_server` directly.

    For HTTP transport, credentials can be provided via HTTP headers:
    - X-ShotGrid-URL: ShotGrid server URL
    - X-ShotGrid-Script-Name: Script name
    - X-ShotGrid-Script-Key: API key

    For stdio transport, credentials are read from environment variables:
    - SHOTGRID_URL
    - SHOTGRID_SCRIPT_NAME
    - SHOTGRID_SCRIPT_KEY

    Args:
        connection: Optional direct ShotGrid connection, used in testing.
        lazy_connection: If True, skip connection test during server creation.
        enable_caching: If True, enable response caching (handled by core).
        preload_schema: If True, preload common entity schemas on startup.

    Returns:
        FastMCP: The server instance (dcc-mcp-core compatible).

    Raises:
        Exception: If server creation fails.
    """
    try:
        server = create_shotgrid_server(port=8000)

        if preload_schema and not lazy_connection:
            try:
                with server.get_connection_context(connection) as sg:
                    import asyncio
                    from shotgrid_mcp_server.schema_cache import preload_schemas

                    asyncio.run(preload_schemas(sg))
                    logger.info("Schema preloading completed")
            except Exception as e:
                logger.warning("Schema preloading failed: %s", e)

        # Return the underlying MCP server for FastMCP compatibility
        return server._server
    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


# Module-level MCP instance for FastMCP Cloud / dcc-gateway deployment
# The entrypoint should be: src/shotgrid_mcp_server/server.py:mcp
_server_instance: ShotGridServer | None = None


def _get_mcp() -> Any:
    """Get or create the module-level MCP server instance."""
    global _server_instance
    if _server_instance is None:
        _server_instance = create_shotgrid_server(port=8000)
    return _server_instance._server


# Lazy-initialized module-level mcp for deployment entrypoints
mcp: Any = None  # Will be set on first access


def __getattr__(name: str) -> Any:
    """Lazy initialization of module-level ``mcp`` instance.

    This avoids creating ShotGrid connections during import time,
    which is critical for Docker builds and FastMCP Cloud deployment.
    """
    if name == "mcp":
        return _get_mcp()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def main() -> None:
    """Entry point for the ShotGrid MCP server.

    This function is kept for backward compatibility.
    The actual CLI implementation is in cli.py.
    """
    from shotgrid_mcp_server.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
