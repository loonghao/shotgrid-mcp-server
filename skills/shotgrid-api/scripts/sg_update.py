"""Tool: shotgrid-api__sg_update — Low-level ShotGrid update operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_update


@skill_entry
def main(
    entity_type: str,
    entity_id: int,
    data: dict,
    **kwargs,
) -> dict:
    """Low-level ShotGrid update operation. Updates an existing entity's fields."""
    sg = get_current_shotgrid_connection()
    result = sg_update(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
        data=data,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
