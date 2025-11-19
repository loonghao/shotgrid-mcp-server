"""ShotGrid MCP server implementation."""

# Import built-in modules
import logging

# Import third-party modules
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext
from shotgrid_mcp_server.http_context import get_shotgrid_credentials_from_headers
from shotgrid_mcp_server.logger import setup_logging
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


def create_server(connection=None, lazy_connection: bool = False) -> FastMCP:  # type: ignore[type-arg]
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

    Returns:
        FastMCP: The server instance.

    Raises:
        Exception: If server creation fails.
    """
    try:
        mcp: FastMCP = FastMCP(name="shotgrid-server")  # type: ignore[type-arg]
        logger.debug("Created FastMCP instance")

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

        return mcp
    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


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
else:
    # When imported, create a server for testing
    try:
        app = create_server()
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        # Don't raise here, as this is not the main entry point
