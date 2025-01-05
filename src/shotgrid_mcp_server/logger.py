"""Logging configuration for the ShotGrid MCP server.

This module provides a centralized logging configuration for the entire application.
"""

# Import built-in modules
import logging
import logging.handlers
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import third-party modules
from platformdirs import PlatformDirs

# Create platform dirs instance
dirs = PlatformDirs("shotgrid-mcp-server")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: The name of the logger. If None, returns the root logger.

    Returns:
        logging.Logger: A logger instance.
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def setup_logging(log_dir: Optional[str] = None) -> None:
    """Set up logging configuration.

    Args:
        log_dir: Optional directory to store log files. If not provided,
                logs will be stored in the platform-specific user log directory.
    """
    # Use platform-specific log directory if not specified
    if log_dir is None:
        log_dir = dirs.user_log_dir

    # Create logs directory if it doesn't exist
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # Generate log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_path / f"shotgrid_mcp_server_{timestamp}.log"

    # Create formatters
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s")
    console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        str(log_file),  # Convert Path to str for compatibility
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)
    console_handler.setLevel(logging.INFO)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Create logger for this application
    logger = logging.getLogger("mcp_shotgrid_server")
    logger.info("Logging system initialized. Log file: %s", log_file)
