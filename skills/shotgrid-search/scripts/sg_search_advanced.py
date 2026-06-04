"""Tool: shotgrid-search__sg_search_advanced — Advanced search with time-based filters and related fields."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_search_advanced as _sg_search_advanced


@skill_entry
def main(
    entity_type: str = "",
    filters: list | None = None,
    time_filters: list | None = None,
    fields: list[str] | None = None,
    related_fields: dict | None = None,
    order: list | None = None,
    limit: int | None = None,
    **kwargs,
) -> dict:
    """Advanced search with time-based filters and related fields."""
    sg = get_current_shotgrid_connection()
    result = _sg_search_advanced(
        sg,
        entity_type=entity_type,
        filters=filters,
        time_filters=time_filters,
        fields=fields,
        related_fields=related_fields,
        order=order,
        limit=limit,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
