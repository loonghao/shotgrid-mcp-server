"""Tool: shotgrid-vendor__find_vendor_versions -- Find versions created by vendor users in ShotGrid."""
import argparse
import json
import sys

from shotgrid_mcp_server.shared_lib import find_vendor_versions
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Find versions created by vendor users in ShotGrid."
    )
    parser.add_argument(
        "--project_id",
        type=int,
        required=True,
        help="Project ID to filter versions by.",
    )
    parser.add_argument(
        "--vendor_id",
        type=int,
        default=None,
        help="Optional vendor user ID to filter by.",
    )
    parser.add_argument(
        "--status",
        type=str,
        default=None,
        help="Optional status to filter versions by (e.g. rev, apr, ip).",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to look back (default: 30).",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = find_vendor_versions(
            sg=sg,
            project_id=args.project_id,
            vendor_id=args.vendor_id,
            status=args.status,
            days=args.days,
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
