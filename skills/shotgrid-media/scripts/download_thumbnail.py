"""Tool: shotgrid-media__download_thumbnail — Download a thumbnail from ShotGrid."""
import argparse
import json
import os
import sys

from shotgrid_mcp_server.shared_lib import download_thumbnail
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Download a thumbnail from ShotGrid for a given entity."
    )
    parser.add_argument(
        "--entity_type", type=str, required=True,
        help="Type of entity (e.g. Asset, Shot, Version)"
    )
    parser.add_argument(
        "--entity_id", type=int, required=True,
        help="ID of the entity"
    )
    parser.add_argument(
        "--field_name", type=str, default="image",
        help="Thumbnail field name (default: image)"
    )
    parser.add_argument(
        "--output_path", type=str, default=None,
        help="Optional output file path. If not provided, a default path is used."
    )

    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = download_thumbnail(
            sg,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            field_name=args.field_name,
            output_path=args.output_path,
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
