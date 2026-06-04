"""Tool: shotgrid-api__sg_upload — Upload a file to ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_upload


@skill_entry
def main(
    entity_type: str,
    entity_id: int,
    field_name: str,
    file_path: str,
    **kwargs,
) -> dict:
    """Upload a file to ShotGrid and attach to an entity field."""
    sg = get_current_shotgrid_connection()
    result = sg_upload(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        file_path=file_path,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
