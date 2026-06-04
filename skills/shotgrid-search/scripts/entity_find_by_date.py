"""Tool: shotgrid-search__entity_find_by_date — Find entities within a date range."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import find_sg_entities_by_date


def main():
    parser = argparse.ArgumentParser(
        description="Find entities within a specific date range."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to find (Shot, Asset, Task, Version, etc.)",
    )
    parser.add_argument(
        "--date_field",
        type=str,
        required=True,
        help="Date field to filter on (e.g., created_at, updated_at, due_date)",
    )
    parser.add_argument(
        "--start_date",
        type=str,
        required=True,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end_date",
        type=str,
        required=True,
        help="End date in YYYY-MM-DD format",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = find_sg_entities_by_date(
            sg,
            entity_type=args.entity_type,
            date_field=args.date_field,
            start_date=args.start_date,
            end_date=args.end_date,
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
