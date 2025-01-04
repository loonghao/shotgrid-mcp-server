"""ShotGrid connection pool module.

This module provides a thread-safe connection pool for ShotGrid API.
"""

# Import built-in modules
import logging
import os
import queue
import threading
from typing import Optional

# Import third-party modules
from shotgun_api3 import Shotgun
from shotgun_api3.lib.mockgun import Shotgun as MockgunShotgun

# Import local modules

# Configure logging
logger = logging.getLogger("mcp_shotgrid_server.connection_pool")


class ShotGridConnectionPool:
    """A thread-safe connection pool for ShotGrid API."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Create a singleton instance of the connection pool."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._pool_size = 5
                cls._instance._connection_queue = queue.Queue(maxsize=5)
                cls._instance._initialized = False
                logger.debug("Created new connection pool instance")
            return cls._instance

    def __init__(self):
        """Initialize the connection pool."""
        if not self._initialized:
            self._init_pool()
            self._initialized = True

    def _get_credentials(self) -> dict:
        """Get ShotGrid credentials from environment variables.

        Returns:
            dict: Dictionary containing ShotGrid credentials.

        Raises:
            ValueError: If required environment variables are missing.
        """
        url = os.getenv("SHOTGRID_URL")
        script_name = os.getenv("SCRIPT_NAME")
        script_key = os.getenv("SCRIPT_KEY")

        if not all([url, script_name, script_key]):
            logger.error("Missing required environment variables for ShotGrid connection")
            logger.debug("SHOTGRID_URL: %s", url)
            logger.debug("SCRIPT_NAME: %s", script_name)
            logger.debug("SCRIPT_KEY: %s", script_key)
            raise ValueError("Missing required environment variables for ShotGrid connection")

        return {
            "url": url,
            "script_name": script_name,
            "script_key": script_key,
        }

    def _create_connection(self) -> Shotgun:
        """Create a new ShotGrid connection.

        Returns:
            Shotgun: A new ShotGrid connection.

        Raises:
            Exception: If connection creation fails.
        """
        try:
            if os.getenv("TESTING"):
                # Set schema paths for mockgun
                schema_path = os.path.join(os.path.dirname(__file__), "../../tests", "schema", "schema.json")
                schema_entity_path = os.path.join(
                    os.path.dirname(__file__), "../../tests", "schema", "schema_entity.json"
                )
                MockgunShotgun.set_schema_paths(schema_path, schema_entity_path)
                sg = MockgunShotgun("https://test.shotgunstudio.com", script_name="test_script", api_key="test_key")
                logger.debug("Created mock ShotGrid connection")
            else:
                # Create real connection
                credentials = self._get_credentials()
                sg = Shotgun(
                    credentials["url"],
                    script_name=credentials["script_name"],
                    api_key=credentials["script_key"],
                    convert_datetimes_to_utc=True,
                    http_proxy=os.getenv("SHOTGUN_HTTP_PROXY"),
                    ca_certs=os.getenv("SHOTGUN_API_CACERTS"),
                )

                # Test connection
                sg.connect()
                logger.info("Successfully connected to ShotGrid at %s", credentials["url"])

            return sg

        except Exception as e:
            logger.error("Failed to create ShotGrid connection: %s", str(e), exc_info=True)
            raise

    def _init_pool(self):
        """Initialize the connection pool with connections."""
        try:
            for i in range(self._pool_size):
                connection = self._create_connection()
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

    def return_connection(self, connection: Shotgun):
        """Return a connection to the pool.

        Args:
            connection: The ShotGrid connection to return to the pool.
        """
        try:
            self._connection_queue.put(connection)
            logger.debug("Returned connection to pool (available: %d)", self._connection_queue.qsize())
        except Exception as e:
            logger.error("Failed to return connection to pool: %s", str(e))

    def close_all(self):
        """Close all connections in the pool."""
        closed = 0
        while not self._connection_queue.empty():
            try:
                connection = self._connection_queue.get_nowait()
                connection.close()
                closed += 1
                logger.debug("Closed connection %d", closed)
            except queue.Empty:
                break
            except Exception as e:
                logger.error("Error closing connection: %s", str(e))
        logger.info("Closed %d connections", closed)


class ShotGridConnectionContext:
    """Context manager for safely handling ShotGrid connections."""

    def __init__(self, pool: Optional[ShotGridConnectionPool] = None, timeout: Optional[float] = None):
        """Initialize the context manager.

        Args:
            pool: The connection pool to get connections from. If None, creates a new pool.
            timeout: How long to wait for a connection if none are available.
        """
        self.pool = pool if pool is not None else ShotGridConnectionPool()
        self.timeout = timeout
        self.connection = None

    def __enter__(self) -> Shotgun:
        """Get a connection from the pool.

        Returns:
            Shotgun: A ShotGrid connection from the pool.

        Raises:
            Exception: If connection acquisition fails.
        """
        try:
            self.connection = self.pool.get_connection(timeout=self.timeout)
            # Test connection before returning
            if not isinstance(self.connection, MockgunShotgun):
                try:
                    self.connection.connect()
                except Exception as e:
                    logger.error("Failed to connect to ShotGrid: %s", str(e))
                    self.pool.return_connection(self.connection)
                    raise
            logger.debug("Acquired connection from pool")
            return self.connection
        except Exception as e:
            logger.error("Failed to get connection from pool: %s", str(e), exc_info=True)
            if self.connection:
                self.pool.return_connection(self.connection)
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Return the connection to the pool."""
        if self.connection:
            try:
                self.pool.return_connection(self.connection)
                logger.debug("Released connection back to pool")
            except Exception as e:
                logger.error("Failed to return connection to pool: %s", str(e))
