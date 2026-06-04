"""Tool: shotgrid-batch__batch_delete — Delete (retire) multiple entities in a single batch operation."""
import argparse
import json
import sys

from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError
from shotgrid_mcp_server.tools.base import handle_error


def main():
    parser = argparse.ArgumentParser(
        description="Delete (retire) multiple entities in a single batch operation."
    )
    parser.add_argument(
        "--entity_type",
        type=str,
        required=True,
        help="Type of entities to delete (e.g., Shot, Task, Version).",
    )
    parser.add_argument(
        "--entity_ids",
        type=str,
        required=True,
        help="JSON-encoded list of entity IDs to delete.",
    )
    args = parser.parse_args()

    try:
        entity_ids = json.loads(args.entity_ids)
        if not isinstance(entity_ids, list):
            raise ShotGridMCPError("entity_ids must be a JSON array of integers")

        sg = get_current_shotgrid_connection()

        # Build batch requests: one "delete" per entity_id
        batch_data = [
            {
                "request_type": "delete",
                "entity_type": args.entity_type,
                "entity_id": int(eid),
            }
            for eid in entity_ids
        ]

        results = sg.batch(batch_data)
        if results is None:
            raise ShotGridMCPError(f"Failed to batch delete {args.entity_type} entities")

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
            "message": f"Successfully deleted {len(serialized)} {args.entity_type} entities",
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
