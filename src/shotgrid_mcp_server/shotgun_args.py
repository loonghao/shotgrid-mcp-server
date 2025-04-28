"""ShotGrid arguments handling module.

This module provides utilities for handling ShotGrid arguments and configuration.
"""

import logging
from typing import Any, Dict, Optional, TypeVar

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")


def _get_value_from_shotgun_args(
    shotgun_args: Dict[str, Any],
    key: str,
    default_value: T,
) -> T:
    """Get a value from ShotGrid arguments with a default fallback.

    Args:
        shotgun_args: Dictionary of ShotGrid arguments.
        key: Key to look up in the arguments.
        default_value: Default value to use if key is not found.

    Returns:
        Value from arguments or default value.
    """
    if not shotgun_args or key not in shotgun_args:
        return default_value

    value = shotgun_args.get(key)
    if value is None:
        return default_value

    return value


def _ignore_shotgun_args(shotgun_args: Dict[str, Any]) -> Dict[str, Any]:
    """Filter out ShotGrid-specific arguments.

    Args:
        shotgun_args: Dictionary of ShotGrid arguments.

    Returns:
        Dictionary with ShotGrid-specific arguments removed.
    """
    if not shotgun_args:
        return {}

    # Create a copy of the arguments
    kwargs = shotgun_args.copy()

    # Remove ShotGrid-specific arguments
    for key in ["max_rpc_attempts", "timeout_secs", "rpc_attempt_interval"]:
        if key in kwargs:
            del kwargs[key]

    return kwargs


def get_shotgun_connection_args(
    shotgun_args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Get ShotGrid connection arguments with default values.

    Args:
        shotgun_args: Optional dictionary of ShotGrid arguments.

    Returns:
        Dictionary of ShotGrid connection arguments with defaults applied.
    """
    shotgun_args = shotgun_args or {}

    # Get connection parameters with defaults (increased for better reliability)
    max_rpc_attempts = _get_value_from_shotgun_args(
        shotgun_args, "max_rpc_attempts", default_value=10
    )  # Increased from 5 to 10 for better reliability with slow connections
    timeout_secs = _get_value_from_shotgun_args(
        shotgun_args, "timeout_secs", default_value=30
    )  # Increased from 10 to 30 seconds to handle larger responses
    rpc_attempt_interval = _get_value_from_shotgun_args(
        shotgun_args, "rpc_attempt_interval", default_value=10000
    )  # Increased from 5000 to 10000ms to reduce server load

    # Create connection arguments dictionary
    connection_args = {
        "max_rpc_attempts": max_rpc_attempts,
        "timeout_secs": timeout_secs,
        "rpc_attempt_interval": rpc_attempt_interval,
    }

    # Log connection parameters
    logger.debug(
        "ShotGrid connection parameters: max_rpc_attempts=%s, timeout_secs=%s, rpc_attempt_interval=%s",
        max_rpc_attempts,
        timeout_secs,
        rpc_attempt_interval,
    )

    return connection_args
