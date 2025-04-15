"""Type definitions for ShotGrid MCP server tools.

This module contains type definitions used across the tools modules.
"""

from typing import Any, Dict, List, TypeVar

from fastmcp import FastMCP

from shotgrid_mcp_server.types import Entity, Filter

# Define a type variable for FastMCP
T = TypeVar("T")
FastMCPType = FastMCP[T]

# Define common type aliases
FilterList = List[Filter]
EntityDict = Dict[str, Any]
EntityList = List[Entity]
