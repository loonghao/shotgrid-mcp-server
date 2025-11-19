"""Tests for HTTP context module."""

from unittest.mock import MagicMock, patch

import pytest

from shotgrid_mcp_server.http_context import (
    SHOTGRID_SCRIPT_KEY_HEADER,
    SHOTGRID_SCRIPT_NAME_HEADER,
    SHOTGRID_URL_HEADER,
    get_request_info,
    get_shotgrid_credentials_from_headers,
)


class TestGetShotGridCredentialsFromHeaders:
    """Test get_shotgrid_credentials_from_headers function."""

    def test_no_headers_available(self):
        """Test when no HTTP headers are available (stdio mode)."""
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=None):
            url, script_name, api_key = get_shotgrid_credentials_from_headers()
            assert url is None
            assert script_name is None
            assert api_key is None

    def test_all_headers_present(self):
        """Test when all ShotGrid headers are present."""
        mock_headers = {
            SHOTGRID_URL_HEADER: "https://test.shotgunstudio.com",
            SHOTGRID_SCRIPT_NAME_HEADER: "test_script",
            SHOTGRID_SCRIPT_KEY_HEADER: "test_key_12345",
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            url, script_name, api_key = get_shotgrid_credentials_from_headers()
            assert url == "https://test.shotgunstudio.com"
            assert script_name == "test_script"
            assert api_key == "test_key_12345"

    def test_lowercase_headers(self):
        """Test when headers are in lowercase."""
        mock_headers = {
            SHOTGRID_URL_HEADER.lower(): "https://test.shotgunstudio.com",
            SHOTGRID_SCRIPT_NAME_HEADER.lower(): "test_script",
            SHOTGRID_SCRIPT_KEY_HEADER.lower(): "test_key_12345",
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            url, script_name, api_key = get_shotgrid_credentials_from_headers()
            assert url == "https://test.shotgunstudio.com"
            assert script_name == "test_script"
            assert api_key == "test_key_12345"

    def test_partial_headers(self):
        """Test when only some headers are present."""
        mock_headers = {
            SHOTGRID_URL_HEADER: "https://test.shotgunstudio.com",
            # Missing script name and key
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            url, script_name, api_key = get_shotgrid_credentials_from_headers()
            assert url == "https://test.shotgunstudio.com"
            assert script_name is None
            assert api_key is None

    def test_empty_headers(self):
        """Test when headers dict is empty."""
        with patch("fastmcp.server.dependencies.get_http_headers", return_value={}):
            url, script_name, api_key = get_shotgrid_credentials_from_headers()
            assert url is None
            assert script_name is None
            assert api_key is None


class TestGetRequestInfo:
    """Test get_request_info function."""

    def test_no_headers_available(self):
        """Test when no HTTP headers are available."""
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=None):
            info = get_request_info()
            assert info == {}

    def test_all_request_info_present(self):
        """Test when all request info headers are present."""
        mock_headers = {
            "x-forwarded-for": "192.168.1.100",
            "user-agent": "TestClient/1.0",
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            info = get_request_info()
            assert info["forwarded_for"] == "192.168.1.100"
            assert info["user_agent"] == "TestClient/1.0"

    def test_partial_request_info(self):
        """Test when only some request info headers are present."""
        mock_headers = {
            "user-agent": "TestClient/1.0",
            # Missing X-Forwarded-For
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            info = get_request_info()
            assert "forwarded_for" not in info
            assert info["user_agent"] == "TestClient/1.0"

    def test_empty_headers(self):
        """Test when headers dict is empty."""
        with patch("fastmcp.server.dependencies.get_http_headers", return_value={}):
            info = get_request_info()
            assert info == {}


class TestHeaderConstants:
    """Test header constant values."""

    def test_header_constants(self):
        """Test that header constants are correctly defined."""
        assert SHOTGRID_URL_HEADER == "X-ShotGrid-URL"
        assert SHOTGRID_SCRIPT_NAME_HEADER == "X-ShotGrid-Script-Name"
        assert SHOTGRID_SCRIPT_KEY_HEADER == "X-ShotGrid-Script-Key"


class TestLogging:
    """Test logging behavior."""

    def test_logging_with_credentials(self):
        """Test that credentials are logged when present."""
        mock_headers = {
            SHOTGRID_URL_HEADER: "https://test.shotgunstudio.com",
            SHOTGRID_SCRIPT_NAME_HEADER: "test_script",
            SHOTGRID_SCRIPT_KEY_HEADER: "test_key",
            "User-Agent": "TestClient/1.0",
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            with patch("shotgrid_mcp_server.http_context.logger") as mock_logger:
                get_shotgrid_credentials_from_headers()
                # Should log info about the request
                assert mock_logger.info.called

    def test_logging_without_credentials(self):
        """Test logging when no credentials are present."""
        mock_headers = {
            "User-Agent": "TestClient/1.0",
        }
        with patch("fastmcp.server.dependencies.get_http_headers", return_value=mock_headers):
            with patch("shotgrid_mcp_server.http_context.logger") as mock_logger:
                get_shotgrid_credentials_from_headers()
                # Should log debug message
                assert mock_logger.debug.called

