"""Tests for utils module."""

import os
import tempfile
from pathlib import Path
from unittest import mock

from shotgrid_mcp_server.utils import (
    generate_default_file_path,
)


class TestGenerateDefaultFilePath:
    """Tests for generate_default_file_path function."""

    def test_generate_default_file_path_default_params(self):
        """Test generate_default_file_path with default parameters."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Call the function
                result = generate_default_file_path("Shot", 123)

                # Check the result
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                expected_file = expected_dir / "Shot_123_image.jpg"
                assert result == str(expected_file)

                # Verify the directory was created
                assert expected_dir.exists()

    def test_generate_default_file_path_custom_params(self):
        """Test generate_default_file_path with custom parameters."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Call the function with custom parameters
                result = generate_default_file_path(
                    entity_type="Asset",
                    entity_id=456,
                    field_name="custom_image",
                    image_format="png",
                )

                # Check the result
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                expected_file = expected_dir / "Asset_456_custom_image.png"
                assert result == str(expected_file)

                # Verify the directory was created
                assert expected_dir.exists()

    def test_generate_default_file_path_directory_creation(self):
        """Test that generate_default_file_path creates the directory if it doesn't exist."""
        # Mock expanduser to return a temporary directory
        with mock.patch("os.path.expanduser") as mock_expanduser:
            with tempfile.TemporaryDirectory() as temp_dir:
                mock_expanduser.return_value = temp_dir

                # Ensure the directory doesn't exist
                expected_dir = Path(temp_dir) / ".shotgrid_mcp" / "thumbnails"
                if expected_dir.exists():
                    os.rmdir(expected_dir)

                # Call the function
                generate_default_file_path("Version", 789)

                # Verify the directory was created
                assert expected_dir.exists()
