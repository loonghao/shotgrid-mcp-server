"""Tool: shotgrid-api__sg_delete — Low-level ShotGrid delete operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_delete


@skill_entry
def main(
    entity_type: str,
    entity_id: int,
    **kwargs,
) -> dict:
    """Low-level ShotGrid delete operation. Retires an entity by ID."""
    sg = get_current_shotgrid_connection()
    result = sg_delete(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
