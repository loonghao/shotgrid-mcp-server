"""Tool: shotgrid-media__upload_thumbnail — Upload a thumbnail to ShotGrid."""
import argparse
import json
import os
import sys

from shotgrid_mcp_server.shared_lib import upload_thumbnail
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Upload a thumbnail image to ShotGrid for a given entity."
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
        "--file_path", type=str, required=True,
        help="Path to the image file to upload"
    )

    args = parser.parse_args()

    if not os.path.isfile(args.file_path):
        print(
            json.dumps({"error": f"File not found: {args.file_path}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        sg = get_current_shotgrid_connection()
        result = upload_thumbnail(
            sg,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
            field_name=args.field_name,
            file_path=args.file_path,
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
