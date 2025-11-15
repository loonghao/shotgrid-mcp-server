"""Note tools for ShotGrid MCP server.

This module contains tools for working with ShotGrid notes.
"""

from fastmcp import FastMCP
from shotgun_api3.lib.mockgun import Shotgun

from shotgrid_mcp_server.connection_pool import ShotGridConnectionContext
from shotgrid_mcp_server.models import (
    NoteCreateRequest,
    NoteCreateResponse,
    NoteReadResponse,
    NoteUpdateRequest,
    NoteUpdateResponse,
)


def register_note_tools(server: FastMCP, sg: Shotgun) -> None:
    """Register note tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    # Register note tools
    @server.tool("shotgrid.note.create")
    async def create_note_tool(request: NoteCreateRequest) -> NoteCreateResponse:
        """Create a new note in ShotGrid.

        Args:
            request: Note creation request.

        Returns:
            Note creation response.
        """
        context = ShotGridConnectionContext(sg)
        return create_note(request, context)

    @server.tool("shotgrid.note.read")
    async def read_note_tool(note_id: int) -> NoteReadResponse:
        """Read a note from ShotGrid.

        Args:
            note_id: Note ID.

        Returns:
            Note read response.
        """
        context = ShotGridConnectionContext(sg)
        return read_note(note_id, context)

    @server.tool("shotgrid.note.update")
    async def update_note_tool(request: NoteUpdateRequest) -> NoteUpdateResponse:
        """Update a note in ShotGrid.

        Args:
            request: Note update request.

        Returns:
            Note update response.
        """
        context = ShotGridConnectionContext(sg)
        return update_note(request, context)


def create_note(request: NoteCreateRequest, context: ShotGridConnectionContext) -> NoteCreateResponse:
    """Create a new note in ShotGrid.

    Args:
        request: Note creation request.
        context: ShotGrid connection context.

    Returns:
        Note creation response.
    """
    # Create note data
    note_data = {
        "project": {"type": "Project", "id": request.project_id},
        "subject": request.subject,
        "content": request.content,
    }

    # Add optional fields
    if request.link_entity_type and request.link_entity_id:
        note_data["note_links"] = [{"type": request.link_entity_type, "id": request.link_entity_id}]

    if request.user_id:
        note_data["user"] = {"type": "HumanUser", "id": request.user_id}

    if request.addressings_to:
        note_data["addressings_to"] = [{"type": "HumanUser", "id": user_id} for user_id in request.addressings_to]

    if request.addressings_cc:
        note_data["addressings_cc"] = [{"type": "HumanUser", "id": user_id} for user_id in request.addressings_cc]

    # Create note
    sg = context.connection
    note = sg.create("Note", note_data)

    # Return response
    return NoteCreateResponse(
        id=note["id"],
        type="Note",
        subject=note["subject"],
        content=note.get("content", ""),
        created_at=note.get("created_at", ""),
    )


def read_note(note_id: int, context: ShotGridConnectionContext) -> NoteReadResponse:
    """Read a note from ShotGrid.

    Args:
        note_id: Note ID.
        context: ShotGrid connection context.

    Returns:
        Note read response.
    """
    # Define fields to retrieve
    fields = [
        "subject",
        "content",
        "created_at",
        "updated_at",
        "user",
        "note_links",
        "addressings_to",
        "addressings_cc",
    ]

    # Read note
    sg = context.connection
    note = sg.find_one("Note", [["id", "is", note_id]], fields)

    if not note:
        raise ValueError(f"Note with ID {note_id} not found")

    # Extract user info
    user_id = None
    user_name = None
    if note.get("user"):
        user_id = note["user"].get("id")
        user_name = note["user"].get("name")

    # Extract link info
    link_entity_type = None
    link_entity_id = None
    if note.get("note_links") and len(note["note_links"]) > 0:
        link_entity_type = note["note_links"][0].get("type")
        link_entity_id = note["note_links"][0].get("id")

    # Extract addressings
    addressings_to = []
    if note.get("addressings_to"):
        addressings_to = [user.get("id") for user in note["addressings_to"]]

    addressings_cc = []
    if note.get("addressings_cc"):
        addressings_cc = [user.get("id") for user in note["addressings_cc"]]

    # Return response
    return NoteReadResponse(
        id=note_id,
        type="Note",
        subject=note["subject"],
        content=note.get("content", ""),
        created_at=note.get("created_at", ""),
        updated_at=note.get("updated_at", ""),
        user_id=user_id,
        user_name=user_name,
        link_entity_type=link_entity_type,
        link_entity_id=link_entity_id,
        addressings_to=addressings_to,
        addressings_cc=addressings_cc,
    )


def update_note(request: NoteUpdateRequest, context: ShotGridConnectionContext) -> NoteUpdateResponse:
    """Update a note in ShotGrid.

    Args:
        request: Note update request.
        context: ShotGrid connection context.

    Returns:
        Note update response.
    """
    # Create update data
    update_data = {}

    # Add fields to update
    if request.subject is not None:
        update_data["subject"] = request.subject

    if request.content is not None:
        update_data["content"] = request.content

    if request.link_entity_type is not None and request.link_entity_id is not None:
        update_data["note_links"] = [{"type": request.link_entity_type, "id": request.link_entity_id}]

    if request.addressings_to is not None:
        update_data["addressings_to"] = [{"type": "HumanUser", "id": user_id} for user_id in request.addressings_to]

    if request.addressings_cc is not None:
        update_data["addressings_cc"] = [{"type": "HumanUser", "id": user_id} for user_id in request.addressings_cc]

    # Update note
    sg = context.connection
    sg.update("Note", request.id, update_data)
    # Get updated note
    note = sg.find_one("Note", [["id", "is", request.id]], ["subject", "content", "updated_at"])

    # Return response
    return NoteUpdateResponse(
        id=request.id,
        type="Note",
        subject=note["subject"],
        content=note.get("content", ""),
        updated_at=note.get("updated_at", ""),
    )
