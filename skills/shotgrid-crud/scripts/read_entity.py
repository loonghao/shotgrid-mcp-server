"""Tool: shotgrid-crud__read_entity — Read a single entity from ShotGrid by ID."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import read_sg_entity


@skill_entry
def main(
    entity_type: str = "",
    entity_id: int = 0,
    fields: list[str] | None = None,
    **kwargs,
) -> dict:
    """Read a single entity from ShotGrid by ID."""
    sg = get_current_shotgrid_connection()
    result = read_sg_entity(sg, entity_type, entity_id, fields)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
