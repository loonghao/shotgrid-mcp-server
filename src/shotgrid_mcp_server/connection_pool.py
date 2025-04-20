"""ShotGrid connection pool module.

This module provides simplified connection management for ShotGrid API.
"""

# Import built-in modules
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Optional, Type

# Import third-party modules
from shotgun_api3 import Shotgun

# Import local modules
from shotgrid_mcp_server.mockgun_ext import MockgunExt

# Configure logging
logger = logging.getLogger(__name__)


class ShotgunClientFactory(ABC):
    """Abstract factory for creating ShotGrid clients."""

    @abstractmethod
    def create_client(self) -> Shotgun:
        """Create a new ShotGrid client.

        Returns:
            Shotgun: A new ShotGrid client instance.
        """
        pass


class RealShotgunFactory(ShotgunClientFactory):
    """Factory for creating real ShotGrid clients."""

    def __init__(
        self,
        url: str,
        script_name: str,
        script_key: str,
        http_proxy: Optional[str] = None,
        ca_certs: Optional[str] = None,
    ) -> None:
        """Initialize the factory.

        Args:
            url: ShotGrid server URL
            script_name: Script name for authentication
            script_key: Script key for authentication
            http_proxy: Optional HTTP proxy
            ca_certs: Optional CA certificates path
        """
        self.url = url
        self.script_name = script_name
        self.script_key = script_key
        self.http_proxy = http_proxy
        self.ca_certs = ca_certs

    def create_client(self) -> Shotgun:
        """Create a real ShotGrid client.

        Returns:
            Shotgun: A new ShotGrid client instance.

        Raises:
            Exception: If connection creation fails.
        """
        sg = Shotgun(
            self.url,
            script_name=self.script_name,
            api_key=self.script_key,
            http_proxy=self.http_proxy,
            ca_certs=self.ca_certs,
        )
        sg.connect()
        logger.info("Successfully connected to ShotGrid at %s", self.url)
        return sg


class MockShotgunFactory(ShotgunClientFactory):
    """Factory for creating mock ShotGrid clients."""

    def __init__(self, schema_path: str, schema_entity_path: str) -> None:
        """Initialize the factory.

        Args:
            schema_path: Path to schema.json
            schema_entity_path: Path to schema_entity.json
        """
        self.schema_path = schema_path
        self.schema_entity_path = schema_entity_path

    def create_client(self) -> MockgunExt:
        """Create a mock ShotGrid client.

        Returns:
            MockgunExt: A new mock ShotGrid client instance.
        """
        # First, check if schema files exist
        if not os.path.exists(self.schema_path) or not os.path.exists(self.schema_entity_path):
            logger.error("Schema files not found: %s, %s", self.schema_path, self.schema_entity_path)
            raise ValueError(f"Schema files not found: {self.schema_path}, {self.schema_entity_path}")

        # Set schema paths before creating the instance
        # This is only required for MockgunExt
        MockgunExt.set_schema_paths(self.schema_path, self.schema_entity_path)

        # Create the instance
        sg = MockgunExt(
            "https://test.shotgunstudio.com",
            script_name="test_script",
            api_key="test_key",
        )
        logger.debug("Created mock ShotGrid connection")
        return sg


def create_default_factory() -> ShotgunClientFactory:
    """Create the default ShotGrid client factory.

    Returns:
        ShotgunClientFactory: The default factory instance.

    Raises:
        ValueError: If required environment variables are missing.
    """
    url = os.getenv("SHOTGRID_URL")
    script_name = os.getenv("SHOTGRID_SCRIPT_NAME")
    script_key = os.getenv("SHOTGRID_SCRIPT_KEY")

    if not all([url, script_name, script_key]):
        missing_vars = []
        if not url:
            missing_vars.append("SHOTGRID_URL")
        if not script_name:
            missing_vars.append("SHOTGRID_SCRIPT_NAME")
        if not script_key:
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
            "See the documentation for more details: https://github.com/loonghao/shotgrid-mcp-server#-mcp-client-configuration"
        )

        logger.error("Missing required environment variables for ShotGrid connection")
        logger.debug("SHOTGRID_URL: %s", url)
        logger.debug("SHOTGRID_SCRIPT_NAME: %s", script_name)
        logger.debug("SHOTGRID_SCRIPT_KEY: %s", script_key)
        raise ValueError(error_msg)

    # At this point, we know these values are not None
    assert url is not None
    assert script_name is not None
    assert script_key is not None

    return RealShotgunFactory(
        url=url,
        script_name=script_name,
        script_key=script_key,
        http_proxy=os.getenv("SHOTGUN_HTTP_PROXY"),
        ca_certs=os.getenv("SHOTGUN_API_CACERTS"),
    )


class ShotGridConnectionContext:
    """Context manager for safely handling ShotGrid connections."""

    def __init__(
        self,
        factory_or_connection: Optional[ShotgunClientFactory] = None,
    ) -> None:
        """Initialize the context manager.

        Args:
            factory_or_connection: Factory for creating ShotGrid clients or a direct Shotgun connection.
        """
        # If a direct connection is provided, use it
        if isinstance(factory_or_connection, Shotgun):
            self.factory = None
            self.connection = factory_or_connection
        else:
            # Otherwise, use the factory to create a connection
            self.factory = factory_or_connection or create_default_factory()
            try:
                self.connection = self.factory.create_client()
            except Exception as e:
                logger.error("Failed to create connection: %s", str(e), exc_info=True)
                self.connection = None

    def __enter__(self) -> Shotgun:
        """Create a new ShotGrid connection.

        Returns:
            Shotgun: A new ShotGrid connection.

        Raises:
            Exception: If connection creation fails.
        """
        try:
            self.connection = self.factory.create_client()
            return self.connection
        except Exception as e:
            logger.error("Failed to create connection: %s", str(e), exc_info=True)
            raise

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        """Clean up the connection."""
        # No need to return connection to pool, just set to None
        self.connection = None
