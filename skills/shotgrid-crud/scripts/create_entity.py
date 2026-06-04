"""Tool: shotgrid-crud__create_entity — Create a new entity in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import create_sg_entity


@skill_entry
def main(
    entity_type: str = "",
    data: dict | None = None,
    project_id: int | None = None,
    **kwargs,
) -> dict:
    """Create a new entity in ShotGrid (Shot, Asset, Task, Version, etc.)."""
    sg = get_current_shotgrid_connection()
    entity_data = dict(data or {})
    if project_id is not None:
        entity_data["project"] = {"type": "Project", "id": project_id}
    result = create_sg_entity(sg, entity_type, entity_data)
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
