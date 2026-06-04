"""Tool: shotgrid-api__sg_update — Low-level ShotGrid update operation."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_update
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Low-level ShotGrid update operation. Updates an existing entity.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to update (e.g., Shot, Asset, Task)")
    parser.add_argument("--entity-id", type=int, required=True, help="ID of the entity to update")
    parser.add_argument("--data", type=json.loads, required=True, help="JSON object of fields to update as key-value pairs")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_update(
            sg,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            data=args.data,
        )
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
