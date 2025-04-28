"""ShotGrid MCP server implementation."""

# Import built-in modules
import logging

# Import third-party modules
from fastmcp import FastMCP

# Import local modules
from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext
from shotgrid_mcp_server.logger import setup_logging
from shotgrid_mcp_server.tools import register_all_tools

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()


def create_server(connection=None) -> FastMCP:  # type: ignore[type-arg]
    """Create a FastMCP server instance.

    Args:
        connection: Optional direct ShotGrid connection, used in testing.

    Returns:
        FastMCP: The server instance.

    Raises:
        Exception: If server creation fails.
    """
    try:
        mcp: FastMCP = FastMCP(name="shotgrid-server")  # type: ignore[type-arg]
        logger.debug("Created FastMCP instance")

        # Register tools using connection context
        with ShotGridConnectionContext(factory_or_connection=connection) as sg:
            register_all_tools(mcp, sg)
            logger.debug("Registered all tools")
            return mcp
    except Exception as err:
        logger.error("Failed to create server: %s", str(err), exc_info=True)
        raise


def main() -> None:
    """Entry point for the ShotGrid MCP server."""
    try:
        app = create_server()
        app.run()
    except ValueError as e:
        # Handle missing environment variables error
        if "Missing required environment variables for ShotGrid connection" in str(e):
            # Print the error message in a more user-friendly way
            print("\n" + "=" * 80)
            print("ERROR: ShotGrid MCP Server Configuration Issue")
            print("=" * 80)
            print(str(e))
            print("=" * 80 + "\n")
            # Exit with error code
            import sys

            sys.exit(1)
        else:
            # Re-raise other ValueError exceptions
            raise


if __name__ == "__main__":
    main()
else:
    # When imported, create a server for testing
    try:
        app = create_server()
    except Exception as e:
        logger.error(f"Failed to initialize server: {e}")
        # Don't raise here, as this is not the main entry point
