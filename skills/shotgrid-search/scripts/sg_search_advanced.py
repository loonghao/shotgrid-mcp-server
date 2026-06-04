"""Tool: shotgrid-search__sg_search_advanced — Advanced search with time-based filters and related fields."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import sg_search_advanced


def main():
    parser = argparse.ArgumentParser(
        description="Advanced search with time-based filters and related fields."
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
        help="Standard filters as JSON, e.g. '[["sg_status_list","is","ip"]]'",
    )
    parser.add_argument(
        "--time_filters",
        type=json.loads,
        default=None,
        help="Time-based filters as JSON, e.g. '[{"field":"updated_at","operator":"in_last","count":7,"unit":"DAY"}]'",
    )
    parser.add_argument(
        "--fields",
        type=json.loads,
        default=None,
        help="Optional list of fields as JSON",
    )
    parser.add_argument(
        "--related_fields",
        type=json.loads,
        default=None,
        help="Related entity fields as JSON",
    )
    parser.add_argument(
        "--order",
        type=json.loads,
        default=None,
        help="Optional sort order as JSON",
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
        result = sg_search_advanced(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            time_filters=args.time_filters,
            fields=args.fields,
            related_fields=args.related_fields,
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
