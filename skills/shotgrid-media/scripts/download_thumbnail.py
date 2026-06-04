"""Tool: shotgrid-media__download_thumbnail — Download a thumbnail from ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import download_thumbnail


@skill_entry
def main(
    entity_type: str = "",
    entity_id: int = 0,
    field_name: str = "image",
    output_path: str | None = None,
    **kwargs,
) -> dict:
    """Download a thumbnail from ShotGrid for a given entity."""
    sg = get_current_shotgrid_connection()
    result = download_thumbnail(
        sg,
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        output_path=output_path,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
