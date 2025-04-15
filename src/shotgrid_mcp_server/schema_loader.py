"""Schema loader module for ShotGrid MCP server.

This module provides utilities for loading schema files for the MockgunExt class.
"""

# Import built-in modules
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


def find_schema_files() -> Tuple[str, str]:
    """Find schema files in various locations.

    Returns:
        Tuple[str, str]: Paths to schema.bin and entity_schema.bin files.

    Raises:
        FileNotFoundError: If schema files cannot be found.
    """
    # Try different locations for schema files
    # 1. First try package data directory
    package_dir = Path(__file__).parent
    schema_path = os.path.join(package_dir, "data", "schema.bin")
    schema_entity_path = os.path.join(package_dir, "data", "entity_schema.bin")

    # 2. If not found, try tests directory in package
    if not (os.path.exists(schema_path) and os.path.exists(schema_entity_path)):
        package_root = package_dir.parent.parent
        schema_path = os.path.join(package_root, "tests", "data", "schema.bin")
        schema_entity_path = os.path.join(package_root, "tests", "data", "entity_schema.bin")

    # 3. If still not found, try current directory and parent directories
    if not (os.path.exists(schema_path) and os.path.exists(schema_entity_path)):
        current_dir = Path.cwd()
        for _ in range(5):  # Look up to 5 levels up
            test_schema_path = os.path.join(current_dir, "tests", "data", "schema.bin")
            test_schema_entity_path = os.path.join(current_dir, "tests", "data", "entity_schema.bin")

            if os.path.exists(test_schema_path) and os.path.exists(test_schema_entity_path):
                schema_path = test_schema_path
                schema_entity_path = test_schema_entity_path
                break

            current_dir = current_dir.parent

    # Check if files were found
    if not (os.path.exists(schema_path) and os.path.exists(schema_entity_path)):
        error_msg = f"Schema files not found: {schema_path}, {schema_entity_path}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Log the paths we're using
    logger.info(f"Using schema files: {schema_path} and {schema_entity_path}")
    return schema_path, schema_entity_path


def ensure_schema_directory() -> Path:
    """Ensure the schema directory exists.

    Returns:
        Path: Path to the schema directory.
    """
    schema_dir = Path(__file__).parent / "data"
    os.makedirs(schema_dir, exist_ok=True)
    return schema_dir


def copy_schema_files(source_dir: Path, target_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """Copy schema files from source to target directory.

    Args:
        source_dir: Source directory containing schema files.
        target_dir: Target directory to copy files to. If None, uses package data directory.

    Returns:
        Tuple[Path, Path]: Paths to the copied schema files.

    Raises:
        FileNotFoundError: If source schema files cannot be found.
    """
    import shutil

    # Set default target directory if not provided
    if target_dir is None:
        target_dir = ensure_schema_directory()

    # Source schema files
    source_schema = source_dir / "schema.bin"
    source_schema_entity = source_dir / "entity_schema.bin"

    # Check if source files exist
    if not source_schema.exists() or not source_schema_entity.exists():
        error_msg = f"Source schema files not found: {source_schema}, {source_schema_entity}"
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    # Target schema files
    target_schema = target_dir / "schema.bin"
    target_schema_entity = target_dir / "entity_schema.bin"

    # Copy files
    shutil.copy2(source_schema, target_schema)
    shutil.copy2(source_schema_entity, target_schema_entity)

    logger.info(f"Copied schema files to {target_dir}")
    return target_schema, target_schema_entity
