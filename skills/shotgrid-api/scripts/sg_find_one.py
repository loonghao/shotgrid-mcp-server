"""Tool: shotgrid-api__sg_find_one — Low-level ShotGrid find_one operation."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_find_one
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Low-level ShotGrid find_one operation. Returns a single entity.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to find (e.g., Shot, Asset, Task)")
    parser.add_argument("--filters", type=json.loads, required=True, help="JSON array of filter conditions")
    parser.add_argument("--fields", type=json.loads, default=None, help="JSON array of field names to return")
    parser.add_argument("--order", type=json.loads, default=None, help="JSON array of sort specifications")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_find_one(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            fields=args.fields,
            order=args.order,
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
