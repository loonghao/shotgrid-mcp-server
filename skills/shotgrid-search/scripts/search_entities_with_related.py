"""Tool: shotgrid-search__search_entities_with_related — Search entities with related entity data in a single query."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import search_sg_entities_with_related


@skill_entry
def main(
    entity_type: str = "",
    filters: list | None = None,
    fields: list[str] | None = None,
    related_fields: dict | None = None,
    order: list | None = None,
    limit: int | None = None,
    **kwargs,
) -> dict:
    """Search entities with related entity data in a single query."""
    sg = get_current_shotgrid_connection()
    result = search_sg_entities_with_related(
        sg,
        entity_type=entity_type,
        filters=filters,
        fields=fields,
        related_fields=related_fields,
        order=order,
        limit=limit,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
