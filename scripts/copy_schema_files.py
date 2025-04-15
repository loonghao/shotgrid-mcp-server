#!/usr/bin/env python
"""
Copy schema files to the package directory during installation.
This script is meant to be run during the package installation process.
"""

import os
import shutil
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CopySchemaFilesBuildHook(BuildHookInterface):
    """Build hook to copy schema files to the package directory."""

    def initialize(self, version, build_data):
        """Initialize the build hook.

        Args:
            version: The version of the package being built.
            build_data: The build data.
        """
        # Get the source directory (project root)
        source_dir = Path(self.root)

        # Source schema files
        source_schema = source_dir / "tests" / "data" / "schema.bin"
        source_schema_entity = source_dir / "tests" / "data" / "entity_schema.bin"

        # Get the package directory
        package_dir = source_dir / "src" / "shotgrid_mcp_server"

        # Create target directory if it doesn't exist
        target_dir = package_dir / "data"
        os.makedirs(target_dir, exist_ok=True)

        # Target schema files
        target_schema = target_dir / "schema.bin"
        target_schema_entity = target_dir / "entity_schema.bin"

        # Copy files
        if source_schema.exists():
            shutil.copy2(source_schema, target_schema)
            print(f"Copied schema file to {target_schema}")
        else:
            print(f"Warning: Source schema file {source_schema} not found")

        if source_schema_entity.exists():
            shutil.copy2(source_schema_entity, target_schema_entity)
            print(f"Copied schema entity file to {target_schema_entity}")
        else:
            print(f"Warning: Source schema entity file {source_schema_entity} not found")


# This is the hook that will be loaded by hatchling
build_hook = CopySchemaFilesBuildHook
