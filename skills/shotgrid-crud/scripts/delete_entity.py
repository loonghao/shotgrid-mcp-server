"""Tool: shotgrid-crud__delete_entity — Delete (retire) an entity in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import delete_sg_entity


@skill_entry
def main(
    entity_type: str = "",
    entity_id: int = 0,
    **kwargs,
) -> dict:
    """Delete (retire) an entity in ShotGrid."""
    sg = get_current_shotgrid_connection()
    result = delete_sg_entity(sg, entity_type, entity_id)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
