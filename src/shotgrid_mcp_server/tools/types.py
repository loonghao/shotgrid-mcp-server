"""Type definitions for ShotGrid MCP server tools.

This module contains type definitions used across the tools modules.
"""

from typing import Any, Dict, List

from shotgrid_mcp_server.custom_types import EntityType, Filter

# Define a type alias for FastMCP
FastMCPType = Any

# Define common type aliases
FilterList = List[Filter]
EntityDict = Dict[str, Any]
EntityList = List[EntityType]
