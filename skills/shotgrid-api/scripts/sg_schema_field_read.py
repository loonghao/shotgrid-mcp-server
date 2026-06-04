"""Tool: shotgrid-api__sg_schema_field_read — Read field schema for an entity type."""
# Import built-in modules
import json

# Import third-party modules
from dcc_mcp_core.skill import run_main, skill_entry, skill_success

# Import local modules
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.shared_lib import sg_schema_field_read


@skill_entry
def main(
    entity_type: str,
    field_name: str | None = None,
    **kwargs,
) -> dict:
    """Read field schema for an entity type. Optionally filter by specific field."""
    sg = get_current_shotgrid_connection()
    result = sg_schema_field_read(
        sg,
        entity_type=entity_type,
        field_name=field_name,
    )
    return skill_success({"result": result})


if __name__ == "__main__":
    run_main(main)
