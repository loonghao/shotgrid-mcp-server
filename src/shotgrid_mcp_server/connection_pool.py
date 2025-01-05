"""ShotGrid connection pool module.

This module provides a thread-safe connection pool for ShotGrid API.
"""

# Import built-in modules
import logging
import os
import queue
import threading
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
        # Set schema paths before creating the instance
        MockgunExt.set_schema_paths(self.schema_path, self.schema_entity_path)
        sg = MockgunExt(
            "https://test.shotgunstudio.com",
            script_name="test_script",
            api_key="test_key",
        )
        logger.debug("Created mock ShotGrid connection")
        return sg


class ShotGridConnectionPool:
    """A thread-safe connection pool for ShotGrid API."""

    _instance: Optional["ShotGridConnectionPool"] = None
    _lock: threading.Lock = threading.Lock()
    _pool_size: int = 10
    _connection_queue: queue.Queue[Shotgun]
    _initialized: bool = False
    _factory: ShotgunClientFactory

    def __new__(
        cls: Type["ShotGridConnectionPool"], factory: Optional[ShotgunClientFactory] = None
    ) -> "ShotGridConnectionPool":
        """Create a singleton instance of the connection pool.

        Args:
            factory: Factory for creating ShotGrid clients

        Returns:
            ShotGridConnectionPool: The singleton instance.
        """
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._pool_size = 10
                cls._instance._connection_queue = queue.Queue(maxsize=10)
                cls._instance._initialized = False
                cls._instance._factory = factory or cls._create_default_factory()
                logger.debug("Created new connection pool instance")
            return cls._instance

    @staticmethod
    def _create_default_factory() -> ShotgunClientFactory:
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
            logger.error("Missing required environment variables for ShotGrid connection")
            logger.debug("SHOTGRID_URL: %s", url)
            logger.debug("SHOTGRID_SCRIPT_NAME: %s", script_name)
            logger.debug("SHOTGRID_SCRIPT_KEY: %s", script_key)
            raise ValueError("Missing required environment variables for ShotGrid connection")

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

    def __init__(self, factory: Optional[ShotgunClientFactory] = None) -> None:
        """Initialize the connection pool.

        Args:
            factory: Factory for creating ShotGrid clients
        """
        if factory:
            self._factory = factory
        if not self._initialized:
            self._init_pool()
            self._initialized = True

    def _init_pool(self) -> None:
        """Initialize the connection pool with connections."""
        try:
            for i in range(self._pool_size):
                connection = self._factory.create_client()
                self._connection_queue.put(connection)
                logger.debug("Added connection %d/%d to pool", i + 1, self._pool_size)
            logger.info("Successfully initialized connection pool with %d connections", self._pool_size)
        except Exception as e:
            logger.error("Failed to initialize connection pool: %s", str(e), exc_info=True)
            raise

    def get_connection(self, timeout: Optional[float] = None) -> Shotgun:
        """Get a connection from the pool.

        Args:
            timeout: How long to wait for a connection if none are available.
                    If None, wait indefinitely.

        Returns:
            Shotgun: A ShotGrid connection from the pool.

        Raises:
            queue.Empty: If no connection is available within the timeout period.
        """
        try:
            connection = self._connection_queue.get(timeout=timeout)
            logger.debug("Got connection from pool (available: %d)", self._connection_queue.qsize())
            return connection
        except queue.Empty:
            logger.error("Failed to get connection from pool: timeout after %s seconds", timeout)
            raise

    def return_connection(self, connection: Shotgun) -> None:
        """Return a connection to the pool.

        Args:
            connection: Connection to return to the pool.
        """
        try:
            self._connection_queue.put(connection)
            logger.debug("Returned connection to pool (available: %d)", self._connection_queue.qsize())
        except Exception as e:
            logger.error("Failed to return connection to pool: %s", str(e), exc_info=True)
            raise


class ShotGridConnectionContext:
    """Context manager for safely handling ShotGrid connections."""

    def __init__(
        self,
        pool: Optional[ShotGridConnectionPool] = None,
        factory: Optional[ShotgunClientFactory] = None,
        timeout: Optional[float] = None,
    ) -> None:
        """Initialize the context manager.

        Args:
            pool: The connection pool to get connections from. If None, creates a new pool.
            factory: Factory for creating ShotGrid clients. If provided, creates a new pool with this factory.
            timeout: How long to wait for a connection if none are available.
        """
        self.pool = pool if pool is not None else ShotGridConnectionPool(factory)
        self.timeout = timeout
        self.connection: Optional[Shotgun] = None

    def __enter__(self) -> Shotgun:
        """Get a connection from the pool.

        Returns:
            Shotgun: A ShotGrid connection from the pool.

        Raises:
            Exception: If connection acquisition fails.
        """
        try:
            self.connection = self.pool.get_connection(timeout=self.timeout)
            return self.connection
        except Exception as e:
            logger.error("Failed to acquire connection: %s", str(e), exc_info=True)
            raise

    def __exit__(
        self, exc_type: Optional[Type[BaseException]], exc_val: Optional[BaseException], exc_tb: Optional[Any]
    ) -> None:
        """Return the connection to the pool."""
        if self.connection:
            self.pool.return_connection(self.connection)
            self.connection = None
