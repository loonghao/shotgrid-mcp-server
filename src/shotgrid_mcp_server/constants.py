"""Constants module for ShotGrid server.

This module contains all constant values used throughout the ShotGrid server application.
"""

# HTTP Status Codes
HTTP_200_OK = 200
HTTP_201_CREATED = 201
HTTP_400_BAD_REQUEST = 400
HTTP_404_NOT_FOUND = 404
HTTP_500_INTERNAL_SERVER_ERROR = 500

# Environment Variables
ENV_SHOTGRID_URL = "SHOTGRID_URL"
ENV_SCRIPT_KEY = "SCRIPT_KEY"
ENV_SCRIPT_NAME = "SCRIPT_NAME"

# Common entity types
DEFAULT_ENTITY_TYPES = [
    "Version",
    "Shot",
    "Asset",
    "Task",
    "Sequence",
    "Project",
    "Scene",
    "CustomEntity01",
    "CustomEntity02",
    "CustomEntity03",
]

# Custom entity types can be added through environment variables
ENV_CUSTOM_ENTITY_TYPES = "SHOTGRID_CUSTOM_ENTITY_TYPES"  # Comma-separated list of custom entity types
ENTITY_TYPES_ENV_VAR = ENV_CUSTOM_ENTITY_TYPES  # Alias for backward compatibility

# Batch operation limits
MAX_BATCH_SIZE = 100  # Maximum number of operations per batch request
MAX_FUZZY_RANGE = 1000  # Maximum range for fuzzy ID searches
MAX_ID_RANGE = 10000  # Maximum range for ID-based searches

# ShotGrid API Credentials
ENV_SHOTGRID_URL = "SHOTGRID_URL"
ENV_SCRIPT_NAME = "SCRIPT_NAME"
ENV_SCRIPT_KEY = "SCRIPT_KEY"

# API Routes
API_PREFIX = "/api/v1"
HEALTH_CHECK = "/health"
ENTITY = "/entity"
ENTITIES = "/entities"
DOWNLOAD = "/download"
