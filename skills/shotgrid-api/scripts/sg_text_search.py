"""Tool: shotgrid-api__sg_text_search — Full-text search across ShotGrid entities."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_text_search
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Full-text search across ShotGrid entities.")
    parser.add_argument("--text", type=str, required=True, help="Search text to look for across entities")
    parser.add_argument("--entity-types", type=json.loads, required=True, help="JSON array of entity type names to search, e.g. [\"Shot\",\"Asset\"]")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_text_search(
            sg,
            text=args.text,
            entity_types=args.entity_types,
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
