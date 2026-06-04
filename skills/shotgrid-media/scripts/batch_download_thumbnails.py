"""Tool: shotgrid-media__batch_download_thumbnails — Download multiple thumbnails in batch."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import batch_download_thumbnails


@skill_entry
def main(
    entity_type: str = "",
    entity_ids: list[int] | None = None,
    field_name: str = "image",
    output_dir: str = "",
    **kwargs,
) -> dict:
    """Download multiple thumbnails in batch for a list of entities."""
    if entity_ids is None:
        entity_ids = []
    sg = get_current_shotgrid_connection()
    result = batch_download_thumbnails(
        sg,
        entity_type=entity_type,
        entity_ids=entity_ids,
        field_name=field_name,
        output_dir=output_dir,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
