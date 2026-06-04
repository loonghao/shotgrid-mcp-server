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

    def test_execute_find_with_related_expands_dot_fields(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import execute_find_with_related

        mock_sg.schema_field_read.return_value = {"properties": {"valid_types": {"value": ["Asset"]}}}
        mock_sg.find.return_value = [{"type": "Shot", "id": 1, "assets.Asset.code": "Hero"}]

        result = execute_find_with_related(
            mock_sg,
            "Shot",
            filters=[["id", "is", 1]],
            fields=["code"],
            related_fields={"assets": ["code", "sg_asset_type"]},
            limit=5,
        )

        assert result[0]["id"] == 1
        _, _, find_kwargs = mock_sg.find.mock_calls[-1]
        assert find_kwargs["fields"] == ["code", "assets.Asset.code", "assets.Asset.sg_asset_type"]
        assert find_kwargs["limit"] == 5

    def test_sg_search_advanced_combines_time_and_related_filters(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import sg_search_advanced

        mock_sg.schema_field_read.return_value = {"properties": {"valid_types": {"value": ["Task"]}}}
        mock_sg.find.return_value = [{"type": "Version", "id": 12, "code": "v001"}]

        result = sg_search_advanced(
            mock_sg,
            "Version",
            filters=[["sg_status_list", "is", "rev"]],
            time_filters=[{"field": "created_at", "operator": "in_last", "count": 7, "unit": "DAY"}],
            fields=["code"],
            related_fields={"sg_task": ["content"]},
            order=[{"field_name": "created_at", "direction": "desc"}],
            limit=10,
        )

        assert result == [{"type": "Version", "id": 12, "code": "v001"}]
        _, _, find_kwargs = mock_sg.find.mock_calls[-1]
        assert find_kwargs["fields"] == ["code", "sg_task.Task.content"]
        assert find_kwargs["limit"] == 10


class TestBatchFunctions:
    """Test batch operations."""

    def test_batch_create_update_delete(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import batch_create, batch_delete, batch_update

        mock_sg.batch.side_effect = [
            [{"type": "Shot", "id": 3, "code": "SH003"}],
            [{"type": "Shot", "id": 3, "code": "SH003B"}],
            [True, False],
        ]

        created = batch_create(mock_sg, "Shot", [{"code": "SH003"}])
        updated = batch_update(mock_sg, "Shot", [{"id": 3, "code": "SH003B"}])
        deleted = batch_delete(mock_sg, "Shot", [3, 4])

        assert created[0]["code"] == "SH003"
        assert updated[0]["code"] == "SH003B"
        assert deleted == [True, False]
        create_request = mock_sg.batch.mock_calls[0].args[0][0]
        update_request = mock_sg.batch.mock_calls[1].args[0][0]
        delete_request = mock_sg.batch.mock_calls[2].args[0][0]
        assert create_request == {"request_type": "create", "entity_type": "Shot", "data": {"code": "SH003"}}
        assert update_request["entity_id"] == 3
        assert update_request["data"] == {"code": "SH003B"}
        assert delete_request == {"request_type": "delete", "entity_type": "Shot", "entity_id": 3}


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

    def test_update_note(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import update_note

        mock_sg.update.return_value = {"type": "Note", "id": 10, "content": "Updated"}
        result = update_note(mock_sg, 10, {"content": "Updated"})

        assert result["content"] == "Updated"
        mock_sg.update.assert_called_with("Note", 10, {"content": "Updated"})


class TestMediaFunctions:
    """Test media operations."""

    def test_thumbnail_download_and_upload(self, mock_sg, tmp_path):
        from shotgrid_mcp_server.shared_lib import download_thumbnail, upload_thumbnail

        output_path = tmp_path / "thumb.png"
        downloaded = download_thumbnail(mock_sg, "Shot", 1, output_path=str(output_path))

        assert downloaded == {
            "status": "downloaded",
            "path": str(output_path),
            "entity_type": "Shot",
            "entity_id": 1,
        }
        mock_sg.download_attachment.assert_called_with(
            {"type": "Shot", "id": 1},
            attachment_field_name="image",
            file_path=str(output_path),
        )

        mock_sg.upload.return_value = {"type": "Attachment", "id": 99}
        uploaded = upload_thumbnail(mock_sg, "Shot", 1, "image", str(output_path))

        assert uploaded["status"] == "uploaded"
        assert uploaded["result"]["id"] == 99
        mock_sg.upload.assert_called_with("Shot", 1, str(output_path), field_name="image")

    def test_batch_download_thumbnails_records_success_and_errors(self, mock_sg, tmp_path):
        from shotgrid_mcp_server.shared_lib import batch_download_thumbnails

        mock_sg.download_attachment.side_effect = [None, RuntimeError("missing image")]

        results = batch_download_thumbnails(mock_sg, "Shot", [1, 2], output_dir=str(tmp_path))

        assert results[0]["status"] == "downloaded"
        assert results[0]["path"].endswith("Shot_1.png")
        assert results[1]["status"] == "error"
        assert "missing image" in results[1]["error"]


class TestPlaylistFunctions:
    """Test playlist operations."""

    def test_playlist_lifecycle_operations(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import (
            add_versions_to_playlist,
            create_playlist,
            find_playlists,
            remove_versions_from_playlist,
        )

        mock_sg.create.return_value = {"type": "Playlist", "id": 5, "code": "Daily"}
        created = create_playlist(mock_sg, "Daily", 2, description="Review", version_ids=[10, 11])

        assert created["id"] == 5
        create_data = mock_sg.create.call_args.args[1]
        assert create_data["project"] == {"type": "Project", "id": 2}
        assert create_data["versions"] == [{"type": "Version", "id": 10}, {"type": "Version", "id": 11}]

        mock_sg.find.return_value = [{"type": "Playlist", "id": 5, "code": "Daily"}]
        found = find_playlists(mock_sg, project_id=2, name_contains="Dai")

        assert found[0]["code"] == "Daily"
        find_args = mock_sg.find.call_args.args
        assert find_args[0] == "Playlist"
        assert ["project", "is", {"type": "Project", "id": 2}] in find_args[1]
        assert ["code", "contains", "Dai"] in find_args[1]

        mock_sg.update.return_value = {"type": "Playlist", "id": 5}
        added = add_versions_to_playlist(mock_sg, 5, [12])
        removed = remove_versions_from_playlist(mock_sg, 5, [10])

        assert added["id"] == 5
        assert removed["id"] == 5
        add_payload = mock_sg.update.mock_calls[-2].args[2]
        remove_payload = mock_sg.update.mock_calls[-1].args[2]
        assert add_payload["update_mode"] == "multi_entity_update_mode_add"
        assert remove_payload["update_mode"] == "multi_entity_update_mode_remove"


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

    def test_low_level_batch_schema_upload_and_download(self, mock_sg, tmp_path):
        from shotgrid_mcp_server.shared_lib import (
            sg_batch,
            sg_download_attachment,
            sg_schema_entity_read,
            sg_schema_field_read,
            sg_upload,
        )

        mock_sg.batch.return_value = [{"type": "Shot", "id": 7}]
        assert sg_batch(mock_sg, [{"request_type": "create"}])[0]["id"] == 7
        assert "Shot" in sg_schema_entity_read(mock_sg)
        assert sg_schema_field_read(mock_sg, "Shot", "code") == {"code": {"data_type": {"value": "text"}}}

        file_path = tmp_path / "upload.mov"
        mock_sg.upload.return_value = 44
        assert sg_upload(mock_sg, "Version", 3, "sg_uploaded_movie", str(file_path)) == {
            "status": "uploaded",
            "id": 44,
        }

        output_path = tmp_path / "download.mov"
        assert sg_download_attachment(mock_sg, 55, str(output_path)) == {
            "status": "downloaded",
            "attachment_id": 55,
            "path": str(output_path),
        }


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

    def test_find_entities_by_date_range(self, mock_sg):
        from shotgrid_query import FilterModel

        from shotgrid_mcp_server.shared_lib import find_entities_by_date_range

        status_filter = FilterModel(field="sg_status_list", operator="is", value="ip")
        mock_sg.find.return_value = [{"type": "Shot", "id": 1, "code": "SH001"}]

        result = find_entities_by_date_range(
            mock_sg,
            "Shot",
            "updated_at",
            "2026-01-01",
            "2026-01-31",
            additional_filters=[status_filter, ["project", "is", {"type": "Project", "id": 2}]],
        )

        assert result[0]["code"] == "SH001"
        filters = mock_sg.find.call_args.args[1]
        assert ("sg_status_list", "is", "ip") in filters
        assert ["project", "is", {"type": "Project", "id": 2}] in filters


class TestVendorFunctions:
    """Test vendor helper functions."""

    def test_find_vendor_users_versions_and_playlist(self, mock_sg):
        from shotgrid_mcp_server.shared_lib import (
            create_vendor_playlist,
            find_vendor_users,
            find_vendor_versions,
        )

        mock_sg.find.return_value = [{"type": "HumanUser", "id": 8, "name": "Vendor One"}]
        users = find_vendor_users(mock_sg, name_contains="Vendor", email_contains="@studio")

        assert users[0]["id"] == 8
        user_filters = mock_sg.find.call_args.args[1]
        assert ["sg_status_list", "is", "act"] in user_filters
        assert ["name", "contains", "Vendor"] in user_filters
        assert ["email", "contains", "@studio"] in user_filters

        mock_sg.find.return_value = [{"type": "Version", "id": 22, "code": "Vendor v001"}]
        versions = find_vendor_versions(mock_sg, 2, vendor_id=8, status="rev", days=14)

        assert versions[0]["code"] == "Vendor v001"
        version_filters = mock_sg.find.call_args.args[1]
        assert ["project", "is", {"type": "Project", "id": 2}] in version_filters
        assert ["user", "is", {"type": "HumanUser", "id": 8}] in version_filters
        assert ["sg_status_list", "is", "rev"] in version_filters

        mock_sg.create.return_value = {"type": "Playlist", "id": 9, "code": "Vendor Review"}
        playlist = create_vendor_playlist(
            mock_sg,
            "Vendor Review",
            2,
            version_ids=[22, 23],
            vendor_user_ids=[8],
        )

        assert playlist["id"] == 9
        playlist_data = mock_sg.create.call_args.args[1]
        assert playlist_data["description"] == "Vendor review playlist"
        assert playlist_data["versions"] == [{"type": "Version", "id": 22}, {"type": "Version", "id": 23}]


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
