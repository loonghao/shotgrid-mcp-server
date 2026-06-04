"""Tool: shotgrid-api__sg_schema_entity_read — Read entity schema from ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_schema_entity_read


@skill_entry
def main(**kwargs) -> dict:
    """Read entity schema. Returns all available entity types."""
    sg = get_current_shotgrid_connection()
    result = sg_schema_entity_read(sg)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
