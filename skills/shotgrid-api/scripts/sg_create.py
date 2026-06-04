"""Tool: shotgrid-api__sg_create — Low-level ShotGrid create operation."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_create
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Low-level ShotGrid create operation. Creates a new entity.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to create (e.g., Shot, Asset, Task)")
    parser.add_argument("--data", type=json.loads, required=True, help="JSON object of entity data as key-value pairs")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_create(
            sg,
            entity_type=args.entity_type,
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
