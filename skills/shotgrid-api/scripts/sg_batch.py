"""Tool: shotgrid-api__sg_batch — Low-level ShotGrid batch operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_batch


@skill_entry
def main(
    requests: list,
    **kwargs,
) -> dict:
    """Low-level ShotGrid batch operation. Executes multiple requests in a single API call."""
    sg = get_current_shotgrid_connection()
    result = sg_batch(
        sg,
        requests=requests,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
