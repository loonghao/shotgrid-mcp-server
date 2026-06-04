"""Tool: shotgrid-crud__entity_schema — Get field schema information for an entity type."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.shared_lib import get_sg_entity_schema


def main():
    parser = argparse.ArgumentParser(
        description="Get field schema information for an entity type (Shot, Asset, Task, etc.)"
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entity to get schema for (Shot, Asset, Task, etc.)",
    )
    args = parser.parse_args()

    try:
        sg = get_current_shotgrid_connection()
        result = get_sg_entity_schema(sg, args.entity_type)
        print(json.dumps(result, default=str))
    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
