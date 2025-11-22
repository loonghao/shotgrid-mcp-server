"""Schema caching for ShotGrid MCP Server.

This module provides caching functionality for ShotGrid schema data to improve
performance and reduce API calls. It uses diskcache_rs for persistent caching.

The cache stores:
- Entity schemas (field definitions, data types, validation rules)
- Entity types list
- Field schemas for specific entity types

Cache TTL (Time To Live):
- Schema data: 24 hours (86400 seconds)
- Entity types: 24 hours (86400 seconds)

This allows the server to validate field names and types without making
repeated API calls to ShotGrid.
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from diskcache_rs import DiskCache
from platformdirs import PlatformDirs

logger = logging.getLogger(__name__)

# Create platform dirs instance (same as logger.py for consistent directory structure)
_dirs = PlatformDirs("shotgrid-mcp-server")

# Default cache directory - same level as logs
# Structure: <user_data_dir>/shotgrid-mcp-server/schema
# This keeps all shotgrid-mcp-server data organized in one place:
#   - <user_data_dir>/shotgrid-mcp-server/schema  (schema cache)
#   - <user_log_dir>/shotgrid-mcp-server/         (logs)
DEFAULT_CACHE_DIR = Path(_dirs.user_data_dir) / "schema"

# Default TTL for schema data (24 hours)
DEFAULT_SCHEMA_TTL = 86400


class SchemaCache:
    """Cache for ShotGrid schema data.

    This class provides a simple interface for caching and retrieving
    ShotGrid schema information using diskcache_rs.

    Example:
        >>> cache = SchemaCache()
        >>> cache.set_entity_schema("Shot", schema_data)
        >>> schema = cache.get_entity_schema("Shot")
    """

    def __init__(self, cache_dir: Path | str = DEFAULT_CACHE_DIR, ttl: int = DEFAULT_SCHEMA_TTL):
        """Initialize the schema cache.

        Args:
            cache_dir: Directory to store cache files (Path or str)
            ttl: Time to live for cached items in seconds
        """
        # Convert to Path if string
        if isinstance(cache_dir, str):
            cache_dir = Path(cache_dir)

        # Ensure cache directory exists
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize cache with string path
        self.cache = DiskCache(str(cache_dir))
        self.ttl = ttl
        logger.info(f"Initialized schema cache at {cache_dir} with TTL={ttl}s")

    def get_entity_schema(self, entity_type: str) -> Optional[Dict[str, Any]]:
        """Get cached schema for an entity type.

        Args:
            entity_type: ShotGrid entity type (e.g., "Shot", "Asset")

        Returns:
            Schema dictionary if cached, None otherwise
        """
        key = f"entity_schema:{entity_type}"
        value = self.cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit for entity schema: {entity_type}")
        else:
            logger.debug(f"Cache miss for entity schema: {entity_type}")
        return value

    def set_entity_schema(self, entity_type: str, schema: Dict[str, Any]) -> None:
        """Cache schema for an entity type.

        Args:
            entity_type: ShotGrid entity type (e.g., "Shot", "Asset")
            schema: Schema dictionary from ShotGrid API
        """
        key = f"entity_schema:{entity_type}"
        self.cache.set(key, schema, expire=self.ttl)
        logger.debug(f"Cached entity schema: {entity_type}")

    def get_field_schema(self, entity_type: str, field_name: str) -> Optional[Dict[str, Any]]:
        """Get cached schema for a specific field.

        Args:
            entity_type: ShotGrid entity type (e.g., "Shot", "Asset")
            field_name: Field name (e.g., "code", "sg_status_list")

        Returns:
            Field schema dictionary if cached, None otherwise
        """
        key = f"field_schema:{entity_type}:{field_name}"
        value = self.cache.get(key)
        if value is not None:
            logger.debug(f"Cache hit for field schema: {entity_type}.{field_name}")
        else:
            logger.debug(f"Cache miss for field schema: {entity_type}.{field_name}")
        return value

    def set_field_schema(self, entity_type: str, field_name: str, schema: Dict[str, Any]) -> None:
        """Cache schema for a specific field.

        Args:
            entity_type: ShotGrid entity type (e.g., "Shot", "Asset")
            field_name: Field name (e.g., "code", "sg_status_list")
            schema: Field schema dictionary from ShotGrid API
        """
        key = f"field_schema:{entity_type}:{field_name}"
        self.cache.set(key, schema, expire=self.ttl)
        logger.debug(f"Cached field schema: {entity_type}.{field_name}")

    def get_entity_types(self) -> Optional[Dict[str, Any]]:
        """Get cached list of entity types.

        Returns:
            Dictionary of entity types if cached, None otherwise
        """
        key = "entity_types"
        value = self.cache.get(key)
        if value is not None:
            logger.debug("Cache hit for entity types")
        else:
            logger.debug("Cache miss for entity types")
        return value

    def set_entity_types(self, entity_types: Dict[str, Any]) -> None:
        """Cache list of entity types.

        Args:
            entity_types: Dictionary of entity types from ShotGrid API
        """
        key = "entity_types"
        self.cache.set(key, entity_types, expire=self.ttl)
        logger.debug("Cached entity types")

    def clear(self) -> None:
        """Clear all cached data."""
        self.cache.clear()
        logger.info("Cleared schema cache")

    def close(self) -> None:
        """Close the cache."""
        self.cache.close()
        logger.info("Closed schema cache")


# Global cache instance
_global_cache: Optional[SchemaCache] = None


def get_schema_cache() -> SchemaCache:
    """Get the global schema cache instance.

    Returns:
        Global SchemaCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = SchemaCache()
    return _global_cache


async def preload_schemas(sg_connection: Any, entity_types: Optional[List[str]] = None) -> None:
    """Preload schemas for common entity types.

    This function should be called during server startup to cache
    schema data for frequently used entity types.

    Args:
        sg_connection: ShotGrid connection
        entity_types: List of entity types to preload. If None, preloads common types.
    """
    if entity_types is None:
        # Common entity types to preload
        entity_types = [
            "Shot",
            "Asset",
            "Task",
            "Version",
            "PublishedFile",
            "Note",
            "Project",
            "Sequence",
            "Episode",
            "CustomEntity01",  # Common custom entity
        ]

    cache = get_schema_cache()

    for entity_type in entity_types:
        try:
            # Check if already cached
            if cache.get_entity_schema(entity_type) is not None:
                logger.debug(f"Schema for {entity_type} already cached")
                continue

            # Fetch and cache schema
            schema = sg_connection.schema_field_read(entity_type)
            cache.set_entity_schema(entity_type, schema)
            logger.info(f"Preloaded schema for {entity_type}")
        except Exception as e:
            logger.warning(f"Failed to preload schema for {entity_type}: {e}")

    logger.info(f"Schema preloading completed for {len(entity_types)} entity types")
