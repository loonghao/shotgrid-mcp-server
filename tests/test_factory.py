"""Tests for ShotGrid factory functions."""

import os
import unittest
from unittest.mock import patch, MagicMock

import shotgun_api3

from shotgrid_mcp_server.connection_pool import (
    create_shotgun_connection,
    create_shotgun_connection_from_env,
)


class TestFactory(unittest.TestCase):
    """Test ShotGrid factory functions."""

    @patch("shotgrid_mcp_server.connection_pool.shotgun_api3.Shotgun")
    def test_create_shotgun_connection(self, mock_shotgun):
        """Test create_shotgun_connection function."""
        # Create a mock Shotgun instance
        mock_instance = MagicMock()
        mock_instance.config = MagicMock()
        mock_shotgun.return_value = mock_instance

        # Test with default args
        sg = create_shotgun_connection("https://test.shotgunstudio.com", "script_name", "api_key")

        # Verify Shotgun was called with correct args
        mock_shotgun.assert_called_once_with(
            base_url="https://test.shotgunstudio.com",
            script_name="script_name",
            api_key="api_key",
        )

        # Verify config was set correctly
        self.assertEqual(sg.config.max_rpc_attempts, 10)
        self.assertEqual(sg.config.timeout_secs, 30)
        self.assertEqual(sg.config.rpc_attempt_interval, 10000)

        # Reset mock
        mock_shotgun.reset_mock()

        # Test with custom args
        sg = create_shotgun_connection(
            "https://test.shotgunstudio.com",
            "script_name",
            "api_key",
            shotgun_args={
                "max_rpc_attempts": 20,
                "timeout_secs": 60,
                "rpc_attempt_interval": 20000,
                "connect": False,
            },
        )

        # Verify Shotgun was called with correct args
        mock_shotgun.assert_called_once_with(
            base_url="https://test.shotgunstudio.com",
            script_name="script_name",
            api_key="api_key",
            connect=False,
        )

        # Verify config was set correctly
        self.assertEqual(sg.config.max_rpc_attempts, 20)
        self.assertEqual(sg.config.timeout_secs, 60)
        self.assertEqual(sg.config.rpc_attempt_interval, 20000)

    @patch("shotgrid_mcp_server.connection_pool.create_shotgun_connection")
    @patch.dict(os.environ, {
        "SHOTGRID_URL": "https://test.shotgunstudio.com",
        "SHOTGRID_SCRIPT_NAME": "script_name",
        "SHOTGRID_SCRIPT_KEY": "api_key",
    })
    def test_create_shotgun_connection_from_env(self, mock_create_shotgun):
        """Test create_shotgun_connection_from_env function."""
        # Create a mock Shotgun instance
        mock_instance = MagicMock()
        mock_create_shotgun.return_value = mock_instance

        # Test with default args
        sg = create_shotgun_connection_from_env()

        # Verify create_shotgun_connection was called with correct args
        mock_create_shotgun.assert_called_once_with(
            url="https://test.shotgunstudio.com",
            script_name="script_name",
            api_key="api_key",
            shotgun_args=None,
        )

        # Reset mock
        mock_create_shotgun.reset_mock()

        # Test with custom args
        sg = create_shotgun_connection_from_env(
            shotgun_args={
                "max_rpc_attempts": 20,
                "timeout_secs": 60,
                "rpc_attempt_interval": 20000,
            },
        )

        # Verify create_shotgun_connection was called with correct args
        mock_create_shotgun.assert_called_once_with(
            url="https://test.shotgunstudio.com",
            script_name="script_name",
            api_key="api_key",
            shotgun_args={
                "max_rpc_attempts": 20,
                "timeout_secs": 60,
                "rpc_attempt_interval": 20000,
            },
        )

    @patch.dict(os.environ, {}, clear=True)
    def test_create_shotgun_connection_from_env_missing_vars(self):
        """Test create_shotgun_connection_from_env function with missing environment variables."""
        # Test with missing environment variables
        with self.assertRaises(ValueError) as context:
            create_shotgun_connection_from_env()

        # Verify error message
        self.assertIn("Missing required environment variables", str(context.exception))


if __name__ == "__main__":
    unittest.main()
