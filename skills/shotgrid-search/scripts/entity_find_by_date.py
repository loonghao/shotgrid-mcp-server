"""Tool: shotgrid-search__entity_find_by_date — Find entities within a date range."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_sg_entities_by_date


@skill_entry
def main(
    entity_type: str = "",
    date_field: str = "",
    start_date: str = "",
    end_date: str = "",
    **kwargs,
) -> dict:
    """Find entities within a date range."""
    sg = get_current_shotgrid_connection()
    result = find_sg_entities_by_date(
        sg,
        entity_type=entity_type,
        date_field=date_field,
        start_date=start_date,
        end_date=end_date,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
