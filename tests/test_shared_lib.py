"""Unit tests for shared_lib — framework-agnostic business logic."""

# Import built-in modules
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture
def mock_sg():
    """Create a mock ShotGrid connection."""
    sg = MagicMock()
    sg.find.return_value = [{"type": "Shot", "id": 1, "code": "SH001"}]
    sg.find_one.return_value = {"type": "Shot", "id": 1, "code": "SH001"}
    sg.create.return_value = {"type": "Shot", "id": 2, "code": "SH002"}
    sg.update.return_value = {"type": "Shot", "id": 1, "code": "SH001_UPDATED"}
    sg.delete.return_value = True
    sg.schema_field_read.return_value = {"code": {"data_type": {"value": "text"}}}
    sg.schema_entity_read.return_value = {"Shot": {}, "Asset": {}, "Task": {}}
    sg.batch.return_value = [{"type": "Shot", "id": 3}]
    sg.revive.return_value = True
    sg.summarize.return_value = {"groups": [{"value": "ip", "count": 5}]}
    return sg


class TestCRUDFunctions:
    """Test CRUD operations from shared_lib."""

    def test_create_entity(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import create_entity_record

        result = create_entity_record(mock_sg, "Shot", {"code": "SH002"})
        assert result is not None
        mock_sg.create.assert_called_once()

    def test_read_entity(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import read_entity_record

        result = read_entity_record(mock_sg, "Shot", 1)
        assert result is not None
        mock_sg.find_one.assert_called_once()

    def test_read_entity_not_found(self, mock_sg):
        from shotgrid_mcp_server.exceptions import EntityNotFoundError
        from shotgrid_mcp_server.shared_lib import read_entity_record

        mock_sg.find_one.return_value = None
        with pytest.raises(EntityNotFoundError):
            read_entity_record(mock_sg, "Shot", 999)

    def test_update_entity(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import update_entity_record

        result = update_entity_record(mock_sg, "Shot", 1, {"code": "UPDATED"})
        assert result is not None
        mock_sg.update.assert_called_once()

    def test_delete_entity(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import delete_entity_record

        result = delete_entity_record(mock_sg, "Shot", 1)
        assert result is True


class TestSchemaFunctions:
    """Test schema functions."""

    def test_get_entity_schema(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import get_entity_schema

        result = get_entity_schema(mock_sg, "Shot")
        assert result is not None
        assert "entity_type" in result

    def test_get_all_entity_types(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import get_all_entity_types

        result = get_all_entity_types(mock_sg)
        assert "Shot" in result

    def test_get_field_schema(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import get_field_schema

        result = get_field_schema(mock_sg, "Shot", "code")
        assert result is not None


class TestSearchFunctions:
    """Test search functions."""

    def test_execute_search(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import execute_search

        result = execute_search(mock_sg, "Shot", filters=[["code", "is", "SH001"]])
        assert isinstance(result, list)

    def test_execute_find_one(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import execute_find_one

        result = execute_find_one(mock_sg, "Shot", [["id", "is", 1]])
        assert result is not None

    def test_execute_find_one_none(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import execute_find_one

        mock_sg.find_one.return_value = None
        result = execute_find_one(mock_sg, "Shot", [["id", "is", 999]])
        assert result is None


class TestNoteFunctions:
    """Test note operations."""

    def test_create_note(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import create_note

        mock_sg.create.return_value = {"type": "Note", "id": 10, "subject": "Test"}
        result = create_note(mock_sg, "Shot", 1, "Test Subject", "Test content")
        assert result is not None

    def test_get_entity_notes(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import get_entity_notes

        mock_sg.find.return_value = [{"type": "Note", "id": 10}]
        result = get_entity_notes(mock_sg, "Shot", 1)
        assert isinstance(result, list)


class TestLowLevelAPI:
    """Test low-level API functions."""

    def test_sg_find(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_find

        result = sg_find(mock_sg, "Shot", [])
        assert isinstance(result, list)

    def test_sg_find_one(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_find_one

        result = sg_find_one(mock_sg, "Shot", [["id", "is", 1]])
        assert result is not None

    def test_sg_text_search(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_text_search

        mock_sg.text_search.return_value = [{"type": "Shot", "id": 1}]
        result = sg_text_search(mock_sg, "hero", ["Shot"])
        assert isinstance(result, list)

    def test_sg_revive(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_revive

        result = sg_revive(mock_sg, "Shot", 1)
        assert result is True

    def test_sg_summarize(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_summarize

        result = sg_summarize(mock_sg, "Shot", [], "sg_status_list")
        assert result is not None
        assert "groups" in result


class TestUserProjectHelpers:
    """Test user and project helper functions."""

    def test_find_active_projects(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import find_active_projects

        mock_sg.find.return_value = [{"type": "Project", "id": 1, "name": "Demo"}]
        result = find_active_projects(mock_sg, days=90)
        assert isinstance(result, list)

    def test_find_active_users(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import find_active_users

        mock_sg.find.return_value = [{"type": "HumanUser", "id": 1, "name": "test"}]
        result = find_active_users(mock_sg, days=30)
        assert isinstance(result, list)


class TestAliases:
    """Test that all alias functions work."""

    @pytest.mark.parametrize(
        "alias_name",
        [
            "create_sg_entity",
            "delete_sg_entity",
            "update_sg_entity",
            "read_sg_entity",
            "get_sg_entity_schema",
            "create_sg_note",
            "read_sg_notes",
            "update_sg_note",
            "find_one_sg_entity",
            "search_sg_entities",
            "find_active_sg_projects",
            "find_active_sg_users",
            "find_sg_entities_by_date",
        ],
    )
    def test_alias_exists(self, alias_name):
        """Each skill script alias exists in shared_lib."""
        from shotgrid_mcp_server import shared_lib as sl

        assert hasattr(sl, alias_name), f"Missing alias: {alias_name}"
        assert callable(getattr(sl, alias_name))
