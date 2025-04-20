"""Tests for error_handler module."""

import re
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError
from shotgun_api3 import ShotgunError

from shotgrid_mcp_server.error_handler import (
    create_error_response,
    format_error_message,
    handle_tool_error,
    is_entity_not_found_error,
    is_permission_error,
)
from shotgrid_mcp_server.exceptions import (
    ConnectionError,
    EntityNotFoundError,
    FilterError,
    PermissionError,
    SerializationError,
)


class TestFormatErrorMessage:
    """Tests for format_error_message function."""

    def test_remove_thumbnail_url_prefix(self):
        """Test removing thumbnail URL prefix."""
        error_msg = "Error getting thumbnail URL: No thumbnail found"
        result = format_error_message(error_msg)
        assert result == "No thumbnail found"

    def test_remove_thumbnail_download_prefix(self):
        """Test removing thumbnail download prefix."""
        error_msg = "Error downloading thumbnail: Connection failed"
        result = format_error_message(error_msg)
        assert result == "Connection failed"

    def test_remove_executing_tool_prefix(self):
        """Test removing executing tool prefix."""
        error_msg = "Error executing tool get_entity: Entity not found"
        result = format_error_message(error_msg)
        assert result == "Entity not found"

    def test_standardize_id_terminology(self):
        """Test standardizing ID terminology."""
        error_msg = "Entity Shot with id 123 not found"
        result = format_error_message(error_msg)
        assert result == "Entity Shot with ID 123 not found"

    def test_standardize_no_image_message(self):
        """Test standardizing no image message."""
        error_msg = "Entity has no image"
        result = format_error_message(error_msg)
        assert result == "No thumbnail URL found"

    def test_no_changes_needed(self):
        """Test when no changes are needed."""
        error_msg = "Generic error message"
        result = format_error_message(error_msg)
        assert result == "Generic error message"


class TestHandleToolError:
    """Tests for handle_tool_error function."""

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_entity_not_found_error(self, mock_logger):
        """Test handling entity not found error."""
        error = ShotgunError("Entity Shot with id 123 not found")
        with pytest.raises(EntityNotFoundError) as excinfo:
            handle_tool_error(error, "find_entity")
        
        assert excinfo.value.entity_type == "shot"
        assert excinfo.value.entity_id == 123
        assert "Entity Shot with ID 123 not found" in str(excinfo.value)
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_permission_error(self, mock_logger):
        """Test handling permission error."""
        error = ShotgunError("User does not have permission to access this entity")
        with pytest.raises(PermissionError) as excinfo:
            handle_tool_error(error, "update_entity")
        
        assert "User does not have permission to access this entity" in str(excinfo.value)
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_connection_error(self, mock_logger):
        """Test handling connection error."""
        error = ShotgunError("Connection timeout while accessing ShotGrid")
        with pytest.raises(ConnectionError) as excinfo:
            handle_tool_error(error, "connect_to_shotgrid")
        
        assert "Connection timeout while accessing ShotGrid" in str(excinfo.value)
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_filter_error(self, mock_logger):
        """Test handling filter error."""
        error = ValueError("Invalid filter format")
        with pytest.raises(FilterError) as excinfo:
            handle_tool_error(error, "search_entities")
        
        assert "Invalid filter format" in str(excinfo.value)
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_serialization_error(self, mock_logger):
        """Test handling serialization error."""
        error = ValueError("Failed to serialize JSON data")
        with pytest.raises(SerializationError) as excinfo:
            handle_tool_error(error, "create_entity")
        
        assert "Failed to serialize JSON data" in str(excinfo.value)
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_generic_error(self, mock_logger):
        """Test handling generic error."""
        error = ValueError("Unknown error")
        with pytest.raises(ToolError) as excinfo:
            handle_tool_error(error, "generic_operation")
        
        assert "Error executing tool generic_operation: Unknown error" in str(excinfo.value)
        mock_logger.error.assert_called_once()


class TestCreateErrorResponse:
    """Tests for create_error_response function."""

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_entity_not_found_error(self, mock_logger):
        """Test creating response for entity not found error."""
        error = EntityNotFoundError(entity_type="Shot", entity_id=123, message="Entity not found")
        response = create_error_response(error, "find_entity")
        
        assert response["error"] == "Error executing find_entity: Entity not found"
        assert response["error_type"] == "EntityNotFoundError"
        assert response["error_category"] == "not_found"
        assert response["operation"] == "find_entity"
        assert "timestamp" in response
        assert response["entity_type"] == "Shot"
        assert response["entity_id"] == 123
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_permission_error(self, mock_logger):
        """Test creating response for permission error."""
        error = PermissionError("Permission denied")
        response = create_error_response(error, "update_entity")
        
        assert response["error"] == "Error executing update_entity: Permission denied"
        assert response["error_type"] == "PermissionError"
        assert response["error_category"] == "permission"
        assert response["operation"] == "update_entity"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_filter_error(self, mock_logger):
        """Test creating response for filter error."""
        error = FilterError("Invalid filter")
        response = create_error_response(error, "search_entities")
        
        assert response["error"] == "Error executing search_entities: Invalid filter"
        assert response["error_type"] == "FilterError"
        assert response["error_category"] == "filter"
        assert response["operation"] == "search_entities"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_serialization_error(self, mock_logger):
        """Test creating response for serialization error."""
        error = SerializationError("JSON serialization failed")
        response = create_error_response(error, "create_entity")
        
        assert response["error"] == "Error executing create_entity: JSON serialization failed"
        assert response["error_type"] == "SerializationError"
        assert response["error_category"] == "serialization"
        assert response["operation"] == "create_entity"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_connection_error(self, mock_logger):
        """Test creating response for connection error."""
        error = ConnectionError("Connection failed")
        response = create_error_response(error, "connect_to_shotgrid")
        
        assert response["error"] == "Error executing connect_to_shotgrid: Connection failed"
        assert response["error_type"] == "ConnectionError"
        assert response["error_category"] == "connection"
        assert response["operation"] == "connect_to_shotgrid"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_shotgun_error(self, mock_logger):
        """Test creating response for ShotgunError."""
        error = ShotgunError("ShotGrid API error")
        response = create_error_response(error, "shotgrid_operation")
        
        assert response["error"] == "Error executing shotgrid_operation: ShotGrid API error"
        assert response["error_type"] == "ShotgunError"
        assert response["error_category"] == "shotgrid"
        assert response["operation"] == "shotgrid_operation"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_unknown_error(self, mock_logger):
        """Test creating response for unknown error."""
        error = ValueError("Unknown error")
        response = create_error_response(error, "generic_operation")
        
        assert response["error"] == "Error executing generic_operation: Unknown error"
        assert response["error_type"] == "ValueError"
        assert response["error_category"] == "unknown"
        assert response["operation"] == "generic_operation"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()

    @patch("shotgrid_mcp_server.error_handler.logger")
    def test_custom_error_type(self, mock_logger):
        """Test creating response with custom error type."""
        error = ValueError("Custom error")
        response = create_error_response(error, "custom_operation", error_type=RuntimeError)
        
        assert response["error"] == "Error executing custom_operation: Custom error"
        assert response["error_type"] == "RuntimeError"
        assert response["operation"] == "custom_operation"
        assert "timestamp" in response
        mock_logger.error.assert_called_once()


class TestIsEntityNotFoundError:
    """Tests for is_entity_not_found_error function."""

    def test_shotgun_not_found_error(self):
        """Test with ShotgunError containing 'not found'."""
        error = ShotgunError("Entity not found")
        assert is_entity_not_found_error(error) is True

    def test_shotgun_does_not_exist_error(self):
        """Test with ShotgunError containing 'does not exist'."""
        error = ShotgunError("Entity does not exist")
        assert is_entity_not_found_error(error) is True

    def test_shotgun_other_error(self):
        """Test with ShotgunError not related to entity not found."""
        error = ShotgunError("Other error")
        assert is_entity_not_found_error(error) is False

    def test_non_shotgun_error(self):
        """Test with non-ShotgunError."""
        error = ValueError("Entity not found")
        assert is_entity_not_found_error(error) is False


class TestIsPermissionError:
    """Tests for is_permission_error function."""

    def test_shotgun_permission_error(self):
        """Test with ShotgunError containing 'permission'."""
        error = ShotgunError("Permission denied")
        assert is_permission_error(error) is True

    def test_shotgun_access_error(self):
        """Test with ShotgunError containing 'access'."""
        error = ShotgunError("Access denied")
        assert is_permission_error(error) is True

    def test_shotgun_not_allowed_error(self):
        """Test with ShotgunError containing 'not allowed'."""
        error = ShotgunError("Operation not allowed")
        assert is_permission_error(error) is True

    def test_shotgun_other_error(self):
        """Test with ShotgunError not related to permission."""
        error = ShotgunError("Other error")
        assert is_permission_error(error) is False

    def test_non_shotgun_error(self):
        """Test with non-ShotgunError."""
        error = ValueError("Permission denied")
        assert is_permission_error(error) is False
