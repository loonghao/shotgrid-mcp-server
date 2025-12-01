"""ShotGrid MCP server implementation.

This module provides the FastMCP server for ShotGrid integration.

For FastMCP Cloud deployment, this module exports a module-level `mcp` instance
that is lazily initialized on first access. The entrypoint should be:
    src/shotgrid_mcp_server/server.py:mcp

For local development, use the CLI:
    shotgrid-mcp-server --transport http --port 8000
"""

# Import built-in modules
import logging

# Import third-party modules
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext
from shotgrid_mcp_server.http_context import get_shotgrid_credentials_from_headers
from shotgrid_mcp_server.logger import setup_logging
from shotgrid_mcp_server.schema_cache import preload_schemas
from shotgrid_mcp_server.tools import register_all_tools

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()


def get_connection_context(connection=None) -> ShotGridConnectionContext:
    """Get a ShotGrid connection context with credentials from HTTP headers or environment.

    This function attempts to extract credentials from HTTP headers first (for HTTP transport),
    and falls back to environment variables if headers are not available (for stdio transport).

    Args:
        connection: Optional direct ShotGrid connection, used in testing.

    Returns:
        ShotGridConnectionContext: Connection context with appropriate credentials.
    """
    if connection is not None:
        # Use provided connection directly (for testing)
        return ShotGridConnectionContext(factory_or_connection=connection)

    # Try to get credentials from HTTP headers
    url, script_name, api_key = get_shotgrid_credentials_from_headers()

    # Create connection context with credentials from headers or environment variables
    return ShotGridConnectionContext(
        factory_or_connection=None,
        url=url,
        script_name=script_name,
        api_key=api_key,
    )


def create_server(
    connection=None,
    lazy_connection: bool = False,
    enable_caching: bool = True,
    preload_schema: bool = True,
) -> FastMCP:  # type: ignore[type-arg]
    """Create a FastMCP server instance.

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
            Tools will create connections on-demand. This is useful for HTTP mode
            where credentials come from request headers.
        enable_caching: If True, enable FastMCP response caching middleware.
        preload_schema: If True, preload common entity schemas on startup.

    Returns:
        FastMCP: The server instance.

    Raises:
        Exception: If server creation fails.
    """
    try:
        mcp: FastMCP = FastMCP(name="shotgrid-server")  # type: ignore[type-arg]
        logger.debug("Created FastMCP instance")

        # Add caching middleware if enabled
        if enable_caching:
            try:
                from fastmcp.middleware import CachingMiddleware

                mcp.add_middleware(
                    CachingMiddleware(
                        resource_ttl=86400,  # 24 hours for schema resources
                        tool_ttl=300,  # 5 minutes for tool responses
                        backend="filesystem",  # Use filesystem backend
                    )
                )
                logger.info("Enabled FastMCP response caching middleware")
            except ImportError:
                logger.warning(
                    "FastMCP CachingMiddleware not available. " "Upgrade to fastmcp>=2.13.0 for caching support."
                )

        if lazy_connection:
            # For HTTP mode: register tools without creating a connection
            # Tools will create connections on-demand using HTTP headers or env vars
            from unittest.mock import MagicMock

            # Create a mock ShotGrid object just for tool registration
            # The actual connection will be created when tools are called
            mock_sg = MagicMock()
            register_all_tools(mcp, mock_sg)
            logger.debug("Registered all tools (lazy connection mode)")
        else:
            # For stdio mode or testing: create actual connection during registration
            with get_connection_context(connection) as sg:
                register_all_tools(mcp, sg)
                logger.debug("Registered all tools")

                # Preload schemas if enabled
                if preload_schema:
                    try:
                        import asyncio

                        asyncio.run(preload_schemas(sg))
                        logger.info("Schema preloading completed")
                    except Exception as e:
                        logger.warning(f"Schema preloading failed: {e}")

        return mcp
    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


# Module-level MCP instance for FastMCP Cloud deployment
# FastMCP Cloud looks for 'mcp', 'server', or 'app' in the entrypoint file
# Using lazy_connection=True to avoid connection errors during import
# Credentials are provided via environment variables at runtime
mcp: FastMCP = create_server(lazy_connection=True, preload_schema=False)


def main() -> None:
    """Entry point for the ShotGrid MCP server.

    This function is kept for backward compatibility.
    The actual CLI implementation is in cli.py.
    """
    # Import here to avoid circular imports
    from shotgrid_mcp_server.cli import main as cli_main

    cli_main()


if __name__ == "__main__":
    main()
