"""Tool: shotgrid-batch__batch_update — Update multiple entities in a single batch operation."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import batch_update


@skill_entry
def main(
    entity_type: str = "",
    data_list: list | None = None,
    **kwargs,
) -> dict:
    """Update multiple entities of the same type in a single batch operation."""
    sg = get_current_shotgrid_connection()
    # data_list comes as [{id: 1, data: {...}}, ...] per tools.yaml schema
    # Convert to shared_lib format [{id: 1, ...fields}, ...]
    converted = []
    for item in (data_list or []):
        if isinstance(item, dict):
            entry = {"id": item.get("id")}
            entry.update(item.get("data", {}))
            converted.append(entry)
    results = batch_update(sg, entity_type=entity_type, data_list=converted)
    return skill_success({"results": results, "total_count": len(results)})


if __name__ == "__main__":
    run_main(main)
