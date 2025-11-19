"""HTTP context utilities for extracting ShotGrid credentials from HTTP headers."""

import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# HTTP header names for ShotGrid credentials
SHOTGRID_URL_HEADER = "X-ShotGrid-URL"
SHOTGRID_SCRIPT_NAME_HEADER = "X-ShotGrid-Script-Name"
SHOTGRID_SCRIPT_KEY_HEADER = "X-ShotGrid-Script-Key"


def get_request_info() -> Dict[str, Optional[str]]:
    """Extract request information for debugging purposes.

    Returns:
        Dict with request information including:
        - client_host: Client IP address
        - user_agent: User-Agent header
        - referer: Referer header
        - request_id: X-Request-ID header if present
    """
    try:
        from fastmcp.server.dependencies import get_http_headers

        headers = get_http_headers()
        if headers is None:
            return {}

        # Extract common debugging headers
        info = {
            "user_agent": headers.get("user-agent"),
            "referer": headers.get("referer"),
            "request_id": headers.get("x-request-id"),
            "forwarded_for": headers.get("x-forwarded-for"),
        }

        # Remove None values
        return {k: v for k, v in info.items() if v is not None}

    except Exception:
        return {}


def get_shotgrid_credentials_from_headers() -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Extract ShotGrid credentials from HTTP request headers.

    This function attempts to get credentials from HTTP headers when using HTTP transport.
    If HTTP headers are not available (e.g., when using stdio transport), returns None values.

    Returns:
        Tuple[Optional[str], Optional[str], Optional[str]]: URL, script name, and API key from headers.
            Returns (None, None, None) if not in HTTP context or headers are missing.
    """
    try:
        # Import here to avoid circular dependencies and to handle cases where fastmcp is not available
        from fastmcp.server.dependencies import get_http_headers

        # Get HTTP headers
        headers = get_http_headers()

        if headers is None:
            # Not in HTTP context (e.g., stdio transport)
            logger.debug("No HTTP headers available - likely using stdio transport")
            return None, None, None

        # DEBUG: Log all available headers to understand what's being passed
        logger.debug("Available HTTP headers: %s", dict(headers))

        # Extract credentials from headers (case-insensitive)
        url = headers.get(SHOTGRID_URL_HEADER) or headers.get(SHOTGRID_URL_HEADER.lower())
        script_name = headers.get(SHOTGRID_SCRIPT_NAME_HEADER) or headers.get(SHOTGRID_SCRIPT_NAME_HEADER.lower())
        api_key = headers.get(SHOTGRID_SCRIPT_KEY_HEADER) or headers.get(SHOTGRID_SCRIPT_KEY_HEADER.lower())

        # Get request info for debugging
        request_info = get_request_info()

        if url or script_name or api_key:
            # Build debug message with request source information
            debug_parts = [
                f"ShotGrid URL: {url}" if url else None,
                f"Script Name: {script_name}" if script_name else None,
                f"Client: {request_info.get('forwarded_for', 'unknown')}"
                if request_info.get("forwarded_for")
                else None,
                f"User-Agent: {request_info.get('user_agent', 'unknown')}" if request_info.get("user_agent") else None,
            ]
            debug_msg = " | ".join(filter(None, debug_parts))

            logger.info(
                "HTTP Request - %s",
                debug_msg,
            )
        else:
            # No credentials in headers, log request info anyway
            if request_info:
                logger.debug(
                    "HTTP Request without ShotGrid credentials - Client: %s, User-Agent: %s",
                    request_info.get("forwarded_for", "unknown"),
                    request_info.get("user_agent", "unknown"),
                )

        return url, script_name, api_key

    except ImportError:
        # fastmcp.server.dependencies not available
        logger.debug("fastmcp.server.dependencies not available - cannot extract HTTP headers")
        return None, None, None
    except Exception as e:
        # Any other error (e.g., not in request context)
        logger.debug("Failed to extract credentials from HTTP headers: %s", str(e))
        return None, None, None
