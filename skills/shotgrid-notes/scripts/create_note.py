"""Tool: shotgrid-notes__create_note — Create a note on a ShotGrid entity."""
# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import create_note


@skill_entry
def main(
    entity_type: str = "",
    entity_id: int = 0,
    subject: str = "",
    content: str = "",
    note_type: str = "Note",
    **kwargs,
) -> dict:
    """Create a note on a ShotGrid entity."""
    sg = get_current_shotgrid_connection()
    result = create_note(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
        subject=subject,
        content=content,
        note_type=note_type,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
