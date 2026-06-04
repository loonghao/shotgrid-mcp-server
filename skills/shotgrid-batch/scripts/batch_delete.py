"""Tool: shotgrid-batch__batch_delete — Delete (retire) multiple entities in a single batch operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import batch_delete


@skill_entry
def main(
    entity_type: str = "",
    entity_ids: list | None = None,
    **kwargs,
) -> dict:
    """Delete (retire) multiple entities in a single batch operation."""
    sg = get_current_shotgrid_connection()
    results = batch_delete(sg, entity_type=entity_type, entity_ids=entity_ids or [])
    return skill_success({"results": results, "total_count": len(results)})


if __name__ == "__main__":
    run_main(main)
