"""Tool: shotgrid-api__sg_revive — Revive a retired entity in ShotGrid."""
import argparse
import json
import sys
from shotgrid_mcp_server.shared_lib import sg_revive
from shotgrid_mcp_server.connection_pool import get_current_shotgrid_connection
from shotgrid_mcp_server.exceptions import ShotGridMCPError


def main():
    parser = argparse.ArgumentParser(description="Revive a retired (deleted) entity in ShotGrid.")
    parser.add_argument("--entity-type", type=str, required=True, help="Type of entity to revive (e.g., Shot, Asset, Task)")
    parser.add_argument("--entity-id", type=int, required=True, help="ID of the entity to revive")
    args = parser.parse_args()
    try:
        sg = get_current_shotgrid_connection()
        result = sg_revive(
            sg,
            entity_type=args.entity_type,
            entity_id=args.entity_id,
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
