"""Tool: shotgrid-search__find_one_entity — Find a single entity by ID or unique field."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_one_sg_entity


@skill_entry
def main(
    entity_type: str = "",
    filters: list | None = None,
    fields: list[str] | None = None,
    **kwargs,
) -> dict:
    """Find a single entity by ID or unique field."""
    sg = get_current_shotgrid_connection()
    result = find_one_sg_entity(
        sg,
        entity_type=entity_type,
        filters=filters,
        fields=fields,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
