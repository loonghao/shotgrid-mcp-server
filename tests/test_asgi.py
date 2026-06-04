"""Tests for ASGI application."""

# Import built-in modules
import asyncio
import json
import os
from types import SimpleNamespace
from unittest.mock import patch

# Import third-party modules
import pytest
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Import local modules
from shotgrid_mcp_server.asgi import _health, _mcp_not_available, create_asgi_app


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        "SHOTGRID_URL": "https://test.shotgunstudio.com",
        "SHOTGRID_SCRIPT_NAME": "test_script",
        "SHOTGRID_SCRIPT_KEY": "test_key",
    }
    with patch.dict(os.environ, env_vars):
        yield env_vars


def test_create_asgi_app_default(mock_env_vars):
    """Test creating ASGI app with default settings."""
    app = create_asgi_app()
    assert app is not None


def test_create_asgi_app_with_custom_path(mock_env_vars):
    """Test creating ASGI app with custom path."""
    custom_path = "/api/shotgrid"
    app = create_asgi_app(path=custom_path)
    assert app is not None
    assert app.state.mcp_path == custom_path


def test_asgi_compatibility_routes_report_runtime_path(mock_env_vars):
    """Test compatibility routes return clear runtime information."""
    app = create_asgi_app(path="api/shotgrid")
    request = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(mcp_path=app.state.mcp_path)))

    health = asyncio.run(_health(request))
    assert health.status_code == 200
    assert json.loads(health.body)["runtime"] == "dcc-mcp-core"

    mcp_response = asyncio.run(_mcp_not_available(request))
    assert mcp_response.status_code == 503
    payload = json.loads(mcp_response.body)
    assert payload["error"] == "asgi_mcp_not_available"
    assert payload["mcp_path"] == "/api/shotgrid"


def test_create_asgi_app_with_middleware(mock_env_vars):
    """Test creating ASGI app with custom middleware."""
    cors_middleware = Middleware(
        CORSMiddleware,
        allow_origins=["https://example.com"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    app = create_asgi_app(middleware=[cors_middleware])
    assert app is not None


def test_create_asgi_app_with_multiple_middleware(mock_env_vars):
    """Test creating ASGI app with multiple middleware."""
    from starlette.middleware.gzip import GZipMiddleware

    middleware_list = [
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
        Middleware(GZipMiddleware, minimum_size=1000),
    ]

    app = create_asgi_app(middleware=middleware_list)
    assert app is not None


def test_create_asgi_app_lazy_initialization(mock_env_vars):
    """Test that the module-level app uses lazy initialization."""
    # Import the module
    from shotgrid_mcp_server import asgi

    # The app should be a function (lazy init), not an instance
    assert callable(asgi.app)

    # Calling get_app() should create the instance
    app_instance = asgi.get_app()
    assert app_instance is not None

    # Calling again should return the same instance (singleton)
    app_instance2 = asgi.get_app()
    assert app_instance is app_instance2
