"""Tool: shotgrid-api__sg_find — Low-level ShotGrid find operation."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_find
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Low-level ShotGrid find operation. Returns raw results.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to find (e.g., Shot, Asset, Task)")
    parser.add_argument("--filters", type=json.loads, required=True, help="JSON array of filter conditions")
    parser.add_argument("--fields", type=json.loads, default=None, help="JSON array of field names to return")
    parser.add_argument("--order", type=json.loads, default=None, help="JSON array of sort specifications")
    parser.add_argument("--filter-operator", type=str, default=None, help="Logical operator for combining filters")
    parser.add_argument("--limit", type=int, default=None, help="Maximum number of results to return")
    parser.add_argument("--page", type=int, default=None, help="Page number for paginated results")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_find(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            fields=args.fields,
            order=args.order,
            filter_operator=args.filter_operator,
            limit=args.limit,
            page=args.page,
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
