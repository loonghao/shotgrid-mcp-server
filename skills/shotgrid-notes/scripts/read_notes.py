"""Tool: shotgrid-notes__read_notes — Read notes from a ShotGrid entity."""
# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import get_entity_notes


@skill_entry
def main(
    entity_type: str = "",
    entity_id: int = 0,
    fields: list[str] | None = None,
    **kwargs,
) -> dict:
    """Read notes from a ShotGrid entity."""
    sg = get_current_shotgrid_connection()
    result = get_entity_notes(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
        fields=fields,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
