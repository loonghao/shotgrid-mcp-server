"""Tool: shotgrid-search__search_entities — Search for entities in ShotGrid using filters."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import search_sg_entities


def main():
    parser = argparse.ArgumentParser(
        description="Search for entities in ShotGrid using filters and field selection."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to search (Shot, Asset, Task, Version, etc.)",
    )
    parser.add_argument(
        "--filters",
        type=json.loads,
        default=None,
        help="List of filter conditions as JSON, e.g. '[["sg_status_list","is","ip"]]'",
    )
    parser.add_argument(
        "--fields",
        type=json.loads,
        default=None,
        help="Optional list of fields to return as JSON, e.g. '["code","description"]'",
    )
    parser.add_argument(
        "--order",
        type=json.loads,
        default=None,
        help="Optional sort order as JSON, e.g. '[{"field_name":"code","direction":"asc"}]'",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional maximum number of results",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = search_sg_entities(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            fields=args.fields,
            order=args.order,
            limit=args.limit,
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
