"""Tool: shotgrid-batch__batch_update — Update multiple entities in a single batch operation."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.tools.base import handle_error


def main():
    parser = argparse.ArgumentParser(
        description="Update multiple entities of the same type in a single batch operation."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entities to update (e.g., Shot, Task, Version).",
    )
    parser.add_argument(
        "--data_list",
        type=str,
        required=True,
        help="JSON-encoded list of {id, data} dicts.",
    )
    args = parser.parse_args()

    try:
        data_list = json.loads(args.data_list)
        if not isinstance(data_list, list):
            raise ShotGridMCPError("data_list must be a JSON array of {id, data} dicts")

        sg = get_current_shotgrid_connection()

        # Build batch requests: one "update" per {id, data} dict
        batch_data = []
        for item in data_list:
            if not isinstance(item, dict) or "id" not in item or "data" not in item:
                raise ShotGridMCPError(
                    "Each entry in data_list must be a dict with 'id' and 'data' keys"
                )
            batch_data.append(
                {
                    "request_type": "update",
                    "entity_type": args.entity_type,
                    "entity_id": item["id"],
                    "data": item["data"],
                }
            )

        results = sg.batch(batch_data)
        if results is None:
            raise ShotGridMCPError(f"Failed to batch update {args.entity_type} entities")

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
            "message": f"Successfully updated {len(serialized)} {args.entity_type} entities",
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
