"""Tool: shotgrid-notes__update_note — Update a note in ShotGrid."""
# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import update_note


@skill_entry
def main(
    note_id: int = 0,
    data: dict | None = None,
    **kwargs,
) -> dict:
    """Update a note in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = update_note(sg, note_id=note_id, data=data or {})
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
