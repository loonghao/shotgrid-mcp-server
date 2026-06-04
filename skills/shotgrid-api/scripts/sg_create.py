"""Tool: shotgrid-api__sg_create — Low-level ShotGrid create operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_create


@skill_entry
def main(
    entity_type: str,
    data: dict,
    **kwargs,
) -> dict:
    """Low-level ShotGrid create operation. Creates a new entity with provided data."""
    sg = get_current_shotgrid_connection()
    result = sg_create(
        sg,
        entity_type=entity_type,
        data=data,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
