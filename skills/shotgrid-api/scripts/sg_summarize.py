"""Tool: shotgrid-api__sg_summarize — Summarize entities matching filters."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_summarize


@skill_entry
def main(
    entity_type: str,
    filters: list,
    summarize_field: str,
    **kwargs,
) -> dict:
    """Summarize entities matching filters. Returns counts grouped by a field."""
    sg = get_current_shotgrid_connection()
    result = sg_summarize(
        sg,
        entity_type=entity_type,
        filters=filters,
        summarize_field=summarize_field,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
