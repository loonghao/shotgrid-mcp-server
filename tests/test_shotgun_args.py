"""Tests for ShotGrid arguments handling functions."""

import unittest

from shotgrid_mcp_server.connection_pool import (
    _get_value_from_shotgun_args,
    _ignore_shotgun_args,
    get_shotgun_connection_args,
)


class TestShotgunArgs(unittest.TestCase):
    """Test ShotGrid arguments handling."""

    def test_get_value_from_shotgun_args(self):
        """Test _get_value_from_shotgun_args function."""
        # Test with empty args
        self.assertEqual(_get_value_from_shotgun_args({}, "key", "default"), "default")

        # Test with None args
        self.assertEqual(_get_value_from_shotgun_args(None, "key", "default"), "default")

        # Test with key not in args
        self.assertEqual(_get_value_from_shotgun_args({"other_key": "value"}, "key", "default"), "default")

        # Test with key in args but value is None
        self.assertEqual(_get_value_from_shotgun_args({"key": None}, "key", "default"), "default")

        # Test with key in args and value is not None
        self.assertEqual(_get_value_from_shotgun_args({"key": "value"}, "key", "default"), "value")

    def test_ignore_shotgun_args(self):
        """Test _ignore_shotgun_args function."""
        # Test with empty args
        self.assertEqual(_ignore_shotgun_args({}), {})

        # Test with None args
        self.assertEqual(_ignore_shotgun_args(None), {})

        # Test with ShotGrid-specific args
        args = {
            "max_rpc_attempts": 10,
            "timeout_secs": 30,
            "rpc_attempt_interval": 10000,
            "other_key": "value",
        }
        expected = {"other_key": "value"}
        self.assertEqual(_ignore_shotgun_args(args), expected)

        # Test with no ShotGrid-specific args
        args = {"other_key": "value"}
        self.assertEqual(_ignore_shotgun_args(args), args)

    def test_get_shotgun_connection_args(self):
        """Test get_shotgun_connection_args function."""
        # Test with empty args
        args = get_shotgun_connection_args({})
        self.assertEqual(args["max_rpc_attempts"], 10)
        self.assertEqual(args["timeout_secs"], 30)
        self.assertEqual(args["rpc_attempt_interval"], 10000)

        # Test with custom args
        args = get_shotgun_connection_args({
            "max_rpc_attempts": 20,
            "timeout_secs": 60,
            "rpc_attempt_interval": 20000,
        })
        self.assertEqual(args["max_rpc_attempts"], 20)
        self.assertEqual(args["timeout_secs"], 60)
        self.assertEqual(args["rpc_attempt_interval"], 20000)

        # Test with None args
        args = get_shotgun_connection_args(None)
        self.assertEqual(args["max_rpc_attempts"], 10)
        self.assertEqual(args["timeout_secs"], 30)
        self.assertEqual(args["rpc_attempt_interval"], 10000)


if __name__ == "__main__":
    unittest.main()
