"""Tool: shotgrid-batch__batch_create — Create multiple entities in a single batch operation."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.tools.base import handle_error


def main():
    parser = argparse.ArgumentParser(
        description="Create multiple entities of the same type in a single batch operation."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entities to create (e.g., Shot, Asset, Task).",
    )
    parser.add_argument(
        "--data_list",
        type=str,
        required=True,
        help="JSON-encoded list of entity data dicts.",
    )
    args = parser.parse_args()

    try:
        data_list = json.loads(args.data_list)
        if not isinstance(data_list, list):
            raise ShotGridMCPError("data_list must be a JSON array of entity data dicts")

        sg = get_current_shotgrid_connection()

        # Build batch requests: one "create" per data dict
        batch_data = [
            {"request_type": "create", "entity_type": args.entity_type, "data": data}
            for data in data_list
        ]

        results = sg.batch(batch_data)
        if results is None:
            raise ShotGridMCPError(f"Failed to batch create {args.entity_type} entities")

        # Serialize results for JSON output
        serialized = []
        for result in results:
            if isinstance(result, dict):
                serialized.append(result)
            else:
                serialized.append(str(result))

        output = {
            "results": serialized,
            "total_count": len(serialized),
            "success_count": len(serialized),
            "failure_count": 0,
            "message": f"Successfully created {len(serialized)} {args.entity_type} entities",
        }
        print(json.dumps(output, default=str))

    except ShotGridMCPError as e:
        print(json.dumps({"error": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": f"Unexpected: {e}"}), file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
