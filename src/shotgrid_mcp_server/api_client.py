"""ShotGrid API client with Pydantic validation.

This module provides a client for interacting with the ShotGrid API with Pydantic validation.
It ensures that all parameters passed to the ShotGrid API are valid and properly formatted.
"""

import logging
from typing import Any, Dict, List, Optional

from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.api_models import (
    ActivityStreamReadRequest,
    BatchRequest,
    CreateRequest,
    DeleteRequest,
    DownloadAttachmentRequest,
    FindOneRequest,
    FindRequest,
    FollowersRequest,
    FollowingRequest,
    FollowRequest,
    NoteThreadReadRequest,
    ReviveRequest,
    SchemaFieldReadRequest,
    SummarizeRequest,
    TextSearchRequest,
    UpdateRequest,
    UploadRequest,
)
from shotgrid_mcp_server.exceptions import ShotGridMCPError

logger = logging.getLogger(__name__)


class ShotGridAPIClient:
    """Client for interacting with the ShotGrid API with Pydantic validation."""

    def __init__(self, connection: Shotgun):
        """Initialize the client.

        Args:
            connection: ShotGrid connection.
        """
        self.connection = connection

    def find(self, request: FindRequest) -> List[Dict[str, Any]]:
        """Find entities in ShotGrid.

        Args:
            request: Find request parameters.

        Returns:
            List of entities found.

        Raises:
            ShotGridMCPError: If the find operation fails.
        """
        try:
            # Check if the connection is MockgunExt (used in tests)
            if hasattr(self.connection, "__class__") and self.connection.__class__.__name__ == "MockgunExt":
                # MockgunExt doesn't support all parameters, so build kwargs explicitly
                kwargs: Dict[str, Any] = {
                    "fields": request.fields,
                    "order": request.order,
                    "filter_operator": request.filter_operator,
                }
                if request.limit is not None:
                    kwargs["limit"] = request.limit

                result = self.connection.find(
                    request.entity_type,
                    request.filters,
                    **kwargs,
                )
            else:
                # Use all parameters for real ShotGrid API, but only pass limit when set
                kwargs: Dict[str, Any] = {
                    "fields": request.fields,
                    "order": request.order,
                    "filter_operator": request.filter_operator,
                    "retired_only": request.retired_only,
                    "page": request.page,
                    "include_archived_projects": request.include_archived_projects,
                }
                if request.limit is not None:
                    kwargs["limit"] = request.limit
                if request.additional_filter_presets is not None:
                    kwargs["additional_filter_presets"] = request.additional_filter_presets

                result = self.connection.find(
                    request.entity_type,
                    request.filters,
                    **kwargs,
                )
            return result
        except Exception as err:
            logger.error(f"Error in sg.find: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.find: {str(err)}") from err

    def find_one(self, request: FindOneRequest) -> Optional[Dict[str, Any]]:
        """Find a single entity in ShotGrid.

        Args:
            request: Find one request parameters.

        Returns:
            Entity found, or None if not found.

        Raises:
            ShotGridMCPError: If the find_one operation fails.
        """
        try:
            # Check if the connection is MockgunExt (used in tests)
            if hasattr(self.connection, "__class__") and self.connection.__class__.__name__ == "MockgunExt":
                # MockgunExt doesn't support all parameters, so use only the ones it supports
                result = self.connection.find_one(
                    request.entity_type,
                    request.filters,
                    fields=request.fields,
                    order=request.order,
                    filter_operator=request.filter_operator,
                )
            else:
                # Use all parameters for real ShotGrid API
                result = self.connection.find_one(
                    request.entity_type,
                    request.filters,
                    fields=request.fields,
                    order=request.order,
                    filter_operator=request.filter_operator,
                    retired_only=request.retired_only,
                    include_archived_projects=request.include_archived_projects,
                )
            return result
        except Exception as err:
            logger.error(f"Error in sg.find_one: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.find_one: {str(err)}") from err

    def create(self, request: CreateRequest) -> Dict[str, Any]:
        """Create an entity in ShotGrid.

        Args:
            request: Create request parameters.

        Returns:
            Created entity.

        Raises:
            ShotGridMCPError: If the create operation fails.
        """
        try:
            result = self.connection.create(
                request.entity_type,
                request.data,
                return_fields=request.return_fields,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.create: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.create: {str(err)}") from err

    def update(self, request: UpdateRequest) -> Dict[str, Any]:
        """Update an entity in ShotGrid.

        Args:
            request: Update request parameters.

        Returns:
            Updated entity.

        Raises:
            ShotGridMCPError: If the update operation fails.
        """
        try:
            result = self.connection.update(
                request.entity_type,
                request.entity_id,
                request.data,
                multi_entity_update_mode=request.multi_entity_update_mode,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.update: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.update: {str(err)}") from err

    def delete(self, request: DeleteRequest) -> bool:
        """Delete an entity in ShotGrid.

        Args:
            request: Delete request parameters.

        Returns:
            True if successful, False otherwise.

        Raises:
            ShotGridMCPError: If the delete operation fails.
        """
        try:
            result = self.connection.delete(
                request.entity_type,
                request.entity_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.delete: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.delete: {str(err)}") from err

    def revive(self, request: ReviveRequest) -> bool:
        """Revive a deleted entity in ShotGrid.

        Args:
            request: Revive request parameters.

        Returns:
            True if successful, False otherwise.

        Raises:
            ShotGridMCPError: If the revive operation fails.
        """
        try:
            result = self.connection.revive(
                request.entity_type,
                request.entity_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.revive: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.revive: {str(err)}") from err

    def batch(self, request: BatchRequest) -> List[Dict[str, Any]]:
        """Perform a batch operation in ShotGrid.

        Args:
            request: Batch request parameters.

        Returns:
            List of results from the batch operation.

        Raises:
            ShotGridMCPError: If the batch operation fails.
        """
        try:
            result = self.connection.batch(request.requests)
            return result
        except Exception as err:
            logger.error(f"Error in sg.batch: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.batch: {str(err)}") from err

    def summarize(self, request: SummarizeRequest) -> Dict[str, Any]:
        """Summarize data in ShotGrid.

        Args:
            request: Summarize request parameters.

        Returns:
            Summarized data.

        Raises:
            ShotGridMCPError: If the summarize operation fails.
        """
        try:
            result = self.connection.summarize(
                request.entity_type,
                request.filters,
                request.summary_fields,
                filter_operator=request.filter_operator,
                grouping=request.grouping,
                include_archived_projects=request.include_archived_projects,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.summarize: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.summarize: {str(err)}") from err

    def text_search(self, request: TextSearchRequest) -> Dict[str, List[Dict[str, Any]]]:
        """Perform a text search in ShotGrid.

        Args:
            request: Text search request parameters.

        Returns:
            Search results.

        Raises:
            ShotGridMCPError: If the text_search operation fails.
        """
        try:
            result = self.connection.text_search(
                request.text,
                request.entity_types,
                project_ids=request.project_ids,
                limit=request.limit,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.text_search: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.text_search: {str(err)}") from err

    def schema_entity_read(self) -> Dict[str, Dict[str, Any]]:
        """Read entity schema from ShotGrid.

        Returns:
            Entity schema.

        Raises:
            ShotGridMCPError: If the schema_entity_read operation fails.
        """
        try:
            result = self.connection.schema_entity_read()
            return result
        except Exception as err:
            logger.error(f"Error in sg.schema_entity_read: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.schema_entity_read: {str(err)}") from err

    def schema_field_read(self, request: SchemaFieldReadRequest) -> Dict[str, Dict[str, Any]]:
        """Read field schema from ShotGrid.

        Args:
            request: Schema field read request parameters.

        Returns:
            Field schema.

        Raises:
            ShotGridMCPError: If the schema_field_read operation fails.
        """
        try:
            result = self.connection.schema_field_read(
                request.entity_type,
                field_name=request.field_name,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.schema_field_read: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.schema_field_read: {str(err)}") from err

    def upload(self, request: UploadRequest) -> Dict[str, Any]:
        """Upload a file to ShotGrid.

        Args:
            request: Upload request parameters.

        Returns:
            Upload result.

        Raises:
            ShotGridMCPError: If the upload operation fails.
        """
        try:
            result = self.connection.upload(
                request.entity_type,
                request.entity_id,
                request.path,
                field_name=request.field_name,
                display_name=request.display_name,
                tag_list=request.tag_list,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.upload: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.upload: {str(err)}") from err

    def download_attachment(self, request: DownloadAttachmentRequest) -> str:
        """Download an attachment from ShotGrid.

        Args:
            request: Download attachment request parameters.

        Returns:
            Path to downloaded file.

        Raises:
            ShotGridMCPError: If the download_attachment operation fails.
        """
        try:
            result = self.connection.download_attachment(
                request.attachment,
                file_path=request.file_path,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.download_attachment: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.download_attachment: {str(err)}") from err

    def activity_stream_read(self, request: ActivityStreamReadRequest) -> Dict[str, Any]:
        """Read activity stream from ShotGrid.

        Args:
            request: Activity stream read request parameters.

        Returns:
            Activity stream data.

        Raises:
            ShotGridMCPError: If the activity_stream_read operation fails.
        """
        try:
            result = self.connection.activity_stream_read(
                request.entity_type,
                request.entity_id,
                limit=request.limit,
                max_id=request.max_id,
                min_id=request.min_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.activity_stream_read: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.activity_stream_read: {str(err)}") from err

    def follow(self, request: FollowRequest) -> bool:
        """Follow an entity in ShotGrid.

        Args:
            request: Follow request parameters.

        Returns:
            True if successful, False otherwise.

        Raises:
            ShotGridMCPError: If the follow operation fails.
        """
        try:
            result = self.connection.follow(
                request.entity_type,
                request.entity_id,
                user_id=request.user_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.follow: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.follow: {str(err)}") from err

    def unfollow(self, request: FollowRequest) -> bool:
        """Unfollow an entity in ShotGrid.

        Args:
            request: Unfollow request parameters.

        Returns:
            True if successful, False otherwise.

        Raises:
            ShotGridMCPError: If the unfollow operation fails.
        """
        try:
            result = self.connection.unfollow(
                request.entity_type,
                request.entity_id,
                user_id=request.user_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.unfollow: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.unfollow: {str(err)}") from err

    def followers(self, request: FollowersRequest) -> List[Dict[str, Any]]:
        """Get followers of an entity in ShotGrid.

        Args:
            request: Followers request parameters.

        Returns:
            List of followers.

        Raises:
            ShotGridMCPError: If the followers operation fails.
        """
        try:
            result = self.connection.followers(
                request.entity_type,
                request.entity_id,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.followers: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.followers: {str(err)}") from err

    def following(self, request: FollowingRequest) -> List[Dict[str, Any]]:
        """Get entities followed by a user in ShotGrid.

        Args:
            request: Following request parameters.

        Returns:
            List of followed entities.

        Raises:
            ShotGridMCPError: If the following operation fails.
        """
        try:
            result = self.connection.following(
                user_id=request.user_id,
                entity_type=request.entity_type,
            )
            return result
        except Exception as err:
            logger.error(f"Error in sg.following: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.following: {str(err)}") from err

    def note_thread_read(self, request: NoteThreadReadRequest) -> Dict[str, Any]:
        """Read a note thread from ShotGrid.

        Args:
            request: Note thread read request parameters.

        Returns:
            Note thread data.

        Raises:
            ShotGridMCPError: If the note_thread_read operation fails.
        """
        try:
            result = self.connection.note_thread_read(request.note_id)
            return result
        except Exception as err:
            logger.error(f"Error in sg.note_thread_read: {str(err)}")
            raise ShotGridMCPError(f"Error executing sg.note_thread_read: {str(err)}") from err
