"""Tests for ASGI application."""

# Import built-in modules
import os
from unittest.mock import MagicMock, patch

# Import third-party modules
import pytest
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

# Import local modules
from shotgrid_mcp_server.asgi import create_asgi_app


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


def test_create_asgi_app_imports():
    """Test that the default app is created on module import."""
    # Import here to test module-level initialization
    from shotgrid_mcp_server import asgi

    assert asgi.app is not None
