"""Tests for CLI module."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from shotgrid_mcp_server.cli import cli, main


def test_cli_help() -> None:
    """CLI help describes the current dcc-gateway runtime."""

    result = CliRunner().invoke(cli, ["--help"])

    assert result.exit_code == 0
    assert "ShotGrid MCP Server" in result.output
    assert "--port" in result.output
    assert "dcc-gateway" in result.output


def test_cli_starts_shotgrid_server() -> None:
    """CLI creates a ShotGrid server and reports the MCP URL."""

    mock_server = MagicMock()
    mock_handle = MagicMock()
    mock_handle.mcp_url.return_value = "http://127.0.0.1:9000/mcp"
    mock_server.__enter__.return_value = mock_handle

    with patch("shotgrid_mcp_server.cli.create_shotgrid_server", return_value=mock_server) as create_server:
        with patch("time.sleep", side_effect=KeyboardInterrupt):
            result = CliRunner().invoke(cli, ["--port", "9000"])

    assert result.exit_code == 0
    create_server.assert_called_once_with(port=9000)
    assert "Server listening at http://127.0.0.1:9000/mcp" in result.output
    assert "Server stopped." in result.output


def test_cli_configuration_error() -> None:
    """Missing configuration is reported as a CLI error."""

    with patch("shotgrid_mcp_server.cli.create_shotgrid_server") as create_server:
        create_server.side_effect = ValueError("Missing required environment variables for ShotGrid connection")
        result = CliRunner().invoke(cli, [])

    assert result.exit_code == 1
    assert "Configuration Error" in result.output
    assert "Missing required environment variables" in result.output


def test_cli_generic_exception_aborts() -> None:
    """Unexpected startup errors abort the command."""

    with patch("shotgrid_mcp_server.cli.create_shotgrid_server") as create_server:
        create_server.side_effect = RuntimeError("Test error")
        result = CliRunner().invoke(cli, [])

    assert result.exit_code == 1
    assert "Error: Test error" in result.output


def test_main_function() -> None:
    """main delegates to click command."""

    with patch("shotgrid_mcp_server.cli.cli") as mock_cli:
        main()

    mock_cli.assert_called_once()
