"""Tool: shotgrid-playlists__find_playlists — Search for playlists in ShotGrid."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


DEFAULT_PLAYLIST_FIELDS = [
    "id", "code", "description", "created_at", "updated_at",
    "created_by", "versions", "project",
]


def main():
    parser = argparse.ArgumentParser(description="Search for playlists in ShotGrid.")
    parser.add_argument("--project_id", type=int, default=None, help="Optional project ID filter")
    parser.add_argument("--name_contains", type=str, default=None, help="Optional name filter")
    parser.add_argument("--fields", type=str, nargs="*", default=None, help="Optional fields to return")
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()

        fields = args.fields if args.fields else DEFAULT_PLAYLIST_FIELDS

        filters = []
        if args.project_id:
            filters.append(["project", "is", {"type": "Project", "id": args.project_id}])
        if args.name_contains:
            filters.append(["code", "contains", args.name_contains])

        try:
            result = sg.find("Playlist", filters, fields=fields, retired_only=False)
        except TypeError:
            result = sg.find("Playlist", filters, fields=fields)

        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
