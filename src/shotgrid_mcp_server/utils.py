"""Utility functions for ShotGrid MCP server."""

# Import built-in modules
import json
import logging
import os
import ssl
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TypeVar, Union

# Import third-party modules
import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Import local modules
from shotgrid_mcp_server.constants import ENTITY_TYPES_ENV_VAR, ENV_CUSTOM_ENTITY_TYPES

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")

# Default entity types to support
DEFAULT_ENTITY_TYPES: Set[str] = {
    "Asset",
    "Shot",
    "Sequence",
    "Project",
    "Task",
    "HumanUser",
    "Group",
    "Version",
    "PublishedFile",
    "Note",
    "Department",
    "Step",
    "Playlist",
}


def create_ssl_context(minimum_version: Optional[int] = None) -> ssl.SSLContext:
    """Create an SSL context with specified minimum TLS version.

    Args:
        minimum_version: Minimum TLS version to use. Defaults to TLSv1.2.

    Returns:
        ssl.SSLContext: Configured SSL context.
    """
    # Create default context
    context = ssl.create_default_context()

    # Set minimum TLS version if specified
    if minimum_version is not None:
        context.minimum_version = minimum_version
    else:
        # Default to TLSv1.2 which is widely supported
        context.minimum_version = ssl.TLSVersion.TLSv1_2

    logger.debug(
        "Created SSL context with minimum TLS version: %s",
        "TLSv1.2" if context.minimum_version == ssl.TLSVersion.TLSv1_2 else str(context.minimum_version),
    )

    return context


def create_session() -> requests.Session:
    """Create a requests session with retry logic and proper SSL configuration.

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

    # Mount retry adapter with SSL configuration
    adapter = HTTPAdapter(max_retries=retries, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    return session


def download_file(url: str, local_path: str, chunk_size: int = 8192) -> str:
    """Download a file from a URL with multiple fallback mechanisms for SSL issues.

    Args:
        url: URL to download from.
        local_path: Path to save the file to.
        chunk_size: Size of chunks to download in bytes.

    Returns:
        str: Path to the downloaded file.

    Raises:
        Exception: If all download methods fail.
    """
    # Import certifi for SSL certificate verification
    from urllib.request import urlopen

    import certifi

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)

    # Try multiple methods to handle various SSL issues
    methods_tried = []

    # Method 1: Use requests with verify=True (default)
    try:
        methods_tried.append("requests with verify=True")
        # Create session with retry logic and SSL configuration
        session = create_session()

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
        return local_path
    except Exception as e:
        logger.warning("Method 1 (requests with verify=True) failed: %s", str(e))

    # Method 2: Use requests with verify=False (insecure, but may work in some environments)
    try:
        methods_tried.append("requests with verify=False")
        # Suppress InsecureRequestWarning
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Create a session with SSL verification disabled
        no_verify_session = requests.Session()
        no_verify_session.verify = False

        # Configure retry strategy
        retries = Retry(total=3, backoff_factor=0.3, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retries)
        no_verify_session.mount("http://", adapter)
        no_verify_session.mount("https://", adapter)

        with no_verify_session.get(url, stream=True) as response:
            response.raise_for_status()

            with open(local_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        logger.info("Successfully downloaded file to %s with SSL verification disabled", local_path)
        return local_path
    except Exception as e:
        logger.warning("Method 2 (requests with verify=False) failed: %s", str(e))

    # Method 3: Use urllib with custom SSL context
    try:
        methods_tried.append("urllib with custom SSL context")
        # Create a custom SSL context that's more permissive
        context = ssl.create_default_context(cafile=certifi.where())
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE

        with urlopen(url, context=context, timeout=30) as response:
            with open(local_path, "wb") as f:
                f.write(response.read())

        logger.info("Successfully downloaded file to %s using urllib with custom SSL context", local_path)
        return local_path
    except Exception as e:
        logger.warning("Method 3 (urllib with custom SSL context) failed: %s", str(e))

    # Method 4: Try with completely disabled SSL verification and older protocol
    try:
        methods_tried.append("urllib with completely disabled SSL")
        # Create a context with no verification at all
        context = ssl._create_unverified_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # Try with older protocol versions
        context.options |= ssl.OP_NO_TLSv1_3
        context.options |= ssl.OP_NO_TLSv1_2
        context.options |= ssl.OP_NO_TLSv1_1
        # Force TLSv1.0
        context.minimum_version = ssl.TLSVersion.TLSv1
        context.maximum_version = ssl.TLSVersion.TLSv1

        with urlopen(url, context=context, timeout=30) as response:
            with open(local_path, "wb") as f:
                f.write(response.read())

        logger.info("Successfully downloaded file to %s using urllib with completely disabled SSL", local_path)
        return local_path
    except Exception as e:
        logger.warning("Method 4 (urllib with completely disabled SSL) failed: %s", str(e))

    # If all methods fail, raise an exception with details
    error_msg = f"All download methods failed for URL: {url}. Methods tried: {', '.join(methods_tried)}"
    logger.error(error_msg)
    raise Exception(error_msg)


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


# Mapping of common field names to their entity types
# This is used to infer entity types from field names when normalizing integer IDs
FIELD_TO_ENTITY_TYPE: Dict[str, str] = {
    "project": "Project",
    "entity": "Entity",  # Generic, may need context
    "task": "Task",
    "shot": "Shot",
    "asset": "Asset",
    "sequence": "Sequence",
    "version": "Version",
    "user": "HumanUser",
    "created_by": "HumanUser",
    "updated_by": "HumanUser",
    "assigned_to": "HumanUser",
    "artist": "HumanUser",
    "reviewer": "HumanUser",
    "sg_task": "Task",
    "sg_shot": "Shot",
    "sg_asset": "Asset",
    "sg_sequence": "Sequence",
    "sg_version": "Version",
    "sg_project": "Project",
    "sg_user": "HumanUser",
    "sg_assigned_to": "HumanUser",
    "department": "Department",
    "step": "Step",
    "sg_step": "Step",
    "sg_department": "Department",
    "note": "Note",
    "sg_note": "Note",
    "playlist": "Playlist",
    "sg_playlist": "Playlist",
    "published_file": "PublishedFile",
    "sg_published_file": "PublishedFile",
    "group": "Group",
    "sg_group": "Group",
    "linked_entity": "Entity",
    "parent": "Entity",
    "sg_parent": "Entity",
}


def infer_entity_type_from_field_name(field_name: str) -> str:
    """Infer entity type from field name.

    Args:
        field_name: The field name to infer entity type from.

    Returns:
        Inferred entity type string (e.g., 'Project' from 'project').
    """
    # Check if field name is in the mapping
    lower_field = field_name.lower()
    if lower_field in FIELD_TO_ENTITY_TYPE:
        return FIELD_TO_ENTITY_TYPE[lower_field]

    # Handle dot notation (e.g., "project.Project.id" -> "Project")
    if "." in field_name:
        parts = field_name.split(".")
        # Try the first part
        if parts[0].lower() in FIELD_TO_ENTITY_TYPE:
            return FIELD_TO_ENTITY_TYPE[parts[0].lower()]
        # If second part looks like an entity type, use it
        if len(parts) > 1 and parts[1][0].isupper():
            return parts[1]

    # Default: capitalize the field name (e.g., 'project' -> 'Project')
    return field_name.title().replace("_", "")


def normalize_entity_reference(value: Any, field_name: str) -> Any:
    """Normalize an entity reference value.

    Converts integer entity IDs to proper entity dict format.
    ShotGrid API expects entity references as {"type": "EntityType", "id": 123}.

    Args:
        value: The value to normalize (can be int, dict, or other).
        field_name: The field name to infer entity type from.

    Returns:
        Normalized value (dict format if was int, otherwise unchanged).

    Examples:
        >>> normalize_entity_reference(70, "project")
        {"type": "Project", "id": 70}

        >>> normalize_entity_reference({"type": "Project", "id": 70}, "project")
        {"type": "Project", "id": 70}

        >>> normalize_entity_reference("active", "status")
        "active"
    """
    if isinstance(value, int):
        entity_type = infer_entity_type_from_field_name(field_name)
        logger.debug(
            "Normalized integer entity reference: %s=%d -> {'type': '%s', 'id': %d}",
            field_name,
            value,
            entity_type,
            value,
        )
        return {"type": entity_type, "id": value}
    return value


def normalize_filter_value(filter_item: Any) -> Any:
    """Normalize a single filter item, converting integer entity IDs to dict format.

    Args:
        filter_item: A filter item, which can be:
            - A list like ["field", "operator", value]
            - A dict like {"field": value}
            - Other values (passed through unchanged)

    Returns:
        Normalized filter item.

    Examples:
        >>> normalize_filter_value(["project", "is", 70])
        ["project", "is", {"type": "Project", "id": 70}]

        >>> normalize_filter_value({"project": 70})
        {"project": {"type": "Project", "id": 70}}
    """
    if isinstance(filter_item, list) and len(filter_item) >= 3:
        # Standard filter format: ["field", "operator", value]
        field_name = filter_item[0]
        operator = filter_item[1]
        value = filter_item[2]

        # Handle dot notation field names (e.g., "project.Project.id")
        base_field = field_name.split(".")[0] if "." in field_name else field_name

        # Normalize the value
        normalized_value = normalize_entity_reference(value, base_field)

        # Handle list values (e.g., for "in" operator)
        if isinstance(value, list):
            normalized_value = [normalize_entity_reference(v, base_field) for v in value]

        return [field_name, operator, normalized_value] + list(filter_item[3:])

    elif isinstance(filter_item, dict):
        # Dict format filter: {"field": value}
        normalized = {}
        for key, value in filter_item.items():
            if key in ("filter_operator", "filters"):
                # Nested filter structure
                if key == "filters" and isinstance(value, list):
                    normalized[key] = normalize_filters(value)
                else:
                    normalized[key] = value
            else:
                normalized[key] = normalize_entity_reference(value, key)
        return normalized

    return filter_item


def normalize_filters(filters: List[Any]) -> List[Any]:
    """Normalize all filters, converting integer entity IDs to dict format.

    This function recursively processes filter lists to ensure all entity
    references are in the proper dict format expected by ShotGrid API.

    Args:
        filters: List of filter conditions.

    Returns:
        Normalized list of filters.

    Examples:
        >>> normalize_filters([["project", "is", 70]])
        [["project", "is", {"type": "Project", "id": 70}]]

        >>> normalize_filters([["project", "is", 70], ["shot", "is", 123]])
        [["project", "is", {"type": "Project", "id": 70}],
         ["shot", "is", {"type": "Shot", "id": 123}]]
    """
    if not isinstance(filters, list):
        return filters

    return [normalize_filter_value(f) for f in filters]


def normalize_grouping(grouping: Optional[List[Dict[str, Any]]]) -> Optional[List[Dict[str, Any]]]:
    """Normalize grouping configuration for sg_summarize.

    Args:
        grouping: List of grouping configurations.

    Returns:
        Normalized grouping list.
    """
    if not grouping:
        return grouping

    normalized = []
    for group in grouping:
        if isinstance(group, dict):
            normalized_group = dict(group)
            # The 'field' in grouping doesn't need entity normalization,
            # but if there are any entity reference values, normalize them
            for key, value in group.items():
                if key not in ("field", "type", "direction") and isinstance(value, int):
                    normalized_group[key] = normalize_entity_reference(value, key)
            normalized.append(normalized_group)
        else:
            normalized.append(group)
    return normalized


def normalize_data_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize entity references in a data dictionary.

    Used for create/update operations where data contains field-value pairs.

    Args:
        data: Dictionary of field names to values.

    Returns:
        Normalized dictionary with entity references converted.

    Examples:
        >>> normalize_data_dict({"project": 70, "code": "SH001"})
        {"project": {"type": "Project", "id": 70}, "code": "SH001"}
    """
    if not isinstance(data, dict):
        return data

    normalized = {}
    for key, value in data.items():
        if isinstance(value, int) and key.lower() in FIELD_TO_ENTITY_TYPE:
            # This looks like an entity field with an integer ID
            normalized[key] = normalize_entity_reference(value, key)
        elif isinstance(value, list):
            # Could be a multi-entity field
            if all(isinstance(v, int) for v in value) and key.lower() in FIELD_TO_ENTITY_TYPE:
                normalized[key] = [normalize_entity_reference(v, key) for v in value]
            else:
                normalized[key] = value
        else:
            normalized[key] = value
    return normalized


def normalize_batch_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize entity references in a batch request.

    Args:
        request: A batch request dictionary with request_type, entity_type, etc.

    Returns:
        Normalized batch request.
    """
    if not isinstance(request, dict):
        return request

    normalized = dict(request)

    # Normalize data field if present
    if "data" in normalized and isinstance(normalized["data"], dict):
        normalized["data"] = normalize_data_dict(normalized["data"])

    return normalized


def generate_default_file_path(
    entity_type: str, entity_id: int, field_name: str = "image", image_format: str = "jpg"
) -> str:
    """Generate a default file path for a thumbnail.

    Args:
        entity_type: Type of entity.
        entity_id: ID of entity.
        field_name: Name of field containing thumbnail.
        image_format: Format of the image.

    Returns:
        str: Default file path.
    """
    # Create a temporary directory if it doesn't exist
    temp_dir = Path(os.path.expanduser("~")) / ".shotgrid_mcp" / "thumbnails"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # Generate a filename based on entity type, id, and field name
    filename = f"{entity_type}_{entity_id}_{field_name}.{image_format}"
    return str(temp_dir / filename)
