"""Command-line interface for ShotGrid MCP server."""

# Import built-in modules
import logging
import sys

# Import third-party modules
import click

# Import local modules
from shotgrid_mcp_server.server import create_server

# Configure logger
logger = logging.getLogger(__name__)


@click.command(
    help="ShotGrid MCP Server - Model Context Protocol server for ShotGrid",
    epilog="""
\b
Transport Modes:
  stdio (default): Standard input/output transport for local MCP clients
  http:            Streamable HTTP transport for web-based deployments

\b
Examples:
  # Run with stdio transport (default)
  shotgrid-mcp-server

  # Run with HTTP transport
  shotgrid-mcp-server --transport http --host 0.0.0.0 --port 8000

  # Run with HTTP transport on custom path
  shotgrid-mcp-server --transport http --port 8080 --path /mcp

\b
Environment Variables:
  SHOTGRID_URL:         Your ShotGrid server URL
  SHOTGRID_SCRIPT_NAME: Your ShotGrid script name
  SHOTGRID_SCRIPT_KEY:  Your ShotGrid script key
    """,
)
@click.option(
    "--transport",
    type=click.Choice(["stdio", "http"], case_sensitive=False),
    default="stdio",
    show_default=True,
    help="Transport protocol to use",
)
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    show_default=True,
    help="Host to bind to for HTTP transport",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    show_default=True,
    help="Port to bind to for HTTP transport",
)
@click.option(
    "--path",
    type=str,
    default="/mcp",
    show_default=True,
    help="Path for HTTP transport endpoint",
)
def main(transport: str, host: str, port: int, path: str) -> None:
    """Entry point for the ShotGrid MCP server."""
    try:
        app = create_server()

        # Run server with specified transport
        if transport == "stdio":
            logger.info("Starting ShotGrid MCP server with stdio transport")
            app.run(transport="stdio")
        elif transport == "http":
            logger.info(
                "Starting ShotGrid MCP server with HTTP transport on %s:%d%s",
                host,
                port,
                path,
            )
            click.echo(f"\n{'=' * 80}")
            click.echo("ShotGrid MCP Server - HTTP Transport")
            click.echo(f"{'=' * 80}")
            click.echo(f"Server URL: http://{host}:{port}{path}")
            click.echo(f"{'=' * 80}\n")
            app.run(transport="http", host=host, port=port, path=path)

    except ValueError as e:
        # Handle missing environment variables error
        if "Missing required environment variables for ShotGrid connection" in str(e):
            # Print the error message in a more user-friendly way
            click.echo(f"\n{'=' * 80}", err=True)
            click.echo("ERROR: ShotGrid MCP Server Configuration Issue", err=True)
            click.echo(f"{'=' * 80}", err=True)
            click.echo(str(e), err=True)
            click.echo(f"{'=' * 80}\n", err=True)
            # Exit with error code
            sys.exit(1)
        else:
            # Re-raise other ValueError exceptions
            raise


if __name__ == "__main__":
    main()

