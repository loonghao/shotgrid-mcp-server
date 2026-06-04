"""Tool: shotgrid-playlists__create_playlist — Create a playlist for version review in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import create_playlist as create_sg_playlist


@skill_entry
def main(
    name: str = "",
    project_id: int = 0,
    description: str = "",
    version_ids: list[int] | None = None,
    **kwargs,
) -> dict:
    """Create a playlist for version review in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = create_sg_playlist(
        sg,
        name=name,
        project_id=project_id,
        description=description or None,
        version_ids=version_ids,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
