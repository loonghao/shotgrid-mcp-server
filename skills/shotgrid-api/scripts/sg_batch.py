"""Tool: shotgrid-api__sg_batch — Low-level ShotGrid batch operation."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_batch
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Low-level ShotGrid batch operation. Executes multiple requests in one call.")
    parser.add_argument("--requests", type=json.loads, required=True, help="JSON array of batch request dicts, e.g. [{\"request_type\":\"create\",\"entity_type\":\"Shot\",\"data\":{...}}]")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_batch(
            sg,
            requests=args.requests,
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
