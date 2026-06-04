"""Tool: shotgrid-playlists__add_versions_to_playlist — Add versions to an existing playlist."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Add versions to an existing playlist.")
    parser.add_argument("--playlist_id", type=int, required=True, help="Playlist ID")
    parser.add_argument("--version_ids", type=int, nargs="+", required=True, help="Version IDs to add")
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()

        playlist = sg.find_one("Playlist", [["id", "is", args.playlist_id]], ["versions"])
        if playlist is None:
            raise ShotGridMCPError(f"Playlist with ID {args.playlist_id} not found")

        current_versions = playlist.get("versions") or []
        current_version_ids = {v["id"] for v in current_versions}

        new_versions = [
            {"type": "Version", "id": vid}
            for vid in args.version_ids
            if vid not in current_version_ids
        ]

        if not new_versions:
            print(json.dumps(playlist, default=str))
            return

        all_versions = current_versions + new_versions
        result = sg.update("Playlist", args.playlist_id, {"versions": all_versions})

        if result is None:
            raise ShotGridMCPError(f"Failed to update playlist with ID {args.playlist_id}")

        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
