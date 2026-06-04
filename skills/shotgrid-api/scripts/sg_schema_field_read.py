"""Tool: shotgrid-api__sg_schema_field_read — Read field schema for an entity type."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_schema_field_read
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Read field schema for an entity type from ShotGrid.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to read schema for (e.g., Shot, Asset, Task)")
    parser.add_argument("--field-name", type=str, default=None, help="Optional specific field name to retrieve schema for")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_schema_field_read(
            sg,
            entity_type=args.entity_type,
            field_name=args.field_name,
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
