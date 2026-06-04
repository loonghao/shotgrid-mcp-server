"""Tool: shotgrid-search__project_find_active — Find projects active in the last N days."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_active_sg_projects


@skill_entry
def main(
    days: int = 90,
    **kwargs,
) -> dict:
    """Find projects active in the last N days."""
    sg = get_current_shotgrid_connection()
    result = find_active_sg_projects(sg, days=days)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
