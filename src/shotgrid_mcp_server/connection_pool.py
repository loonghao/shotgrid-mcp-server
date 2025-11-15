# -*- coding: utf-8 -*-

"""
ShotGrid connection pool and factory implementation.
Provides thread-safe API calls for Python 3.x
Requires Shotgun Python API: https://github.com/shotgunsoftware/python-api

The connection pool implementation is based on:
https://gist.github.com/danielskovli/cfec8aae6c0e1ab7e418e5a222a489fb
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional, Tuple, TypeVar

import shotgun_api3

# Import local modules
from shotgrid_mcp_server.exceptions import NoAvailableInstancesError

# Configure logging
logger = logging.getLogger(__name__)

# Type variables
T = TypeVar("T")


# ShotGrid arguments handling functions
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

    # Get connection parameters with defaults
    max_rpc_attempts = _get_value_from_shotgun_args(
        shotgun_args, "max_rpc_attempts", default_value=10
    )  # Increased from 5 to 10 for better reliability with slow connections (default: 5)
    timeout_secs = _get_value_from_shotgun_args(
        shotgun_args, "timeout_secs", default_value=30
    )  # Increased from 10 to 30 seconds to handle larger responses (default: 10)
    rpc_attempt_interval = _get_value_from_shotgun_args(
        shotgun_args, "rpc_attempt_interval", default_value=10000
    )  # Increased from 5000 to 10000ms to reduce server load (default: 5000)

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


class InstancePoolManager:
    """Manager for `InstancePool`"""

    def __init__(self, pool: InstancePool):
        """Initialize a new InstancePoolManager. This object will handle enter/exit hooks during a `with` clause
        Args:
            pool (InstancePool): The InstancePool to interact with
        """

        self.pool = pool
        self.obj = None

    def __enter__(self):
        """User-code has entered `with` clause, acquire Shotgun instance"""

        self.instance = self.pool.acquire()
        logger.debug(
            f"Manager: Allocated Shotgun instance with ID {id(self.instance)} (session token {self.instance.config.session_token})"
        )

        return self.instance

    def __exit__(self, *_):
        """User-code has exited `with` clause, release Shotgun instance"""

        self.pool.release(self.instance)


class InstancePool:
    """Instance pool that keeps track of `Shotgun` instances.

    Based on the implementation from:
    https://gist.github.com/danielskovli/cfec8aae6c0e1ab7e418e5a222a489fb
    """

    def __init__(self, host: str, scriptName: str, apiKey: str, size: int = -1):
        """Initialize a new InstancePool
        Args:
            host (str): Base URL to Shotgun site. Eg. https://your-site.shotgunstudio.com
            scriptName (str): API key name
            apiKey (str): API key secret
            size (int, optional): Max pool size. Defaults to -1, which means unlimited
        """

        self.host = host
        self.scriptName = scriptName
        self.apiKey = apiKey
        self.size = size
        self.free: list[shotgun_api3.Shotgun] = []
        self.inUse: list[shotgun_api3.Shotgun] = []

    @property
    def currentSize(self) -> int:
        return len(self.free) + len(self.inUse)

    def acquire(self) -> shotgun_api3.Shotgun:
        """Acquire an instance from the pool. Recycle if possible, create new if required (within `self.size` limits)"""

        numFree = len(self.free)
        numUsed = len(self.inUse)

        if self.size > -1 and numFree == 0 and numUsed >= self.size:
            raise NoAvailableInstancesError(
                f"No further instances can be allocated, as defined by user-defined maximum pool size: {self.size}"
            )

        instance: shotgun_api3.Shotgun
        if numFree:
            logger.debug("Acquire: Returning existing free instance")
            instance = self.free.pop(0)
        else:
            logger.debug("Acquire: Generating new instance")
            instance = self.instanceFactory()

        self.inUse.append(instance)
        return instance

    def release(self, r: shotgun_api3.Shotgun):
        """Release an instance -> move it from `inUse` to `free`"""

        self.inUse.remove(r)
        self.free.append(r)

    def instanceFactory(self) -> shotgun_api3.Shotgun:
        """Generate a new, or clone existing shotgun connection as applicable"""

        existingInstance: Optional[shotgun_api3.Shotgun] = None

        # Realistically this never happens if called from `self.acquire`
        if self.free and self.free[0].config.session_token:
            existingInstance = self.free[0]

        # This is more likely to happen, since the reason we're generating an instance is because all existing ones are busy
        elif self.inUse and self.inUse[0].config.session_token:
            existingInstance = self.inUse[0]

        # We have an instance, clone it
        if existingInstance:
            logger.debug(f"Factory: Using existing instance session token: {existingInstance.config.session_token}")
            # Create a new instance with the existing session token
            instance = shotgun_api3.Shotgun(
                base_url=self.host,
                connect=False,
                session_token=existingInstance.config.session_token,
            )
            instance._connection = None

            # Get connection parameters with defaults
            connection_args = get_shotgun_connection_args()

            # Configure connection parameters
            instance.config.max_rpc_attempts = connection_args["max_rpc_attempts"]
            instance.config.timeout_secs = connection_args["timeout_secs"]
            instance.config.rpc_attempt_interval = connection_args["rpc_attempt_interval"]

            return instance

        # Need to generate new instance, which will require authentication
        else:
            logger.debug("Factory: Generating new instance with auth creds")
            # Use create_shotgun_connection to create a new instance
            instance = create_shotgun_connection(
                url=self.host,
                script_name=self.scriptName,
                api_key=self.apiKey,
            )

            # Force authentication and store session token
            instance.config.session_token = instance.get_session_token()

            return instance


# Factory functions from factory.py
def create_shotgun_connection(
    url: str,
    script_name: str,
    api_key: str,
    shotgun_args: Optional[Dict[str, Any]] = None,
) -> shotgun_api3.Shotgun:
    """Create a ShotGrid connection with optimized parameters.

    Args:
        url: ShotGrid server URL.
        script_name: Script name for authentication.
        api_key: API key for authentication.
        shotgun_args: Optional dictionary of ShotGrid arguments.

    Returns:
        shotgun_api3.Shotgun: A new ShotGrid connection.
    """
    shotgun_args = shotgun_args or {}

    # Get connection parameters with defaults
    connection_args = get_shotgun_connection_args(shotgun_args)

    # Get remaining kwargs
    kwargs = _ignore_shotgun_args(shotgun_args)

    # Create ShotGrid connection
    sg = shotgun_api3.Shotgun(base_url=url, script_name=script_name, api_key=api_key, **kwargs)

    # Configure connection parameters
    sg.config.max_rpc_attempts = connection_args["max_rpc_attempts"]
    sg.config.timeout_secs = connection_args["timeout_secs"]
    sg.config.rpc_attempt_interval = connection_args["rpc_attempt_interval"]

    # Log connection parameters
    logger.debug(
        "ShotGrid connection parameters: max_rpc_attempts=%s, timeout_secs=%s, rpc_attempt_interval=%s",
        connection_args["max_rpc_attempts"],
        connection_args["timeout_secs"],
        connection_args["rpc_attempt_interval"],
    )

    return sg


def get_shotgun_credentials(
    url: Optional[str] = None,
    script_name: Optional[str] = None,
    api_key: Optional[str] = None,
    require_env_vars: bool = True,
) -> Tuple[str, str, str]:
    """Get ShotGrid credentials from arguments or environment variables.

    Args:
        url: ShotGrid server URL. If None, uses SHOTGRID_URL environment variable.
        script_name: ShotGrid script name. If None, uses SHOTGRID_SCRIPT_NAME environment variable.
        api_key: ShotGrid API key. If None, uses SHOTGRID_SCRIPT_KEY environment variable.
        require_env_vars: If True, raises ValueError if environment variables are missing.

    Returns:
        Tuple[str, str, str]: URL, script name, and API key.

    Raises:
        ValueError: If required environment variables are missing and require_env_vars is True.
    """
    # Get values from arguments or environment variables
    url_value = url or os.getenv("SHOTGRID_URL")
    script_name_value = script_name or os.getenv("SHOTGRID_SCRIPT_NAME")
    api_key_value = api_key or os.getenv("SHOTGRID_SCRIPT_KEY")

    # Check if all required values are present
    if require_env_vars and not all([url_value, script_name_value, api_key_value]):
        missing_vars = []
        if not url_value:
            missing_vars.append("SHOTGRID_URL")
        if not script_name_value:
            missing_vars.append("SHOTGRID_SCRIPT_NAME")
        if not api_key_value:
            missing_vars.append("SHOTGRID_SCRIPT_KEY")

        error_msg = (
            f"Missing required environment variables for ShotGrid connection: {', '.join(missing_vars)}\n\n"
            "To fix this issue, please set the following environment variables before starting the server:\n"
            "  - SHOTGRID_URL: Your ShotGrid server URL (e.g., https://your-studio.shotgunstudio.com)\n"
            "  - SHOTGRID_SCRIPT_NAME: Your ShotGrid script name\n"
            "  - SHOTGRID_SCRIPT_KEY: Your ShotGrid script key\n\n"
            "Example:\n"
            "  Windows: set SHOTGRID_URL=https://your-studio.shotgunstudio.com\n"
            "  Linux/macOS: export SHOTGRID_URL=https://your-studio.shotgunstudio.com\n\n"
            "Alternatively, you can configure these in your MCP client settings.\n"
            "See the documentation for more details: \n"
            "https://github.com/loonghao/shotgrid-mcp-server#-mcp-client-configuration"
        )

        logger.error("Missing required environment variables for ShotGrid connection")
        logger.debug("SHOTGRID_URL: %s", url_value)
        logger.debug("SHOTGRID_SCRIPT_NAME: %s", script_name_value)
        logger.debug("SHOTGRID_SCRIPT_KEY: %s", api_key_value)
        raise ValueError(error_msg)

    # Use default values if not provided and not requiring environment variables
    url_value = url_value or "https://example.shotgunstudio.com"
    script_name_value = script_name_value or "script_name"
    api_key_value = api_key_value or "script_key"

    return url_value, script_name_value, api_key_value


def create_shotgun_connection_from_env(
    shotgun_args: Optional[Dict[str, Any]] = None,
) -> shotgun_api3.Shotgun:
    """Create a ShotGrid connection from environment variables.

    Args:
        shotgun_args: Optional dictionary of ShotGrid arguments.

    Returns:
        shotgun_api3.Shotgun: A new ShotGrid connection.

    Raises:
        ValueError: If required environment variables are missing.
    """
    url, script_name, api_key = get_shotgun_credentials(require_env_vars=True)

    return create_shotgun_connection(
        url=url,
        script_name=script_name,
        api_key=api_key,
        shotgun_args=shotgun_args,
    )


class ShotgunClient:
    """Shotgun API Wrapper"""

    def __init__(
        self,
        poolSize: int = -1,
        url: Optional[str] = None,
        script_name: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> None:
        """Shotgun API wrapper.

        Most methods will block while waiting for http, so best called on a separate thread.

        To access the `shotgun_api3.Shotgun` instance directly at any stage, use the `InstancePoolManager`
        or in a pinch, the `.instance` getter

        Args:
            poolSize: Maximum number of connections in the pool. -1 means unlimited.
            url: ShotGrid server URL. If None, uses SHOTGRID_URL environment variable.
            script_name: ShotGrid script name. If None, uses SHOTGRID_SCRIPT_NAME environment variable.
            api_key: ShotGrid API key. If None, uses SHOTGRID_SCRIPT_KEY environment variable.
        """
        super().__init__()

        # Get connection parameters from arguments or environment variables
        host, script_name_value, api_key_value = get_shotgun_credentials(
            url=url, script_name=script_name, api_key=api_key, require_env_vars=False
        )

        self.instancePool = InstancePool(host=host, scriptName=script_name_value, apiKey=api_key_value, size=poolSize)

    @property
    def instance(self) -> shotgun_api3.Shotgun:
        """Acquires a `Shotgun` instance from the instance pool directly.

        This will work, and will be tracked, but will never be recycled unless done so
        manually by the caller. Eg. herein lies memory leaks...

        A better way to access the Shotgun instance is to call the pool manager via:
        `with InstancePoolManager(self.instancePool) as sg: ...`
        """
        # This will be tracked in the pool, but unless the caller manually releases it,
        # the instance will never be returned and recycled
        return self.instancePool.acquire()


class ShotGridConnectionContext:
    """Context manager for safely handling ShotGrid connections."""

    def __init__(
        self,
        factory_or_connection: Optional[shotgun_api3.Shotgun] = None,
    ) -> None:
        """Initialize the context manager.

        Args:
            factory_or_connection: Direct Shotgun connection or None.
        """
        # If a direct connection is provided, use it
        if isinstance(factory_or_connection, shotgun_api3.Shotgun):
            self.connection: Optional[shotgun_api3.Shotgun] = factory_or_connection
            self.sg_client: Optional[ShotgunClient] = None
        else:
            # Create a ShotgunClient with default pool size and environment variables
            self.sg_client = ShotgunClient(poolSize=-1)  # Use unlimited pool size by default
            self.connection = None

    def __enter__(self) -> shotgun_api3.Shotgun:
        """Create a new ShotGrid connection.

        Returns:
            Shotgun: A new ShotGrid connection.

        Raises:
            Exception: If connection creation fails.
        """
        try:
            if self.connection:
                # Direct connection was provided
                return self.connection
            else:
                # Use ShotgunClient instance
                assert self.sg_client is not None, "ShotgunClient is None"
                self.connection = self.sg_client.instance
                return self.connection
        except Exception as e:
            logger.error("Failed to create connection: %s", str(e), exc_info=True)
            raise

    def __exit__(self, *_) -> None:
        """Clean up the connection."""
        # Release the connection back to the pool if using ShotgunClient
        if self.sg_client is not None and self.connection is not None:
            # We know sg_client is not None here
            sg_client = self.sg_client
            if self.connection in sg_client.instancePool.inUse:
                sg_client.instancePool.release(self.connection)

        # Set connection to None
        self.connection = None
