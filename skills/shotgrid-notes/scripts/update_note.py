"""Tool: shotgrid-notes__update_note — Update a note in ShotGrid."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import update_sg_note


def main():
    parser = argparse.ArgumentParser(
        description="Update a note in ShotGrid"
    )
    parser.add_argument(
        "--note_id",
        type=int,
        required=True,
        help="ID of the note to update",
    )
    parser.add_argument(
        "--data",
        type=json.loads,
        required=True,
        help="Fields to update as JSON object (e.g. '{\"subject\":\"New subject\",\"content\":\"Updated content\"}')",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = update_sg_note(sg, args.note_id, args.data)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
