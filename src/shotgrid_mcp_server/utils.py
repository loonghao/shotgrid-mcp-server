"""Utility functions for ShotGrid MCP server."""

# Import built-in modules
import json
import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Set, TypeVar, Union

# Import third-party modules
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import local modules
from shotgrid_mcp_server.constants import ENTITY_TYPES_ENV_VAR, ENV_CUSTOM_ENTITY_TYPES
from shotgrid_mcp_server.types import EntityType

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")

# Default entity types to support - using all entity types from EntityType
DEFAULT_ENTITY_TYPES: Set[str] = set(EntityType.__args__)  # type: ignore


def create_session() -> requests.Session:
    """Create a requests session with retry logic.

    Returns:
        requests.Session: Configured session with retry logic.
    """
    session = requests.Session()

    # Configure retry strategy
    retries = Retry(
        total=3,
        backoff_factor=0.3,
        status_forcelist=[500, 502, 503, 504],
    )

    # Mount retry adapter
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


class ShotGridJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles ShotGrid special data types.

    This encoder handles datetime objects, Pydantic models, and other ShotGrid-specific data types
    to ensure proper serialization in JSON responses.
    """

    def default(self, obj: Any) -> Any:
        """Convert special data types to JSON-serializable formats.

        Args:
            obj: Object to encode.

        Returns:
            JSON-serializable representation of the object.
        """
        if isinstance(obj, datetime):
            # Format datetime with timezone info if available
            if obj.tzinfo is not None:
                return obj.isoformat()
            # Add Z suffix for UTC time without timezone
            return f"{obj.isoformat()}Z"
        elif isinstance(obj, date):
            # Format date as YYYY-MM-DD
            return obj.isoformat()
        # Handle Pydantic models
        elif hasattr(obj, "model_dump") and callable(obj.model_dump):
            return obj.model_dump()
        # Handle older Pydantic models or other objects with to_dict method
        elif hasattr(obj, "to_dict") and callable(obj.to_dict):
            return obj.to_dict()
        elif isinstance(obj, set):
            return list(obj)
        elif isinstance(obj, bytes):
            try:
                return obj.decode("utf-8")
            except UnicodeDecodeError:
                return str(obj)
        # Handle timedelta objects
        elif hasattr(obj, "total_seconds") and callable(obj.total_seconds):
            # Convert timedelta to seconds
            return obj.total_seconds()
        return super().default(obj)


def get_entity_types() -> Set[str]:
    """Get the set of entity types to support.

    Returns:
        Set[str]: Set of entity type names.
    """
    # Try both environment variables
    for env_var in [ENV_CUSTOM_ENTITY_TYPES, ENTITY_TYPES_ENV_VAR]:
        env_types = os.getenv(env_var)
        if env_types:
            try:
                types = {t.strip() for t in env_types.split(",")}
                logger.info("Using entity types from environment variable %s: %s", env_var, types)
                return types
            except Exception as e:
                logger.error("Failed to parse %s: %s", env_var, str(e))

    # Return default types
    logger.info("Using default entity types: %s", DEFAULT_ENTITY_TYPES)
    return DEFAULT_ENTITY_TYPES


def chunk_data(data: Union[List[Dict[str, Any]], Dict[str, Any]], chunk_size: int = 50) -> List[List[Dict[str, Any]]]:
    """Split data into chunks.

    Args:
        data: Data to split.
        chunk_size: Size of each chunk.

    Returns:
        List[List[Dict[str, Any]]]: List of data chunks.

    Raises:
        ValueError: If data is not a list or dict.
    """
    if isinstance(data, dict):
        data = [data]
    elif not isinstance(data, list):
        raise ValueError("Data must be a list or dict")

    return [data[i : i + chunk_size] for i in range(0, len(data), chunk_size)]


def truncate_long_strings(data: T, max_length: int = 1000) -> T:
    """Truncate long string values in data structure.

    Args:
        data: Data structure to process.
        max_length: Maximum length for string values.

    Returns:
        T: Processed data structure.
    """
    if isinstance(data, str):
        return data[:max_length] if len(data) > max_length else data  # type: ignore
    elif isinstance(data, dict):
        return {k: truncate_long_strings(v, max_length) for k, v in data.items()}  # type: ignore
    elif isinstance(data, (list, tuple)):
        return type(data)(truncate_long_strings(x, max_length) for x in data)  # type: ignore
    return data


def filter_essential_fields(data: Dict[str, Any], essential_fields: Set[str]) -> Dict[str, Any]:
    """Filter data to keep only essential fields.

    Args:
        data: Data to filter.
        essential_fields: Set of field names to keep.

    Returns:
        Dict[str, Any]: Filtered data containing only essential fields.
    """
    return {k: v for k, v in data.items() if k in essential_fields}


def serialize_entity(entity: Any) -> Dict[str, Any]:
    """Serialize entity data for JSON response.

    Args:
        entity: Entity data to serialize.

    Returns:
        Dict[str, Any]: Serialized entity data.
    """

    def _serialize_value(value: Any) -> Any:
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, dict):
            return {k: _serialize_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [_serialize_value(v) for v in value]
        return value

    if not isinstance(entity, dict):
        return {}
    return {k: _serialize_value(v) for k, v in entity.items()}
