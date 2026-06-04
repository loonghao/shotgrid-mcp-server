"""Tool: shotgrid-crud__read_entity — Read a single entity from ShotGrid by ID."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import read_sg_entity


def main():
    parser = argparse.ArgumentParser(
        description="Read a single entity from ShotGrid by ID"
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to read",
    )
    parser.add_argument(
        "--entity_id",
        type=int,
        required=True,
        help="ID of the entity to read",
    )
    parser.add_argument(
        "--fields",
        type=str,
        nargs="*",
        default=None,
        help="Optional list of fields to return",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = read_sg_entity(sg, args.entity_type, args.entity_id, args.fields)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
