"""Utility functions for the ShotGrid MCP server."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Set

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


# Configure logging
logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """Create a requests session with retry logic.

    Returns:
        Session configured with retry logic.
    """
    session = requests.Session()

    # Configure retry strategy
    retries = Retry(
        total=3,  # number of retries
        backoff_factor=0.5,  # wait 0.5s * (2 ** (retry - 1)) between retries
        status_forcelist=[500, 502, 503, 504],  # retry on these status codes
        allowed_methods=["GET", "HEAD"],  # only retry these methods
    )

    # Add retry adapter to session
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def download_file(url: str, local_path: str, chunk_size: int = 8192) -> None:
    """Download a file from a URL.

    Args:
        url: URL to download from.
        local_path: Path to save the file to.
        chunk_size: Size of chunks to download in bytes.

    Raises:
        requests.exceptions.RequestException: If download fails.
    """
    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)

        # Create session with retry logic
        session = create_session()

        # Stream download in chunks
        with session.get(url, stream=True) as response:
            response.raise_for_status()

            total_size = int(response.headers.get("content-length", 0))
            downloaded = 0

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)

                        # Log progress for large files
                        if total_size > chunk_size * 10:  # Only log for files > 80KB
                            progress = (downloaded / total_size) * 100
                            logger.debug("Download progress: %.1f%%", progress)

        logger.info("Successfully downloaded file to %s", local_path)

    except Exception as e:
        logger.error("Failed to download file from %s to %s: %s", url, local_path, str(e))
        raise


def handle_error(error: Exception, operation: str) -> Dict[str, Any]:
    """Handle errors in a consistent way.

    Args:
        error: The exception that occurred.
        operation: Name of the operation that failed.

    Returns:
        Dictionary containing error details.
    """
    logger.error("Error in %s: %s", operation, str(error))
    return {
        "error": f"Error executing {operation}: {str(error)}",
        "error_type": error.__class__.__name__,
        "timestamp": datetime.now().isoformat(),
    }


class DateTimeEncoder(json.JSONEncoder):
    """JSON encoder that handles datetime objects."""

    def default(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings.

        Args:
            obj: Object to encode.

        Returns:
            ISO format string if obj is datetime, otherwise default encoding.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def get_entity_types() -> set[str]:
    """Get all available entity types.

    Returns:
        Set of entity type names.
    """
    # Start with default entity types
    entity_types = set()

    # Add custom entity types from environment variable
    custom_types = os.getenv("ENTITY_TYPES", "")
    if custom_types:
        entity_types.update(t.strip() for t in custom_types.split(",") if t.strip())

    return entity_types


def chunk_data(data: Any, chunk_size: int = 1000) -> List[Any]:
    """Split large data into smaller chunks.

    Args:
        data: Data to be chunked (list, dict, or other data types).
        chunk_size: Maximum size of each chunk.

    Returns:
        List of data chunks.
    """
    if isinstance(data, list):
        return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]
    elif isinstance(data, dict):
        items = list(data.items())
        chunks = [dict(items[i:i + chunk_size]) for i in range(0, len(items), chunk_size)]
        return chunks
    else:
        return [data]


def truncate_long_strings(data: Any, max_length: int = 1000) -> Any:
    """Truncate long string values in data structures.

    Args:
        data: Data structure containing strings to truncate.
        max_length: Maximum length for string values.

    Returns:
        Data structure with truncated strings.
    """
    if isinstance(data, dict):
        return {k: truncate_long_strings(v, max_length) for k, v in data.items()}
    elif isinstance(data, list):
        return [truncate_long_strings(item, max_length) for item in data]
    elif isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + "..."

    return data


def filter_essential_fields(data: Dict[str, Any], essential_fields: Set[str]) -> Dict[str, Any]:
    """Filter data to keep only essential fields.

    Args:
        data: Dictionary containing data.
        essential_fields: Set of field names to keep.

    Returns:
        Filtered dictionary containing only essential fields.
    """
    if not isinstance(data, dict):
        return data
    return {k: filter_essential_fields(v, essential_fields) if isinstance(v, dict) else v 
            for k, v in data.items() if k in essential_fields}
