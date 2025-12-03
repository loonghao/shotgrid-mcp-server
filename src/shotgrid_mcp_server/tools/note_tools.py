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
from shotgrid_mcp_server.response_models import generate_entity_url


def register_note_tools(server: FastMCP, sg: Shotgun) -> None:
    """Register note tools with the server.

    Args:
        server: FastMCP server instance.
        sg: ShotGrid connection.
    """

    # Register note tools
    @server.tool("shotgrid_note_create")
    async def create_note_tool(request: NoteCreateRequest) -> NoteCreateResponse:
        """Create a new note in ShotGrid for feedback, comments, and communication.

        **When to use this tool:**
        - Add feedback on a version during review
        - Create task notes for artists with instructions
        - Document issues or bugs on shots/assets
        - Add client feedback to versions
        - Create general project notes or announcements
        - Link notes to specific entities (shots, assets, versions, tasks)
        - Send notifications to specific users about the note

        **When NOT to use this tool:**
        - To read existing notes - Use `shotgrid_note_read` instead
        - To update existing notes - Use `shotgrid_note_update` instead
        - To search for notes - Use `search_entities` with entity_type="Note" instead
        - To delete notes - Use `delete_entity` with entity_type="Note" instead

        **Common use cases:**
        - Review feedback: "Animation looks great, approved for final"
        - Task instructions: "Please focus on facial expressions in this shot"
        - Bug reports: "Missing texture on character's left arm"
        - Client feedback: "Client wants the lighting warmer in this sequence"

        Args:
            request: NoteCreateRequest containing:

                project_id: ID of the project for this note.
                           All notes must belong to a project.

                           Example: 123

                subject: Subject/title of the note.
                        Brief summary of the note's content.

                        Examples:
                        - "Animation timing needs adjustment"
                        - "Client feedback on lighting"
                        - "Bug: Missing texture on character"

                content: Full content/body of the note.
                        Detailed feedback or comments.
                        Supports plain text and basic formatting.

                        Example:
                        "The character's walk cycle feels too slow. Please speed it up by 20% and add more bounce to the step."

                link_entity_type: Optional entity type to link the note to.
                                 Common types: "Version", "Shot", "Asset", "Task"
                                 Must be provided with link_entity_id.

                                 Example: "Version"

                link_entity_id: Optional entity ID to link the note to.
                               Must be provided with link_entity_type.

                               Example: 1234

                user_id: Optional ID of the user creating the note.
                        If not provided, uses the API user.

                        Example: 42

                addressings_to: Optional list of user IDs to address the note to (recipients).
                               These users will be notified about the note.

                               Example: [42, 43, 44]

                addressings_cc: Optional list of user IDs to CC on the note.
                               These users will receive a copy of the notification.

                               Example: [45, 46]

        Returns:
            NoteCreateResponse containing:
            - id: ID of the created note
            - type: "Note"
            - subject: Note subject
            - content: Note content
            - created_at: Creation timestamp
            - user_id: Creator user ID
            - user_name: Creator user name
            - link_entity_type: Linked entity type (if any)
            - link_entity_id: Linked entity ID (if any)

            Example:
            {
                "id": 5678,
                "type": "Note",
                "subject": "Animation timing needs adjustment",
                "content": "The character's walk cycle feels too slow...",
                "created_at": "2025-01-15T10:30:00Z",
                "user_id": 42,
                "user_name": "John Doe",
                "link_entity_type": "Version",
                "link_entity_id": 1234
            }

        Raises:
            ValueError: If project_id is invalid or required fields are missing.

        Examples:
            Create note on a version:
            {
                "project_id": 123,
                "subject": "Great work on the animation!",
                "content": "The timing and spacing look perfect. Approved for final.",
                "link_entity_type": "Version",
                "link_entity_id": 1234,
                "addressings_to": [42]
            }

            Create task note:
            {
                "project_id": 123,
                "subject": "Task instructions",
                "content": "Please focus on the facial expressions in this shot. Reference the animatic for timing.",
                "link_entity_type": "Task",
                "link_entity_id": 5678,
                "user_id": 10,
                "addressings_to": [42, 43]
            }

            Create general project note:
            {
                "project_id": 123,
                "subject": "Project update",
                "content": "All shots in sequence 010 are now ready for review.",
                "addressings_to": [42, 43, 44],
                "addressings_cc": [45]
            }

            Create client feedback note:
            {
                "project_id": 123,
                "subject": "Client feedback - Episode 1",
                "content": "Client loves the overall look but wants the lighting warmer in shots 010-020.",
                "link_entity_type": "Shot",
                "link_entity_id": 1001,
                "addressings_to": [42]
            }

        Note Linking:
            - Notes can be linked to any entity type (Shot, Asset, Version, Task, etc.)
            - One note can be linked to multiple entities via note_links field
            - Linked notes appear in the entity's Notes tab in ShotGrid
            - Use link_entity_type and link_entity_id for single entity linking

        Notifications:
            - Users in addressings_to receive direct notifications
            - Users in addressings_cc receive CC notifications
            - Notifications are sent via email and ShotGrid inbox

        Note:
            - All notes must belong to a project
            - Subject and content are required
            - Notes support @mentions in content (use @username)
            - Created notes are immediately visible in ShotGrid
            - Use shotgrid_note_update to modify notes after creation
        """
        context = ShotGridConnectionContext(sg)
        return create_note(request, context)

    @server.tool("shotgrid_note_read")
    async def read_note_tool(note_id: int) -> NoteReadResponse:
        """Read a note from ShotGrid to view its content and metadata.

        **When to use this tool:**
        - You have a note ID and need to view its full content
        - You need to check who created the note and when
        - You need to see which entities the note is linked to
        - You need to view note recipients (addressings_to, addressings_cc)
        - You need to retrieve note details for display or processing

        **When NOT to use this tool:**
        - To create new notes - Use `shotgrid_note_create` instead
        - To update existing notes - Use `shotgrid_note_update` instead
        - To search for notes by criteria - Use `search_entities` with entity_type="Note" instead
        - To find notes on a specific entity - Use `search_entities` with filters instead

        **Common use cases:**
        - View feedback on a version: Read note ID 5678 to see review comments
        - Check note recipients: See who was addressed in the note
        - Retrieve note for display: Get full note details for UI display

        Args:
            note_id: ID of the note to read.
                    Must be a valid note ID in ShotGrid.

                    Example: 5678

        Returns:
            NoteReadResponse containing:
            - id: Note ID
            - type: "Note"
            - subject: Note subject/title
            - content: Full note content
            - created_at: Creation timestamp
            - updated_at: Last update timestamp
            - user_id: Creator user ID
            - user_name: Creator user name
            - link_entities: List of linked entities
            - addressings_to: List of recipient users
            - addressings_cc: List of CC'd users

            Example:
            {
                "id": 5678,
                "type": "Note",
                "subject": "Animation timing needs adjustment",
                "content": "The character's walk cycle feels too slow...",
                "created_at": "2025-01-15T10:30:00Z",
                "updated_at": "2025-01-15T11:00:00Z",
                "user_id": 42,
                "user_name": "John Doe",
                "link_entities": [
                    {"type": "Version", "id": 1234, "name": "shot_010_anim_v003"}
                ],
                "addressings_to": [
                    {"type": "HumanUser", "id": 43, "name": "Jane Smith"}
                ],
                "addressings_cc": []
            }

        Raises:
            ValueError: If note with the given ID is not found.

        Examples:
            Read a note:
            {
                "note_id": 5678
            }

        Note:
            - Returns all note fields including content, metadata, and links
            - Linked entities include type, id, and name
            - User information includes id and name
            - Timestamps are in ISO 8601 format
        """
        context = ShotGridConnectionContext(sg)
        return read_note(note_id, context)

    @server.tool("shotgrid_note_update")
    async def update_note_tool(request: NoteUpdateRequest) -> NoteUpdateResponse:
        """Update an existing note in ShotGrid to modify its content or recipients.

        **When to use this tool:**
        - Correct typos or errors in note content
        - Update note subject to reflect changes
        - Add or remove note recipients (addressings_to)
        - Add or remove CC recipients (addressings_cc)
        - Modify feedback based on new information
        - Update note content after further review

        **When NOT to use this tool:**
        - To create new notes - Use `shotgrid_note_create` instead
        - To read note content - Use `shotgrid_note_read` instead
        - To delete notes - Use `delete_entity` with entity_type="Note" instead
        - To search for notes - Use `search_entities` with entity_type="Note" instead

        **Common use cases:**
        - Fix typo: Update note content to correct spelling errors
        - Add recipient: Add user ID 45 to addressings_to list
        - Update feedback: Change "needs work" to "approved" after revision

        Args:
            request: NoteUpdateRequest containing:

                id: ID of the note to update.
                   Must be a valid note ID in ShotGrid.

                   Example: 5678

                subject: Optional new subject/title for the note.
                        If not provided, subject remains unchanged.

                        Example: "Updated: Animation timing needs adjustment"

                content: Optional new content/body for the note.
                        If not provided, content remains unchanged.

                        Example: "The character's walk cycle feels too slow. Please speed it up by 25% (updated from 20%)."

                addressings_to: Optional new list of recipient user IDs.
                               If provided, replaces existing recipients.
                               If not provided, recipients remain unchanged.

                               Example: [42, 43, 44]

                addressings_cc: Optional new list of CC user IDs.
                               If provided, replaces existing CC list.
                               If not provided, CC list remains unchanged.

                               Example: [45, 46]

        Returns:
            NoteUpdateResponse containing:
            - id: Note ID
            - type: "Note"
            - subject: Updated subject
            - content: Updated content
            - updated_at: Update timestamp

            Example:
            {
                "id": 5678,
                "type": "Note",
                "subject": "Updated: Animation timing needs adjustment",
                "content": "The character's walk cycle feels too slow. Please speed it up by 25%.",
                "updated_at": "2025-01-15T12:00:00Z"
            }

        Raises:
            ValueError: If note with the given ID is not found.

        Examples:
            Update note content:
            {
                "id": 5678,
                "content": "The character's walk cycle feels too slow. Please speed it up by 25% (updated from 20%)."
            }

            Update note subject and content:
            {
                "id": 5678,
                "subject": "Updated: Animation timing needs adjustment",
                "content": "The character's walk cycle feels too slow. Please speed it up by 25% and add more weight to the landing."
            }

            Update note recipients:
            {
                "id": 5678,
                "addressings_to": [42, 43, 44],
                "addressings_cc": [45]
            }

            Update all fields:
            {
                "id": 5678,
                "subject": "Final: Animation approved with minor notes",
                "content": "Great work! Just add a bit more bounce to the step and we're good to go.",
                "addressings_to": [42],
                "addressings_cc": []
            }

        Note:
            - Only provided fields are updated; others remain unchanged
            - Updating addressings_to or addressings_cc replaces the entire list
            - Updated notes trigger notifications to new recipients
            - Update timestamp is automatically set
            - Cannot change the linked entities (use note_links field via entity_update)
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

    # Generate entity URL
    sg_url = generate_entity_url(sg.base_url, "Note", note["id"]) if note.get("id") else None

    # Return response
    return NoteCreateResponse(
        id=note["id"],
        type="Note",
        subject=note["subject"],
        content=note.get("content", ""),
        created_at=note.get("created_at", ""),
        sg_url=sg_url,
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
