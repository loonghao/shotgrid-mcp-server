"""Tool: shotgrid-crud__entity_schema — Get field schema information for an entity type."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import get_sg_entity_schema


@skill_entry
def main(
    entity_type: str = "",
    **kwargs,
) -> dict:
    """Get field schema information for an entity type (Shot, Asset, Task, etc.)."""
    sg = get_current_shotgrid_connection()
    result = get_sg_entity_schema(sg, entity_type)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
