"""Tool: shotgrid-search__user_find_active — Find users active in the last N days."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import find_active_sg_users


def main():
    parser = argparse.ArgumentParser(
        description="Find users who have been active in the last N days."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Days to look back (default: 30)",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = find_active_sg_users(sg, days=args.days)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
