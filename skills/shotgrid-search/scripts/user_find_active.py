"""Tool: shotgrid-search__user_find_active — Find users active in the last N days."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_active_sg_users


@skill_entry
def main(
    days: int = 30,
    **kwargs,
) -> dict:
    """Find users active in the last N days."""
    sg = get_current_shotgrid_connection()
    result = find_active_sg_users(sg, days=days)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
