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


@click.group(
    help="""
ShotGrid MCP Server - Connect LLMs to ShotGrid.

This server provides Model Context Protocol (MCP) access to ShotGrid,
allowing LLMs like Claude to interact with your production tracking data.

\b
Environment Variables:
  SHOTGRID_URL:         Your ShotGrid server URL
  SHOTGRID_SCRIPT_NAME: Your ShotGrid script name
  SHOTGRID_SCRIPT_KEY:  Your ShotGrid script key
    """,
    invoke_without_command=True,
)
@click.pass_context
def cli(ctx: click.Context) -> None:
    """ShotGrid MCP Server CLI."""
    # If no subcommand is provided, default to stdio
    if ctx.invoked_subcommand is None:
        ctx.invoke(stdio)


@cli.command()
def stdio() -> None:
    """Run server with stdio transport (for local MCP clients like Claude Desktop).

    \b
    Example:
      shotgrid-mcp-server stdio
      shotgrid-mcp-server  # stdio is the default
    """
    try:
        logger.info("Starting ShotGrid MCP server with stdio transport")

        # For stdio, create connection immediately to validate credentials
        app = create_server(lazy_connection=False)
        app.run(transport="stdio")

    except ValueError as e:
        # Handle missing environment variables error
        if "Missing required environment variables for ShotGrid connection" in str(e):
            click.echo(f"\n{'=' * 80}", err=True)
            click.echo("ERROR: ShotGrid MCP Server Configuration Issue", err=True)
            click.echo(f"{'=' * 80}", err=True)
            click.echo(str(e), err=True)
            click.echo(f"{'=' * 80}\n", err=True)
            sys.exit(1)
        raise
    except KeyboardInterrupt:
        click.echo("\n\nShutting down server...")
    except Exception as e:
        logger.error("Failed to start server: %s", str(e), exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort() from e


@cli.command()
@click.option(
    "--host",
    type=str,
    default="127.0.0.1",
    show_default=True,
    help="Host to bind to",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    show_default=True,
    help="Port to bind to",
)
@click.option(
    "--path",
    type=str,
    default="/mcp",
    show_default=True,
    help="API endpoint path",
)
def http(host: str, port: int, path: str) -> None:
    """Run server with HTTP transport (for remote deployments).

    In HTTP mode, credentials can be provided via:
    - HTTP headers: X-ShotGrid-URL, X-ShotGrid-Script-Name, X-ShotGrid-Script-Key
    - Environment variables: SHOTGRID_URL, SHOTGRID_SCRIPT_NAME, SHOTGRID_SCRIPT_KEY

    \b
    Examples:
      shotgrid-mcp-server http
      shotgrid-mcp-server http --host 0.0.0.0 --port 8080
      shotgrid-mcp-server http --host 0.0.0.0 --port 8000 --path /api/mcp
    """
    try:
        click.echo("\n💡 HTTP mode: ShotGrid connection will be created on-demand")
        click.echo("   You can provide credentials via HTTP headers or environment variables\n")

        # For HTTP, use lazy connection mode (credentials from headers)
        app = create_server(lazy_connection=True)

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

    except KeyboardInterrupt:
        click.echo("\n\nShutting down server...")
    except Exception as e:
        logger.error("Failed to start server: %s", str(e), exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort() from e


def main() -> None:
    """Entry point for the ShotGrid MCP server."""
    cli()


if __name__ == "__main__":
    main()
