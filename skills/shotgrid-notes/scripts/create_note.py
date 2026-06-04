"""Tool: shotgrid-notes__create_note — Create a note on a ShotGrid entity."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import create_sg_note


def main():
    parser = argparse.ArgumentParser(
        description="Create a note on a ShotGrid entity"
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to note on (Shot, Asset, Version, Task, etc.)",
    )
    parser.add_argument(
        "--entity_id",
        type=int,
        required=True,
        help="ID of the entity",
    )
    parser.add_argument(
        "--subject",
        type=str,
        required=True,
        help="Note subject/title",
    )
    parser.add_argument(
        "--content",
        type=str,
        required=True,
        help="Note content (HTML or plain text)",
    )
    parser.add_argument(
        "--note_type",
        type=str,
        default="Note",
        help="Optional note type (default: Note)",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = create_sg_note(
            sg,
            args.entity_type,
            args.entity_id,
            args.subject,
            args.content,
            note_type=args.note_type,
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
