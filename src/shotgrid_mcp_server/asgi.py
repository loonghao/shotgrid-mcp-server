"""ASGI compatibility shim for ShotGrid MCP server.

dcc-mcp-core 0.17 starts its own MCP HTTP server via ``DccServerBase.start()``
instead of exposing a FastMCP-style ``http_app()`` object. This module keeps
``shotgrid_mcp_server.asgi:app`` importable for platforms that probe it, while
returning a clear response that the dcc-mcp-core CLI/gateway entrypoint is the
supported runtime path.
"""

# Import built-in modules
import logging
from typing import List, Optional

# Import third-party modules
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

# Import local modules
from shotgrid_mcp_server.logger import setup_logging

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()

_HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]


async def _health(_request: Request) -> JSONResponse:
    """Return a small health payload for ASGI platform probes."""

    return JSONResponse(
        {
            "status": "ok",
            "runtime": "dcc-mcp-core",
            "message": "Use the shotgrid-mcp-server CLI to start the MCP HTTP server.",
        }
    )


async def _mcp_not_available(request: Request) -> JSONResponse:
    """Explain why this ASGI shim does not serve MCP traffic."""

    return JSONResponse(
        {
            "error": "asgi_mcp_not_available",
            "runtime": "dcc-mcp-core",
            "mcp_path": request.app.state.mcp_path,
            "message": (
                "dcc-mcp-core 0.17.54 serves MCP over its own HTTP server. "
                "Start this adapter with `shotgrid-mcp-server --port <port>` "
                "and connect through dcc-gateway."
            ),
        },
        status_code=503,
    )


def create_asgi_app(middleware: Optional[List[Middleware]] = None, path: str = "/mcp"):
    """Create a Starlette ASGI compatibility application.

    Args:
        middleware: Optional list of Starlette middleware to add to the app.
        path: MCP endpoint path reported by the compatibility response.

    Returns:
        Starlette application instance.
    """
    try:
        normalized_path = path if path.startswith("/") else f"/{path}"
        logger.info("Creating ASGI compatibility app for path: %s", normalized_path)

        asgi_app = Starlette(
            routes=[
                Route("/", _health, methods=["GET"]),
                Route(normalized_path, _mcp_not_available, methods=_HTTP_METHODS),
                Route(f"{normalized_path}/{{rest:path}}", _mcp_not_available, methods=_HTTP_METHODS),
            ],
            middleware=middleware or [],
        )
        asgi_app.state.mcp_path = normalized_path

        logger.info("ASGI compatibility app created successfully on path: %s", normalized_path)
        return asgi_app

    except Exception as err:
        logger.error("Failed to create ASGI application: %s", str(err), exc_info=True)
        raise


# Lazy initialization of default ASGI application
# The app is created on first access, not on module import
# This prevents connection errors during Docker build or import time
_app_instance = None


def get_app():
    """Get or create the default ASGI application instance.

    This function implements lazy initialization to avoid creating
    ShotGrid connections during module import or Docker build time.

    Returns:
        Starlette application instance.
    """
    global _app_instance
    if _app_instance is None:
        logger.info("Initializing default ASGI application (lazy mode)")
        try:
            _app_instance = create_asgi_app()
            logger.info("ASGI application initialized successfully")
            logger.info("Deploy with: uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000")
        except Exception as e:
            logger.error("Failed to initialize ASGI application: %s", str(e))
            # Re-raise to let the ASGI server handle the error
            raise
    return _app_instance


# For ASGI servers, we need a module-level callable.
# Import this as: uvicorn shotgrid_mcp_server.asgi:app
def app(scope, receive, send):
    """ASGI application entry point with lazy initialization.

    This is a module-level callable that ASGI servers can import.
    The actual application is created on first request.

    Args:
        scope: ASGI scope dict
        receive: ASGI receive callable
        send: ASGI send callable

    Returns:
        Coroutine for the ASGI application
    """
    application = get_app()
    return application(scope, receive, send)
