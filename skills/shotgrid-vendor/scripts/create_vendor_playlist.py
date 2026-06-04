"""Tool: shotgrid-vendor__create_vendor_playlist -- Create a playlist for vendor review."""
import argparse
import json
import sys

from shotgrid_mcp_server.shared_lib import create_vendor_playlist
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Create a playlist for vendor review in ShotGrid."
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Name for the playlist.",
    )
    parser.add_argument(
        "--project_id",
        type=int,
        required=True,
        help="Project ID where the playlist will be created.",
    )
    parser.add_argument(
        "--version_ids",
        type=int,
        nargs="+",
        default=None,
        help="List of version IDs to include in the playlist.",
    )
    parser.add_argument(
        "--vendor_user_ids",
        type=int,
        nargs="+",
        default=None,
        help="List of vendor user IDs to associate with the playlist.",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = create_vendor_playlist(
            sg=sg,
            name=args.name,
            project_id=args.project_id,
            version_ids=args.version_ids,
            vendor_user_ids=args.vendor_user_ids,
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
