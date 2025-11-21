"""Tests for CLI module."""

import sys
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from shotgrid_mcp_server.cli import cli, main


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def mock_create_server():
    """Mock create_server function."""
    with patch("shotgrid_mcp_server.cli.create_server") as mock:
        mock_app = MagicMock()
        mock.return_value = mock_app
        yield mock


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self, runner):
        """Test CLI help message."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ShotGrid MCP Server" in result.output
        assert "stdio" in result.output
        assert "http" in result.output

    def test_stdio_help(self, runner):
        """Test stdio command help."""
        result = runner.invoke(cli, ["stdio", "--help"])
        assert result.exit_code == 0
        assert "stdio transport" in result.output

    def test_http_help(self, runner):
        """Test http command help."""
        result = runner.invoke(cli, ["http", "--help"])
        assert result.exit_code == 0
        assert "HTTP transport" in result.output
        assert "--host" in result.output
        assert "--port" in result.output
        assert "--path" in result.output


class TestStdioCommand:
    """Test stdio command."""

    def test_stdio_command(self, runner, mock_create_server):
        """Test stdio command execution."""
        with patch.object(sys, "exit"):
            result = runner.invoke(cli, ["stdio"])
            # Should create server with lazy_connection=False
            mock_create_server.assert_called_once_with(lazy_connection=False)
            # Should run with stdio transport
            mock_create_server.return_value.run.assert_called_once_with(transport="stdio")

    def test_stdio_keyboard_interrupt(self, runner, mock_create_server):
        """Test stdio command handles KeyboardInterrupt."""
        mock_create_server.return_value.run.side_effect = KeyboardInterrupt()
        result = runner.invoke(cli, ["stdio"])
        assert "Shutting down server" in result.output

    def test_stdio_value_error(self, runner, mock_create_server):
        """Test stdio command handles ValueError."""
        mock_create_server.side_effect = ValueError("Missing required environment variables for ShotGrid connection")
        result = runner.invoke(cli, ["stdio"])
        assert result.exit_code == 1
        assert "ERROR: ShotGrid MCP Server Configuration Issue" in result.output

    def test_stdio_generic_exception(self, runner, mock_create_server):
        """Test stdio command handles generic exceptions."""
        mock_create_server.side_effect = RuntimeError("Test error")
        result = runner.invoke(cli, ["stdio"])
        assert result.exit_code == 1
        assert "Error: Test error" in result.output


class TestHttpCommand:
    """Test http command."""

    def test_http_command_defaults(self, runner, mock_create_server):
        """Test http command with default options."""
        with patch.object(sys, "exit"):
            result = runner.invoke(cli, ["http"])
            # Should create server with lazy_connection=True
            mock_create_server.assert_called_once_with(lazy_connection=True)
            # Should run with http transport and defaults
            mock_create_server.return_value.run.assert_called_once_with(
                transport="http", host="127.0.0.1", port=8000, path="/mcp"
            )

    def test_http_command_custom_options(self, runner, mock_create_server):
        """Test http command with custom options."""
        with patch.object(sys, "exit"):
            result = runner.invoke(cli, ["http", "--host", "0.0.0.0", "--port", "8080", "--path", "/api/mcp"])
            mock_create_server.return_value.run.assert_called_once_with(
                transport="http", host="0.0.0.0", port=8080, path="/api/mcp"
            )

    def test_http_keyboard_interrupt(self, runner, mock_create_server):
        """Test http command handles KeyboardInterrupt."""
        mock_create_server.return_value.run.side_effect = KeyboardInterrupt()
        result = runner.invoke(cli, ["http"])
        assert "Shutting down server" in result.output

    def test_http_generic_exception(self, runner, mock_create_server):
        """Test http command handles generic exceptions."""
        mock_create_server.side_effect = RuntimeError("Test error")
        result = runner.invoke(cli, ["http"])
        assert result.exit_code == 1
        assert "Error: Test error" in result.output


class TestMainFunction:
    """Test main entry point."""

    def test_main_function(self):
        """Test main function calls cli."""
        with patch("shotgrid_mcp_server.cli.cli") as mock_cli:
            main()
            mock_cli.assert_called_once()


class TestDefaultCommand:
    """Test default command behavior."""

    def test_no_subcommand_defaults_to_stdio(self, runner, mock_create_server):
        """Test that no subcommand defaults to stdio."""
        with patch.object(sys, "exit"):
            result = runner.invoke(cli, [])
            # Should create server with lazy_connection=False (stdio default)
            mock_create_server.assert_called_once_with(lazy_connection=False)
            # Should run with stdio transport
            mock_create_server.return_value.run.assert_called_once_with(transport="stdio")
