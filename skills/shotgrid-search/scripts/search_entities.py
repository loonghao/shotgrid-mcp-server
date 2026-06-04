"""Tool: shotgrid-search__search_entities — Search for entities in ShotGrid using filters."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import search_sg_entities


@skill_entry
def main(
    entity_type: str = "",
    filters: list | None = None,
    fields: list[str] | None = None,
    order: list | None = None,
    limit: int | None = None,
    **kwargs,
) -> dict:
    """Search for entities in ShotGrid using filters and field selection."""
    sg = get_current_shotgrid_connection()
    result = search_sg_entities(
        sg,
        entity_type=entity_type,
        filters=filters,
        fields=fields,
        order=order,
        limit=limit,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
