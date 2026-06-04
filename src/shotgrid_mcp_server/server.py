"""ShotGrid MCP server — backward-compatible entrypoints.

For new code, use :func:`create_shotgrid_server` from
:mod:`shotgrid_mcp_server.shotgrid_adapter` directly.
"""

# Import built-in modules
import logging
from typing import Any

# Import local modules
from shotgrid_mcp_server.logger import setup_logging
from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

logger = logging.getLogger(__name__)
setup_logging()


def create_server(
    connection: Any = None,
    lazy_connection: bool = False,
    enable_caching: bool = True,
    preload_schema: bool = True,
) -> Any:
    """Create a ShotGrid MCP server (dcc-mcp-core based).

    Args:
        connection: Optional direct ShotGrid connection (for testing).
        lazy_connection: If True, defer ShotGrid connection.
        enable_caching: Unused — caching is handled by core.
        preload_schema: If True, preload schemas on startup.

    Returns:
        The inner MCP HTTP server for backward compat.
    """
    server = create_shotgrid_server(port=8000)

    if preload_schema and not lazy_connection:
        try:
            from shotgrid_mcp_server.connection_pool import (
                ShotGridConnectionContext,
            )

            with ShotGridConnectionContext(factory_or_connection=connection) as sg:
                import asyncio

                from shotgrid_mcp_server.schema_cache import preload_schemas

                asyncio.run(preload_schemas(sg))
                logger.info("Schema preloading completed")
        except Exception as e:
            logger.warning("Schema preloading failed: %s", e)

    # Return the server (DccServerBase subclass instance)
    return server


def main() -> None:
    """Entry point for the ShotGrid MCP server."""
    from shotgrid_mcp_server.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
