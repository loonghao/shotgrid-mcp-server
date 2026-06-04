"""Tool: shotgrid-api__sg_find — Low-level ShotGrid find operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_find


@skill_entry
def main(
    entity_type: str,
    filters: list,
    fields: list[str] | None = None,
    order: list | None = None,
    filter_operator: str | None = None,
    limit: int | None = None,
    page: int | None = None,
    **kwargs,
) -> dict:
    """Low-level ShotGrid find operation. Returns raw results with filtering, ordering, and pagination."""
    sg = get_current_shotgrid_connection()
    result = sg_find(
        sg,
        entity_type=entity_type,
        filters=filters,
        fields=fields,
        order=order,
        filter_operator=filter_operator,
        limit=limit,
        page=page,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
