"""Tool: shotgrid-api__sg_revive — Revive a retired entity in ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_revive


@skill_entry
def main(
    entity_type: str,
    entity_id: int,
    **kwargs,
) -> dict:
    """Revive a retired entity by type and ID."""
    sg = get_current_shotgrid_connection()
    result = sg_revive(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
