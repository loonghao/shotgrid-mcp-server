"""Tool: shotgrid-playlists__add_versions_to_playlist — Add versions to an existing playlist."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import add_versions_to_playlist as add_sg_versions


@skill_entry
def main(
    playlist_id: int = 0,
    version_ids: list[int] | None = None,
    **kwargs,
) -> dict:
    """Add versions to an existing playlist."""
    sg = get_current_shotgrid_connection()
    result = add_sg_versions(
        sg,
        playlist_id=playlist_id,
        version_ids=version_ids or [],
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
