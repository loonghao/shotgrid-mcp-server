"""Tool: shotgrid-api__sg_text_search — Full-text search across ShotGrid entities."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_text_search


@skill_entry
def main(
    text: str,
    entity_types: list[str],
    **kwargs,
) -> dict:
    """Full-text search across entities. Searches by text and entity types."""
    sg = get_current_shotgrid_connection()
    result = sg_text_search(
        sg,
        text=text,
        entity_types=entity_types,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
