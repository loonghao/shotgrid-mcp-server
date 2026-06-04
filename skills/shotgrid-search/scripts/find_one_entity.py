"""Tool: shotgrid-search__find_one_entity — Find a single entity by ID or unique field."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import find_one_sg_entity


def main():
    parser = argparse.ArgumentParser(
        description="Find a single entity in ShotGrid by ID or unique field."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to find (Shot, Asset, Task, Version, etc.)",
    )
    parser.add_argument(
        "--filters",
        type=json.loads,
        required=True,
        help="Filter conditions as JSON, e.g. '[["id","is",1234]]'",
    )
    parser.add_argument(
        "--fields",
        type=json.loads,
        default=None,
        help="Optional list of fields to return as JSON, e.g. '["code","description"]'",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = find_one_sg_entity(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            fields=args.fields,
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
