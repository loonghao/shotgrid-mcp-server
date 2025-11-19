"""Example: Custom ASGI application with advanced middleware.

This example demonstrates how to create a production-ready ASGI application
with multiple middleware layers for security, performance, and monitoring.

Deploy with:
    uvicorn examples.custom_app:app --host 0.0.0.0 --port 8000 --workers 4
"""

# Import built-in modules
import logging
import time
from typing import Callable

# Import third-party modules
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.gzip import GZipMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Import local modules
from shotgrid_mcp_server.asgi import create_asgi_app

# Configure logger
logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware
        """
        start_time = time.time()

        # Log request
        logger.info(
            "Request: %s %s from %s",
            request.method,
            request.url.path,
            request.client.host if request.client else "unknown",
        )

        # Process request
        response = await call_next(request)

        # Calculate processing time
        process_time = time.time() - start_time

        # Add custom headers
        response.headers["X-Process-Time"] = str(process_time)

        # Log response
        logger.info(
            "Response: %s %s - Status: %d - Time: %.3fs",
            request.method,
            request.url.path,
            response.status_code,
            process_time,
        )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware (example only, use proper rate limiter in production)."""

    def __init__(self, app, max_requests: int = 100):
        """Initialize rate limiter.

        Args:
            app: ASGI application
            max_requests: Maximum requests per client (simplified example)
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.requests = {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limits and process request.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware in chain

        Returns:
            Response from next middleware or rate limit error
        """
        client_ip = request.client.host if request.client else "unknown"

        # Simple counter (in production, use Redis or similar)
        if client_ip not in self.requests:
            self.requests[client_ip] = 0

        self.requests[client_ip] += 1

        if self.requests[client_ip] > self.max_requests:
            logger.warning("Rate limit exceeded for %s", client_ip)
            # In production, return proper rate limit response
            # For now, just log and continue

        response = await call_next(request)
        return response


# Configure middleware stack
middleware = [
    # CORS middleware - configure for your domain
    Middleware(
        CORSMiddleware,
        allow_origins=[
            "https://yourdomain.com",
            "https://app.yourdomain.com",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
        expose_headers=["X-Process-Time"],
    ),
    # GZip compression for responses
    Middleware(GZipMiddleware, minimum_size=1000),
    # Request logging
    Middleware(RequestLoggingMiddleware),
    # Rate limiting (example only)
    Middleware(RateLimitMiddleware, max_requests=1000),
]

# Create ASGI application with middleware
app = create_asgi_app(
    middleware=middleware,
    path="/mcp",
)

# Log startup
logger.info("Custom ShotGrid MCP ASGI application initialized")
logger.info("Middleware stack: CORS, GZip, Logging, RateLimit")
