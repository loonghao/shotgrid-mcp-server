"""Tool: shotgrid-vendor__create_vendor_playlist — Create a playlist for vendor review."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import create_vendor_playlist


@skill_entry
def main(
    name: str = "",
    project_id: int = 0,
    version_ids: list[int] | None = None,
    vendor_user_ids: list[int] | None = None,
    **kwargs,
) -> dict:
    """Create a playlist for vendor review in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = create_vendor_playlist(
        sg=sg,
        name=name,
        project_id=project_id,
        version_ids=version_ids,
        vendor_user_ids=vendor_user_ids,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
