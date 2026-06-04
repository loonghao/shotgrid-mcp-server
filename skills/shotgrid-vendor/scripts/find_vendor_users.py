"""Tool: shotgrid-vendor__find_vendor_users -- Find vendor (external) users by name or email filter."""
import argparse
import json
import sys

from shotgrid_mcp_server.shared_lib import find_vendor_users
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Find vendor (external) users by name or email filter."
    )
    parser.add_argument(
        "--name_contains",
        type=str,
        default=None,
        help="Filter users whose name contains this string.",
    )
    parser.add_argument(
        "--email_contains",
        type=str,
        default=None,
        help="Filter users whose email contains this string.",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = find_vendor_users(
            sg=sg,
            name_contains=args.name_contains,
            email_contains=args.email_contains,
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
