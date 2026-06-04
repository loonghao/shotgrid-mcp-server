"""Tool: shotgrid-vendor__find_vendor_versions — Find versions created by vendor users in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_vendor_versions


@skill_entry
def main(
    project_id: int = 0,
    vendor_id: int = 0,
    status: str = "",
    days: int = 30,
    **kwargs,
) -> dict:
    """Find versions created by vendor users in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = find_vendor_versions(
        sg=sg,
        project_id=project_id,
        vendor_id=vendor_id or None,
        status=status or None,
        days=days,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
