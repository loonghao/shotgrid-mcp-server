"""Tool: shotgrid-crud__create_entity — Create a new entity in ShotGrid."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import create_sg_entity


def main():
    parser = argparse.ArgumentParser(
        description="Create a new entity in ShotGrid (Shot, Asset, Task, Version, etc.)"
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to create (Shot, Asset, Task, Version, etc.)",
    )
    parser.add_argument(
        "--data",
        type=json.loads,
        required=True,
        help="Entity data as JSON object (key-value pairs)",
    )
    parser.add_argument(
        "--project_id",
        type=int,
        default=None,
        help="Optional project ID to link this entity to",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = create_sg_entity(sg, args.entity_type, args.data, args.project_id)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
