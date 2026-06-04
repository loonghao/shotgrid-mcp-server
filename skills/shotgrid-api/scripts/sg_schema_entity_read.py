"""Tool: shotgrid-api__sg_schema_entity_read — Read entity schema from ShotGrid."""
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_schema_entity_read
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    try:
        sg = get_current_shotgrid_connection()
        result = sg_schema_entity_read(sg)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
