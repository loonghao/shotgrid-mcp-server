"""ASGI application entry point for deployment.

This module provides a customizable ASGI application with middleware support.
It's designed for easy deployment to cloud platforms and ASGI servers.

Deployment Examples:
    1. Uvicorn (development):
        uvicorn app:app --host 0.0.0.0 --port 8000 --reload

    2. Uvicorn (production):
        uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4

    3. Gunicorn with Uvicorn workers:
        gunicorn app:app -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000 --workers 4

    4. Hypercorn:
        hypercorn app:app --bind 0.0.0.0:8000

Environment Variables:
    SHOTGRID_URL:         Your ShotGrid server URL
    SHOTGRID_SCRIPT_NAME: Your ShotGrid script name
    SHOTGRID_SCRIPT_KEY:  Your ShotGrid script key

HTTP Headers (for multi-site support):
    X-ShotGrid-URL:         ShotGrid server URL for this request
    X-ShotGrid-Script-Name: Script name for this request
    X-ShotGrid-Script-Key:  API key for this request
"""

# Import third-party modules
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Import local modules
from shotgrid_mcp_server.asgi import create_asgi_app

# Lazy initialization to avoid connection errors during module import
_app_instance = None


def get_app():
    """Get or create the ASGI application with middleware.

    This function implements lazy initialization to avoid creating
    ShotGrid connections during module import or Docker build time.

    Returns:
        Starlette application instance with configured middleware.
    """
    global _app_instance
    if _app_instance is None:
        # Configure CORS middleware
        # Customize these settings based on your deployment requirements
        cors_middleware = Middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, specify exact origins
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Create ASGI application with middleware
        _app_instance = create_asgi_app(
            middleware=[cors_middleware],
            path="/mcp",  # API endpoint path
        )

    return _app_instance


# ASGI application entry point
def app(scope, receive, send):
    """ASGI application entry point with lazy initialization.

    Args:
        scope: ASGI scope dict
        receive: ASGI receive callable
        send: ASGI send callable

    Returns:
        Coroutine for the ASGI application
    """
    application = get_app()
    return application(scope, receive, send)


# Note: For production deployments, consider:
# 1. Restricting CORS origins to specific domains
# 2. Adding authentication middleware
# 3. Adding rate limiting middleware
# 4. Adding request logging middleware
# 5. Using environment-specific configurations
