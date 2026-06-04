"""Tool: shotgrid-vendor__find_vendor_users — Find vendor (external) users by name or email filter."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import find_vendor_users


@skill_entry
def main(
    name_contains: str = "",
    email_contains: str = "",
    **kwargs,
) -> dict:
    """Find vendor (external) users by name or email filter."""
    sg = get_current_shotgrid_connection()
    result = find_vendor_users(
        sg=sg,
        name_contains=name_contains or None,
        email_contains=email_contains or None,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
