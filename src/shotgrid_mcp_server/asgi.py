"""ASGI application for ShotGrid MCP server.

This module provides a standalone ASGI application that can be deployed
to any ASGI server (Uvicorn, Gunicorn, Hypercorn, etc.) or cloud platforms
like FastMCP Cloud.

Example:
    Deploy with Uvicorn:
        uvicorn shotgrid_mcp_server.asgi:app --host 0.0.0.0 --port 8000

    Deploy with Gunicorn:
        gunicorn shotgrid_mcp_server.asgi:app -k uvicorn.workers.UvicornWorker

    With custom middleware:
        from shotgrid_mcp_server.asgi import create_asgi_app
        from starlette.middleware import Middleware
        from starlette.middleware.cors import CORSMiddleware

        app = create_asgi_app(middleware=[
            Middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_methods=["*"],
                allow_headers=["*"],
            )
        ])
"""

# Import built-in modules
import logging
from typing import List, Optional

# Import third-party modules
from starlette.middleware import Middleware

# Import local modules
from shotgrid_mcp_server.logger import setup_logging
from shotgrid_mcp_server.server import create_server

# Configure logger
logger = logging.getLogger(__name__)
setup_logging()


def create_asgi_app(middleware: Optional[List[Middleware]] = None, path: str = "/mcp"):
    """Create a standalone ASGI application.

    Args:
        middleware: Optional list of Starlette middleware to add to the app.
        path: API endpoint path (default: "/mcp").

    Returns:
        Starlette application instance that can be deployed to any ASGI server.

    Example:
        Basic usage:
            app = create_asgi_app()

        With CORS middleware:
            from starlette.middleware import Middleware
            from starlette.middleware.cors import CORSMiddleware

            app = create_asgi_app(middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_methods=["*"],
                    allow_headers=["*"],
                )
            ])

        With multiple middleware:
            from starlette.middleware.gzip import GZipMiddleware

            app = create_asgi_app(middleware=[
                Middleware(CORSMiddleware, allow_origins=["*"]),
                Middleware(GZipMiddleware, minimum_size=1000),
            ])
    """
    try:
        logger.info("Creating ASGI application with lazy connection mode")

        # Create MCP server with lazy connection mode
        # Credentials will be provided via HTTP headers or environment variables
        mcp_server = create_server(lazy_connection=True)

        # Generate ASGI app from MCP server
        asgi_app = mcp_server.http_app(middleware=middleware, path=path)

        logger.info("ASGI application created successfully on path: %s", path)
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


# For ASGI servers, we need a module-level callable
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
