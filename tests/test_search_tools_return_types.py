"""Test search tools return types."""
import pytest
from unittest.mock import MagicMock, patch
from shotgrid_mcp_server.models import ProjectsResponse, UsersResponse, EntitiesResponse


class TestSearchToolsReturnTypes:
    """Test that search tools return correct types."""

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_recently_active_projects_return_type(self, mock_sg_class):
        """Test find_recently_active_projects returns ProjectsResponse."""
        from shotgrid_mcp_server.tools.search_tools import _find_recently_active_projects
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = [
            {"id": 1, "type": "Project", "name": "Test Project", "updated_at": "2025-01-01"}
        ]
        
        # Call function
        result = _find_recently_active_projects(mock_sg, days=90)
        
        # Verify return type
        assert isinstance(result, ProjectsResponse)
        assert hasattr(result, 'projects')
        assert isinstance(result.projects, list)

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_active_users_return_type(self, mock_sg_class):
        """Test find_active_users returns UsersResponse."""
        from shotgrid_mcp_server.tools.search_tools import _find_active_users
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = [
            {"id": 1, "type": "HumanUser", "name": "Test User", "login": "testuser"}
        ]
        
        # Call function
        result = _find_active_users(mock_sg, days=30)
        
        # Verify return type
        assert isinstance(result, UsersResponse)
        assert hasattr(result, 'users')
        assert isinstance(result.users, list)

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_entities_by_date_range_return_type(self, mock_sg_class):
        """Test find_entities_by_date_range returns EntitiesResponse."""
        from shotgrid_mcp_server.tools.search_tools import _find_entities_by_date_range
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = [
            {"id": 1, "type": "Shot", "code": "SH001", "created_at": "2025-01-01"}
        ]
        
        # Call function
        result = _find_entities_by_date_range(
            mock_sg,
            entity_type="Shot",
            date_field="created_at",
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        # Verify return type
        assert isinstance(result, EntitiesResponse)
        assert hasattr(result, 'entities')
        assert isinstance(result.entities, list)

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_recently_active_projects_empty_result(self, mock_sg_class):
        """Test find_recently_active_projects with empty result."""
        from shotgrid_mcp_server.tools.search_tools import _find_recently_active_projects
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = []
        
        # Call function
        result = _find_recently_active_projects(mock_sg, days=90)
        
        # Verify return type and empty list
        assert isinstance(result, ProjectsResponse)
        assert result.projects == []

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_active_users_empty_result(self, mock_sg_class):
        """Test find_active_users with empty result."""
        from shotgrid_mcp_server.tools.search_tools import _find_active_users
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = []
        
        # Call function
        result = _find_active_users(mock_sg, days=30)
        
        # Verify return type and empty list
        assert isinstance(result, UsersResponse)
        assert result.users == []

    @patch('shotgrid_mcp_server.tools.search_tools.Shotgun')
    def test_find_entities_by_date_range_empty_result(self, mock_sg_class):
        """Test find_entities_by_date_range with empty result."""
        from shotgrid_mcp_server.tools.search_tools import _find_entities_by_date_range
        
        # Mock ShotGrid connection
        mock_sg = MagicMock()
        mock_sg.find.return_value = []
        
        # Call function
        result = _find_entities_by_date_range(
            mock_sg,
            entity_type="Version",
            date_field="created_at",
            start_date="2025-01-01",
            end_date="2025-01-31"
        )
        
        # Verify return type and empty list
        assert isinstance(result, EntitiesResponse)
        assert result.entities == []

