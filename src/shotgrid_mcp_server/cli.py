"""Command-line interface for ShotGrid MCP server.

Powered by dcc-mcp-core. Starts an HTTP server that auto-registers with
the dcc-gateway at 127.0.0.1:9765/mcp.

Usage::

    uvx shotgrid-mcp-server                # default (port 8765)
    uvx shotgrid-mcp-server --port 8000    # custom port
"""

# Import built-in modules
import logging
import os
import sys

# Import third-party modules
import click

# Import local modules
from shotgrid_mcp_server.shotgrid_adapter import create_shotgrid_server

logger = logging.getLogger(__name__)

# Default port — register with gateway at 127.0.0.1:9765
DEFAULT_PORT = int(os.getenv("SHOTGRID_MCP_PORT", "8765"))


@click.command(
    help="""
ShotGrid MCP Server — connect LLMs to ShotGrid via dcc-gateway.

Starts an HTTP server and registers with the local dcc-gateway at
http://127.0.0.1:9765/mcp. All ShotGrid tools are exposed as progressive
skills (search → load → call).

\b
Environment Variables:
  SHOTGRID_URL            ShotGrid server URL
  SHOTGRID_SCRIPT_NAME    ShotGrid script name
  SHOTGRID_SCRIPT_KEY     ShotGrid script key
  SHOTGRID_MCP_PORT       Override server port (default: 8765)
  DCC_MCP_SKILL_PATHS     Additional skill search paths
""",
)
@click.option(
    "--port",
    type=int,
    default=DEFAULT_PORT,
    show_default=True,
    help="HTTP server port",
)
def cli(port: int) -> None:
    """Start the ShotGrid MCP server."""
    try:
        click.echo(f"\n{'=' * 70}")
        click.echo("  ShotGrid MCP Server (dcc-mcp-core)")
        click.echo(f"  Gateway:  http://127.0.0.1:9765/mcp")
        click.echo(f"  Server:   http://127.0.0.1:{port}/mcp")
        click.echo(f"{'=' * 70}\n")
        click.echo("→ Starting server and registering with gateway...\n")

        server = create_shotgrid_server(port=port)

        with server as handle:
            click.echo(f"✓ Server listening at {handle.mcp_url()}")
            click.echo(f"✓ Gateway endpoint: http://127.0.0.1:9765/mcp")
            click.echo("\nPress Ctrl+C to stop...\n")

            # Keep running until interrupted
            try:
                import time
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass

        click.echo("\nServer stopped.")

    except ValueError as e:
        if "Missing required" in str(e):
            click.echo(f"\n{'=' * 60}", err=True)
            click.echo("  Configuration Error", err=True)
            click.echo(f"{'=' * 60}", err=True)
            click.echo(str(e), err=True)
            click.echo(f"{'=' * 60}\n", err=True)
            sys.exit(1)
        raise
    except Exception as e:
        logger.error("Failed to start: %s", e, exc_info=True)
        click.echo(f"\n❌ Error: {e}", err=True)
        raise click.Abort() from e


def main() -> None:
    """Entry point for the ShotGrid MCP server."""
    cli()


if __name__ == "__main__":
    main()
