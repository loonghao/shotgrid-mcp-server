"""Tool: shotgrid-playlists__find_playlists — Search for playlists in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_playlists as find_sg_playlists


@skill_entry
def main(
    project_id: int | None = None,
    name_contains: str = "",
    fields: list[str] | None = None,
    **kwargs,
) -> dict:
    """Search for playlists in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = find_sg_playlists(
        sg,
        project_id=project_id,
        name_contains=name_contains or None,
        fields=fields,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
