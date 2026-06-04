"""Tool: shotgrid-batch__batch_create — Create multiple entities in a single batch operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import batch_create


@skill_entry
def main(
    entity_type: str = "",
    data_list: list | None = None,
    **kwargs,
) -> dict:
    """Create multiple entities of the same type in a single batch operation."""
    sg = get_current_shotgrid_connection()
    results = batch_create(sg, entity_type=entity_type, data_list=data_list or [])
    return skill_success({"results": results, "total_count": len(results)})


if __name__ == "__main__":
    run_main(main)
