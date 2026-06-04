"""Tests for backward-compatible server entrypoints."""

from unittest.mock import MagicMock, patch

from shotgrid_mcp_server.server import create_server, main


def test_create_server_returns_dcc_server_when_lazy() -> None:
    """Lazy mode skips schema preload and returns the dcc-core server."""

    server = MagicMock()

    with patch("shotgrid_mcp_server.server.create_shotgrid_server", return_value=server) as factory:
        result = create_server(lazy_connection=True)

    assert result is server
    factory.assert_called_once_with(port=8000)


def test_create_server_preloads_schema_when_eager() -> None:
    """Eager compatibility path preloads schemas through the connection context."""

    server = MagicMock()
    connection = object()
    sg = MagicMock()
    preload_calls = []

    async def fake_preload_schemas(received_sg):
        preload_calls.append(received_sg)

    with patch("shotgrid_mcp_server.server.create_shotgrid_server", return_value=server):
        with patch("shotgrid_mcp_server.connection_pool.ShotGridConnectionContext") as context:
            with patch("shotgrid_mcp_server.schema_cache.preload_schemas", fake_preload_schemas):
                context.return_value.__enter__.return_value = sg

                result = create_server(connection=connection)

    assert result is server
    context.assert_called_once_with(factory_or_connection=connection)
    assert preload_calls == [sg]


def test_main_delegates_to_cli() -> None:
    """Server module main delegates to the Click entrypoint."""

    with patch("shotgrid_mcp_server.cli.main") as cli_main:
        main()

    cli_main.assert_called_once()
