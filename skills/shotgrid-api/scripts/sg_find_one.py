"""Tool: shotgrid-api__sg_find_one — Low-level ShotGrid find_one operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_find_one


@skill_entry
def main(
    entity_type: str,
    filters: list,
    fields: list[str] | None = None,
    order: list | None = None,
    **kwargs,
) -> dict:
    """Low-level ShotGrid find_one operation. Returns a single entity matching filters."""
    sg = get_current_shotgrid_connection()
    result = sg_find_one(
        sg,
        entity_type=entity_type,
        filters=filters,
        fields=fields,
        order=order,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
