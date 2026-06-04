"""Tool: shotgrid-media__batch_download_thumbnails — Download multiple thumbnails in batch."""
import argparse
import json
import os
import sys

from shotgrid_mcp_server.shared_lib import batch_download_thumbnails
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(
        description="Download multiple thumbnails in batch for a list of entities."
    )
    parser.add_argument(
        "--entity_type", type=str, required=True,
        help="Type of entities (e.g. Asset, Shot, Version)"
    )
    parser.add_argument(
        "--entity_ids", type=int, nargs="+", required=True,
        help="List of entity IDs (space-separated)"
    )
    parser.add_argument(
        "--field_name", type=str, default="image",
        help="Thumbnail field name (default: image)"
    )
    parser.add_argument(
        "--output_dir", type=str, required=True,
        help="Directory to save downloaded thumbnails"
    )

    args = parser.parse_args()

    if not os.path.isdir(args.output_dir):
        print(
            json.dumps({"error": f"Output directory not found: {args.output_dir}"}),
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        sg = get_current_shotgrid_connection()
        result = batch_download_thumbnails(
            sg,
            entity_type=args.entity_type,
            entity_ids=args.entity_ids,
            field_name=args.field_name,
            output_dir=args.output_dir,
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
