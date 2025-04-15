"""Constants module for ShotGrid server.

This module contains all constant values used throughout the ShotGrid server application.
"""

# No imports needed

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500


# Common entity types - using a subset of EntityType
DEFAULT_ENTITY_TYPES = [
    "Version",
    "Shot",
    "Asset",
    "Task",
    "Sequence",
    "Project",
    "CustomEntity01",
    "CustomEntity02",
    "CustomEntity03",
]

# Custom entity types can be added through environment variables
ENV_CUSTOM_ENTITY_TYPES = "SHOTGRID_CUSTOM_ENTITY_TYPES"  # Comma-separated list of custom entity types
ENTITY_TYPES_ENV_VAR = "ENTITY_TYPES"  # For backward compatibility

# Batch operation limits
MAX_BATCH_SIZE = 100  # Maximum number of operations per batch request
MAX_FUZZY_RANGE = 1000  # Maximum range for fuzzy ID searches
MAX_ID_RANGE = 10000  # Maximum range for ID-based searches
