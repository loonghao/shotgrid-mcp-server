"""ShotGrid MCP Server Package.

This package provides a Model Context Protocol (MCP) server for ShotGrid,
allowing AI assistants to interact with ShotGrid data.
"""

__version__ = "0.1.0"

# Define exported symbols
__all__ = [
    # Exceptions
    "ConnectionError",
    "EntityNotFoundError",
    "FilterError",
    "PermissionError",
    "SerializationError",
    "ShotGridMCPError",
    # Filter utilities
    "build_date_filter",
    "combine_filters",
    "create_date_filter",
    "process_filters",
    # Models
    "DateRangeFilter",
    "EntityDict",
    "EntitiesResponse",
    "Filter",
    "FilterList",
    "FilterOperator",
    "ProjectDict",
    "ProjectsResponse",
    "ShotGridDataType",
    "TimeFilter",
    "TimeUnit",
    "UserDict",
    "UsersResponse",
    "create_assigned_to_filter",
    "create_between_filter",
    "create_by_user_filter",
    "create_contains_filter",
    "create_in_last_filter",
    "create_in_next_filter",
    "create_in_project_filter",
    "create_is_filter",
    "create_today_filter",
    "create_tomorrow_filter",
    "create_yesterday_filter",
    # Server
    "create_server",
    "main",
    # Utilities
    "ShotGridJSONEncoder",
    "serialize_entity",
]

from shotgrid_mcp_server.exceptions import (
    ConnectionError,
    EntityNotFoundError,
    FilterError,
    PermissionError,
    SerializationError,
    ShotGridMCPError,
)
from shotgrid_mcp_server.filters import (
    build_date_filter,
    combine_filters,
    create_date_filter,
    process_filters,
)
from shotgrid_mcp_server.models import (
    DateRangeFilter,
    EntitiesResponse,
    EntityDict,
    Filter,
    FilterList,
    FilterOperator,
    ProjectDict,
    ProjectsResponse,
    ShotGridDataType,
    TimeFilter,
    TimeUnit,
    UserDict,
    UsersResponse,
    create_assigned_to_filter,
    create_between_filter,
    create_by_user_filter,
    create_contains_filter,
    create_in_last_filter,
    create_in_next_filter,
    create_in_project_filter,
    create_is_filter,
    create_today_filter,
    create_tomorrow_filter,
    create_yesterday_filter,
)
from shotgrid_mcp_server.server import create_server, main
from shotgrid_mcp_server.utils import ShotGridJSONEncoder, serialize_entity
