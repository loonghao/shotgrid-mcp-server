"""HTTP context utilities for extracting ShotGrid credentials from HTTP headers.

Uses contextvars for thread-safe, async-safe header propagation without
depending on any MCP server framework (fastmcp or dcc-mcp-core).
"""

# Import built-in modules
import logging
from contextvars import ContextVar
from typing import Dict, Mapping, Optional, Tuple

logger = logging.getLogger(__name__)

# HTTP header names for ShotGrid credentials
SHOTGRID_URL_HEADER = "X-ShotGrid-URL"
SHOTGRID_SCRIPT_NAME_HEADER = "X-ShotGrid-Script-Name"
SHOTGRID_SCRIPT_KEY_HEADER = "X-ShotGrid-Script-Key"

# Context variable for storing request-level HTTP headers
# Set by middleware or request handler before tool execution
_http_headers_ctx: ContextVar[Optional[Dict[str, str]]] = ContextVar(
    "shotgrid_http_headers", default=None
)


def set_http_headers(headers: Optional[Mapping[str, str]]) -> None:
    """Store HTTP headers for the current request context.

    Call this from middleware or request handler before executing tools.

    Args:
        headers: HTTP headers dict from the incoming request.
    """
    if headers is not None:
        _http_headers_ctx.set(dict(headers))
    else:
        _http_headers_ctx.set(None)


def get_http_headers() -> Optional[Dict[str, str]]:
    """Get HTTP headers for the current request context.

    Returns:
        Headers dict or None if not in a request context.
    """
    return _http_headers_ctx.get()


def clear_http_headers() -> None:
    """Clear HTTP headers (e.g. after request completes)."""
    _http_headers_ctx.set(None)


def get_request_info() -> Dict[str, Optional[str]]:
    """Extract request information for debugging.

    Returns:
        Dict with user_agent, referer, request_id, forwarded_for.
    """
    headers = get_http_headers()
    if not headers:
        return {}

    info = {
        "user_agent": headers.get("user-agent"),
        "referer": headers.get("referer"),
        "request_id": headers.get("x-request-id"),
        "forwarded_for": headers.get("x-forwarded-for"),
    }
    return {k: v for k, v in info.items() if v is not None}


def get_shotgrid_credentials_from_headers() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract ShotGrid credentials from HTTP request headers.

    Uses contextvar-stored headers (set by middleware). Falls back to
    None values when not in an HTTP request context.

    Returns:
        (url, script_name, api_key) from headers, or (None, None, None).
    """
    headers = get_http_headers()

    if not headers:
        logger.debug("No HTTP headers in context - likely stdio/CLI transport")
        return None, None, None

    logger.debug("Available HTTP headers: %s", dict(headers))

    url = headers.get(SHOTGRID_URL_HEADER) or headers.get(SHOTGRID_URL_HEADER.lower())
    script_name = headers.get(SHOTGRID_SCRIPT_NAME_HEADER) or headers.get(SHOTGRID_SCRIPT_NAME_HEADER.lower())
    api_key = headers.get(SHOTGRID_SCRIPT_KEY_HEADER) or headers.get(SHOTGRID_SCRIPT_KEY_HEADER.lower())

    request_info = get_request_info()

    if url or script_name or api_key:
        debug_parts = [
            f"ShotGrid URL: {url}" if url else None,
            f"Script Name: {script_name}" if script_name else None,
            f"Client: {request_info.get('forwarded_for', 'unknown')}",
        ]
        debug_msg = " | ".join(filter(None, debug_parts))
        logger.info("HTTP Request — %s", debug_msg)
    elif request_info:
        logger.debug(
            "HTTP Request without ShotGrid credentials — Client: %s",
            request_info.get("forwarded_for", "unknown"),
        )

    return url, script_name, api_key
