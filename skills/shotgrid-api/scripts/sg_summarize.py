"""Tool: shotgrid-api__sg_summarize — Summarize entities matching filters."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_summarize
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Summarize entities matching filters. Returns counts grouped by a field.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to summarize (e.g., Shot, Asset, Task)")
    parser.add_argument("--filters", type=json.loads, required=True, help="JSON array of filter conditions")
    parser.add_argument("--summarize-field", type=str, required=True, help="Field to group results by (e.g., sg_status_list)")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_summarize(
            sg,
            entity_type=args.entity_type,
            filters=args.filters,
            summarize_field=args.summarize_field,
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
