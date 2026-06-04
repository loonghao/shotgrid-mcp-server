"""Tool: shotgrid-api__sg_download_attachment — Download an attachment from ShotGrid."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_download_attachment


@skill_entry
def main(
    attachment_id: int,
    output_path: str | None = None,
    **kwargs,
) -> dict:
    """Download an attachment from ShotGrid by attachment ID."""
    sg = get_current_shotgrid_connection()
    result = sg_download_attachment(
        sg,
        attachment_id=attachment_id,
        output_path=output_path,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
