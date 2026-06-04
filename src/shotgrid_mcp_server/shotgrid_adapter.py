"""ShotGrid Adapter — DccServerBase subclass for ShotGrid MCP server.

ShotGrid is an **external bridge** host (no GUI, no main-thread dispatch).
Tools default to ``affinity: any``. The adapter registers with dcc-gateway
and auto-discovers skills from the bundled ``skills/`` directory.

Usage::

    from shotgrid_mcp_server.shotgrid_adapter import ShotGridServer

    server = ShotGridServer()
    server.start()  # starts HTTP + registers with gateway at 127.0.0.1:9765

    # or as context manager:
    with ShotGridServer() as handle:
        print(f"Listening at {handle.mcp_url()}")
"""

# Import built-in modules
import logging
from pathlib import Path
from typing import Any, Optional

# Import third-party modules
from dcc_mcp_core import DccServerBase, DccServerOptions

logger = logging.getLogger(__name__)

# Package-relative path to skills directory
_SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "skills"


class ShotGridServer(DccServerBase):
    """ShotGrid MCP server adapter built on dcc-mcp-core.

    Classified as **external bridge** host:
    - No GUI → no ``HostExecutionBridge`` required
    - All tools ``affinity: any``
    - Credentials from env vars or HTTP headers (``SHOTGRID_*``)

    ShotGrid capabilities are exposed as progressive skills discovered
    and loaded on-demand via dcc-gateway (search → load → call).
    """

    def __init__(
        self,
        port: int = 8765,
        server_version: Optional[str] = None,
    ) -> None:
        if not _SKILLS_DIR.is_dir():
            logger.warning(
                "Skills directory not found: %s. No ShotGrid tools available.",
                _SKILLS_DIR,
            )

        options = DccServerOptions.from_env(
            dcc_name="shotgrid",
            builtin_skills_dir=str(_SKILLS_DIR),
            port=port,
            server_name="shotgrid-mcp-server",
            server_version=server_version,
            enable_gateway_failover=True,
        )

        super().__init__(options=options)
        logger.info(
            "ShotGridServer ready — skills=%s, port=%d",
            _SKILLS_DIR,
            port,
        )

    def _version_string(self) -> str:
        """Return the ShotGrid server version string."""
        from shotgrid_mcp_server import __version__

        return __version__


def create_shotgrid_server(port: int = 8765) -> ShotGridServer:
    """Factory function for :class:`ShotGridServer`.

    Args:
        port: TCP port for the HTTP server.

    Returns:
        A configured :class:`ShotGridServer` instance.
    """
    return ShotGridServer(port=port)
