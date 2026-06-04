"""Tool: shotgrid-playlists__create_playlist — Create a playlist for version review in ShotGrid."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Create a playlist for version review in ShotGrid.")
    parser.add_argument("--name", type=str, required=True, help="Playlist name")
    parser.add_argument("--description", type=str, default=None, help="Optional description")
    parser.add_argument("--project_id", type=int, required=True, help="Project ID")
    parser.add_argument("--versions", type=int, nargs="*", default=None, help="Optional initial version IDs")
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()

        data = {
            "code": args.name,
            "project": {"type": "Project", "id": args.project_id},
        }

        if args.description:
            data["description"] = args.description

        if args.versions:
            data["versions"] = [{"type": "Version", "id": vid} for vid in args.versions]

        result = sg.create("Playlist", data)

        if result is None:
            raise ShotGridMCPError("Failed to create playlist")

        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
